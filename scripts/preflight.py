"""Pre-deploy validation for innovation-factory.

Catches the class of issues that bit Phase 6 deploy:
- Stale ``.env`` profile pointing at a deleted workspace
- App SP missing ``CREATE ON SCHEMA public`` so ``create_all`` raises
  ``permission denied`` and ``initialize_models`` swallows it as a
  "concurrent worker race" warning
- Resource IDs drift between ``fevm_agents_state.json`` (source of truth),
  ``.env``, ``app.yml``, and ``databricks.yml``
- AI/BI dashboard embedding domains not approved at workspace level

Each check returns ``Ok | Warn | Err``. Script exits 0 on all-Ok / Warn,
non-zero on any Err. Structured JSON output (``--json``) for machine
consumers; default is a one-screen human report.

Usage:
    python scripts/preflight.py                      # human report
    python scripts/preflight.py --json               # JSON output
    python scripts/preflight.py --profile <name>     # override profile
    python scripts/preflight.py --skip-permissions   # skip SP CREATE check
"""
from __future__ import annotations

import argparse
import json
import os
import re
import subprocess
import sys
from dataclasses import dataclass, field
from pathlib import Path
from typing import Literal


REPO_ROOT = Path(__file__).resolve().parents[1]
DEFAULT_PROFILE = "fevm-felix-demo"
STATE_FILE = REPO_ROOT / "scripts" / "fevm_agents_state.json"

Status = Literal["ok", "warn", "err"]


@dataclass
class CheckResult:
    name: str
    status: Status
    message: str
    detail: dict = field(default_factory=dict)


def _run_json(cmd: list[str], timeout: int = 30) -> tuple[bool, dict | str]:
    res = subprocess.run(cmd, capture_output=True, text=True, timeout=timeout)
    if res.returncode != 0:
        return False, res.stderr.strip() or res.stdout.strip()
    if not res.stdout.strip():
        return True, {}
    try:
        return True, json.loads(res.stdout)
    except json.JSONDecodeError as e:
        return False, f"invalid JSON: {e}"


def check_profile_reachable(profile: str) -> CheckResult:
    ok, payload = _run_json(
        ["databricks", "current-user", "me", "-p", profile, "--output", "json"]
    )
    if not ok:
        return CheckResult(
            "profile_reachable",
            "err",
            f"Profile {profile!r} not reachable. Run: databricks auth login --profile {profile}",
            detail={"error": str(payload)[:300]},
        )
    user = payload.get("userName") if isinstance(payload, dict) else None
    return CheckResult(
        "profile_reachable", "ok",
        f"Profile {profile!r} authenticated as {user}",
        detail={"user_name": user},
    )


def check_app_sp_create_perm(profile: str, app_name: str = "innovation-factory") -> CheckResult:
    """Check the deployed app's SP has CREATE on schema public.

    Without this, the next deploy that adds a new model will silently
    skip the new tables. The runtime swallows ``permission denied`` as
    "likely concurrent worker race" so the failure is invisible.
    """
    ok, app = _run_json([
        "databricks", "apps", "get", app_name, "-p", profile, "--output", "json",
    ])
    if not ok:
        return CheckResult(
            "app_sp_create_perm",
            "warn",
            f"Could not fetch app {app_name!r} (skipping permission check)",
            detail={"error": str(app)[:200]},
        )
    sp_id = app.get("service_principal_client_id") if isinstance(app, dict) else None
    if not sp_id:
        return CheckResult(
            "app_sp_create_perm", "warn",
            f"App has no service_principal_client_id yet (first deploy?)",
        )

    # Try to query Lakebase as the human user to inspect SP privileges.
    # We hard-code the production endpoint since this is a fevm-felix-demo
    # workspace check; for a different setup, override via env.
    endpoint = os.environ.get(
        "PREFLIGHT_LAKEBASE_ENDPOINT",
        "projects/innovation-factory/branches/production/endpoints/primary",
    )
    ok_cred, cred = _run_json([
        "databricks", "postgres", "generate-database-credential", endpoint,
        "-p", profile, "--output", "json",
    ], timeout=60)
    if not ok_cred:
        return CheckResult(
            "app_sp_create_perm", "warn",
            "Could not fetch Lakebase credential — skipping permission check",
            detail={"error": str(cred)[:200]},
        )
    token = cred.get("token") if isinstance(cred, dict) else None
    if not token:
        return CheckResult(
            "app_sp_create_perm", "warn",
            "Lakebase credential response missing token",
        )

    ok_ep, ep = _run_json([
        "databricks", "postgres", "get-endpoint", endpoint,
        "-p", profile, "--output", "json",
    ])
    host = (ep.get("status", {}).get("hosts", {}).get("host")
            if ok_ep and isinstance(ep, dict) else None)
    if not host:
        return CheckResult(
            "app_sp_create_perm", "warn",
            "Could not resolve Lakebase host",
        )

    ok_me, me = _run_json([
        "databricks", "current-user", "me", "-p", profile, "--output", "json",
    ])
    user = me.get("userName") if ok_me and isinstance(me, dict) else None
    if not user:
        return CheckResult(
            "app_sp_create_perm", "warn",
            "Could not resolve current user identity",
        )

    try:
        import psycopg
    except ImportError:
        return CheckResult(
            "app_sp_create_perm", "warn",
            "psycopg not installed — skipping permission check",
        )

    try:
        conn = psycopg.connect(
            host=host, port=5432, dbname="databricks_postgres",
            user=user, password=token, sslmode="require",
        )
        cur = conn.cursor()
        cur.execute("SELECT has_schema_privilege(%s, 'public', 'CREATE')", (sp_id,))
        has_create = cur.fetchone()[0]
        conn.close()
    except Exception as e:
        return CheckResult(
            "app_sp_create_perm", "warn",
            f"Lakebase connect failed: {type(e).__name__}",
            detail={"error": str(e)[:200]},
        )

    if not has_create:
        return CheckResult(
            "app_sp_create_perm", "err",
            f"App SP {sp_id} is missing CREATE on schema public. "
            f"Run: python scripts/grant_lakebase_app_permissions.py --profile {profile}",
            detail={"sp_client_id": sp_id, "schema": "public"},
        )
    return CheckResult(
        "app_sp_create_perm", "ok",
        f"App SP has CREATE on schema public",
        detail={"sp_client_id": sp_id},
    )


def _scan_id_refs(path: Path) -> dict[str, str]:
    """Return ``{ENV_VAR_NAME: value}`` for every ``NAME=VALUE`` (or yaml
    ``- name: NAME / value: VALUE`` pair) in *path*."""
    if not path.is_file():
        return {}
    text = path.read_text(encoding="utf-8")
    out: dict[str, str] = {}

    # Plain ``KEY=VALUE`` lines (.env)
    for m in re.finditer(r'^\s*([A-Z][A-Z0-9_]+)=([^\n#]*)', text, re.MULTILINE):
        v = m.group(2).strip().strip('"').strip("'")
        out[m.group(1)] = v

    # YAML ``- name: KEY\n  value: VALUE`` pairs (app.yml, databricks.yml)
    for m in re.finditer(
        r'-\s*name:\s*([A-Z][A-Z0-9_]+)\s*\n\s*value:\s*("?)([^"\n]*)\2',
        text,
    ):
        out[m.group(1)] = m.group(3).strip()
    return out


def check_resource_id_drift() -> CheckResult:
    """Compare the env vars in ``.env`` / ``.env.example`` / ``app.yml`` /
    ``databricks.yml`` for the per-accelerator resource IDs we care about.

    Drift here is a deploy-time landmine — Phase 6 hit this when the MAS
    rebuild left ``app.yml`` referencing the old endpoint name.
    """
    sources = {
        ".env": _scan_id_refs(REPO_ROOT / ".env"),
        ".env.example": _scan_id_refs(REPO_ROOT / ".env.example"),
        "app.yml": _scan_id_refs(REPO_ROOT / "app.yml"),
        "databricks.yml": _scan_id_refs(REPO_ROOT / "databricks.yml"),
    }
    # Only look at vars that look like resource IDs — we don't care about
    # every env var differing (e.g. .env may have a local DB override).
    interesting_suffixes = (
        "_DASHBOARD_ID", "_GENIE_SPACE_ID", "_KA_ENDPOINT", "_KA_TILE_ID",
        "_MAS_ENDPOINT_NAME", "_MAS_TILE_ID",
    )
    drift: list[str] = []
    keys: set[str] = set()
    for src in sources.values():
        keys |= {k for k in src if k.endswith(interesting_suffixes)}
    for key in sorted(keys):
        values = {src: vals.get(key) for src, vals in sources.items() if key in vals}
        # Only complain about keys present in ≥2 files with different values
        present = {s: v for s, v in values.items() if v}
        if len(present) >= 2 and len(set(present.values())) > 1:
            drift.append(f"{key}: " + ", ".join(f"{s}={v!r}" for s, v in present.items()))

    if drift:
        return CheckResult(
            "resource_id_drift", "err",
            f"Resource IDs differ across env files: {len(drift)} mismatch(es)",
            detail={"drift": drift},
        )
    return CheckResult(
        "resource_id_drift", "ok",
        f"All resource IDs consistent across env files ({len(keys)} keys checked)",
    )


def check_state_vs_envs() -> CheckResult:
    """Compare ``fevm_agents_state.json`` (source of truth) against env files.

    State maps -> env-var names is hard-coded; mirrors the emit_env_vars
    function in bootstrap.py. If something here is missing from
    ``app.yml`` / ``databricks.yml``, the deployed app won't see it.
    """
    if not STATE_FILE.is_file():
        return CheckResult(
            "state_vs_envs", "warn",
            f"State file not found at {STATE_FILE} — skipping",
        )
    state = json.loads(STATE_FILE.read_text(encoding="utf-8"))
    expected: dict[str, str] = {}
    for k, v in (state.get("genies") or {}).items():
        expected[f"{_state_to_env_genie(k)}_GENIE_SPACE_ID"] = v
    for k, v in (state.get("kas") or {}).items():
        prefix = _state_to_env_ka(k)
        if prefix and v.get("tile_id"):
            expected[f"{prefix}_KA_TILE_ID"] = v["tile_id"]
            expected[f"{prefix}_KA_ENDPOINT"] = v.get("endpoint_name", "")
    for k, v in (state.get("mas") or {}).items():
        prefix = _state_to_env_mas(k)
        if prefix and v.get("tile_id"):
            expected[f"{prefix}_MAS_TILE_ID"] = v["tile_id"]
            expected[f"{prefix}_MAS_ENDPOINT_NAME"] = v.get("endpoint_name", "")
    for k, v in (state.get("dashboards") or {}).items():
        prefix = _state_to_env_dashboard(k)
        if prefix and v:
            expected[f"{prefix}_DASHBOARD_ID"] = v

    app_yml = _scan_id_refs(REPO_ROOT / "app.yml")
    db_yml = _scan_id_refs(REPO_ROOT / "databricks.yml")

    missing_app: list[str] = []
    stale_app: list[str] = []
    for env_var, want in expected.items():
        got = app_yml.get(env_var)
        if got is None:
            missing_app.append(env_var)
        elif got != want:
            stale_app.append(f"{env_var}: app.yml={got!r} != state={want!r}")

    if missing_app or stale_app:
        return CheckResult(
            "state_vs_envs", "err",
            f"app.yml drift vs state: {len(missing_app)} missing, {len(stale_app)} stale",
            detail={"missing_in_app_yml": missing_app, "stale_in_app_yml": stale_app},
        )
    return CheckResult(
        "state_vs_envs", "ok",
        f"app.yml matches state ({len(expected)} resource IDs verified)",
    )


def _state_to_env_genie(k: str) -> str:
    return {
        "hb_sc": "HB_SC", "hb_aq": "HB_AQ", "adtech": "ADTECH",
        "aeco_project_analytics": "AECO_PROJECT_ANALYTICS",
        "aeco_operations_intelligence": "AECO_OPERATIONS_INTELLIGENCE",
    }.get(k, k.upper())


def _state_to_env_ka(k: str) -> str | None:
    return {
        "issue_resolution": "ADTECH_ISSUE_RESOLUTION",
        "customer_relations": "ADTECH_CUSTOMER_RELATIONS",
        "aeco_standards_compliance": "AECO_STANDARDS_COMPLIANCE",
    }.get(k)


def _state_to_env_mas(k: str) -> str | None:
    return {"adtech": "ADTECH", "hb": "HB", "aeco": "AECO"}.get(k)


def _state_to_env_dashboard(k: str) -> str | None:
    return {
        "adtech": "ADTECH", "hb_sc": "HB_SC", "hb_aq": "HB_AQ",
        "aeco_energy": "AECO_ENERGY",
    }.get(k)


def check_dashboard_embedding(profile: str) -> CheckResult:
    """Without ``aibi-dashboard-embedding-approved-domains`` set, the
    energy dashboard iframe shows "Embedding not allowed in this workspace"
    instead of the dashboard."""
    ok, body = _run_json([
        "databricks", "settings",
        "aibi-dashboard-embedding-approved-domains", "get",
        "-p", profile, "--output", "json",
    ])
    if not ok:
        return CheckResult(
            "dashboard_embedding", "warn",
            f"Could not read embedding-domains setting: {str(body)[:200]}",
        )
    domains = (
        body.get("setting", {})
            .get("aibi_dashboard_embedding_approved_domains", {})
            .get("approved_domains", [])
        if isinstance(body, dict) else []
    )
    required = {"databricksapps.com", "aws.databricksapps.com"}
    missing = required - set(domains)
    if missing:
        return CheckResult(
            "dashboard_embedding", "err",
            f"Missing approved domains: {sorted(missing)}. "
            f"Run: python scripts/bootstrap.py --target {profile} --skip-dashboards "
            f"(re-runs configure_embedding)",
            detail={"current_domains": domains, "missing": sorted(missing)},
        )
    return CheckResult(
        "dashboard_embedding", "ok",
        f"Embedding domains include all required entries ({len(domains)} total)",
    )


def run_preflight(profile: str, skip_permissions: bool = False) -> list[CheckResult]:
    results: list[CheckResult] = []
    results.append(check_profile_reachable(profile))
    if results[-1].status == "err":
        # Other checks need profile auth; bail.
        return results
    if not skip_permissions:
        results.append(check_app_sp_create_perm(profile))
    results.append(check_resource_id_drift())
    results.append(check_state_vs_envs())
    results.append(check_dashboard_embedding(profile))
    return results


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--profile", default=DEFAULT_PROFILE)
    parser.add_argument("--json", action="store_true",
                        help="Emit structured JSON instead of human-readable text")
    parser.add_argument("--skip-permissions", action="store_true",
                        help="Skip the SP CREATE perm check (faster, no Lakebase round-trip)")
    args = parser.parse_args()

    results = run_preflight(args.profile, skip_permissions=args.skip_permissions)

    if args.json:
        out = [{"name": r.name, "status": r.status, "message": r.message, "detail": r.detail}
               for r in results]
        print(json.dumps(out, indent=2))
    else:
        print(f"Preflight against profile: {args.profile}\n")
        for r in results:
            marker = {"ok": "✓", "warn": "⚠", "err": "✗"}[r.status]
            print(f"  [{marker}] {r.name:24} {r.message}")
            if r.detail and r.status != "ok":
                for k, v in r.detail.items():
                    print(f"        {k}: {v!r}"[:200])
        print()
        errs = sum(1 for r in results if r.status == "err")
        warns = sum(1 for r in results if r.status == "warn")
        if errs:
            print(f"FAIL — {errs} error(s), {warns} warning(s)")
            return 1
        if warns:
            print(f"OK with {warns} warning(s) — review above")
            return 0
        print("PASS — all preflight checks green.")
    return 0 if all(r.status != "err" for r in results) else 1


if __name__ == "__main__":
    sys.exit(main())
