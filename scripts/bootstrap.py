#!/usr/bin/env python3
"""Bootstrap a fresh Databricks workspace for Innovation Factory.

Run this after ``databricks bundle deploy`` has created the app, the
warehouse binding, and the Lakebase instance. This script handles the
imperative bits DAB doesn't cover (yet):

  - Upload KA docs to UC volumes
  - Seed per-project UC tables (AdTech + HB)
  - Create the UC function ``identify_product``
  - Create the three Genie spaces
  - Create the two Knowledge Assistants
  - Create the two Multi-Agent Supervisors (with D3 naming)
  - Optionally migrate dashboards from a source workspace
  - Configure workspace embedding-allowed domains
  - Print the env-var dump to paste into ``databricks.yml``

Usage:
    python scripts/bootstrap.py --target <profile>

The bootstrap is idempotent — re-running skips anything already in
``scripts/fevm_agents_state.json``. To force a clean rebuild, delete
the state file first.

Prerequisites (do these once, manually, per new workspace):

  1. ``databricks auth login --profile <profile> --host <url>``
  2. ``databricks bundle deploy -t <target> -p <profile>``
     — creates the Databricks App, Lakebase, warehouse binding.
  3. Ensure the target catalog (default ``felix_demo_catalog``) exists
     in the new workspace's Unity Catalog metastore.

After bootstrap, re-run ``databricks bundle deploy`` so app.yml's env
vars pick up the new resource IDs.
"""
from __future__ import annotations

import argparse
import json
import os
import subprocess
import sys
from pathlib import Path


SCRIPT_DIR = Path(__file__).resolve().parent


def _run(cmd: list[str], *, cwd: Path | None = None) -> int:
    """Run a subprocess, streaming output. Return the exit code."""
    print(f"\n$ {' '.join(cmd)}")
    return subprocess.run(cmd, cwd=cwd).returncode


def _run_checked(cmd: list[str], *, cwd: Path | None = None) -> None:
    rc = _run(cmd, cwd=cwd)
    if rc != 0:
        raise SystemExit(f"command exited with {rc}: {' '.join(cmd)}")


def grant_lakebase_app_permissions(profile: str) -> None:
    """Grant the deployed app's SP CREATE on schema public.

    Without this, ``SQLModel.metadata.create_all`` on the next deploy
    fails to create new tables (the SP only has connect-level access by
    default). Idempotent — safe to run on every bootstrap.
    """
    print("\n=== Lakebase: grant app SP CREATE on schema public ===")
    _run_checked([
        sys.executable,
        str(SCRIPT_DIR / "grant_lakebase_app_permissions.py"),
        "--profile", profile,
    ])


def configure_embedding(profile: str) -> None:
    """Add Databricks-Apps domains to the embedding allowlist.

    Without this, the iframe embeds of Lakeview dashboards render a
    "Embedding dashboards is not available in this workspace" error.
    """
    print("\n=== Workspace: AI/BI dashboard embedding approved domains ===")
    body = {
        "allow_missing": True,
        "field_mask": "aibi_dashboard_embedding_approved_domains.approved_domains",
        "setting": {
            "aibi_dashboard_embedding_approved_domains": {
                "approved_domains": [
                    "aws.databricksapps.com",
                    "azuredatabricks.net",
                    "gcp.databricks.com",
                    "databricksapps.com",
                ]
            },
            "setting_name": "default",
        },
    }
    _run_checked([
        "databricks",
        "settings",
        "aibi-dashboard-embedding-approved-domains",
        "update",
        "-p",
        profile,
        "--json",
        json.dumps(body),
    ])


def run_phase(phase: str, profile: str) -> None:
    """Run one phase of deploy_agents_fevm.py with the given profile.

    We pass the profile through an env var so deploy_agents_fevm.py can
    pick it up without changing its argparse interface.
    """
    env = os.environ.copy()
    # deploy_agents_fevm.py reads PROFILE from a module constant. For
    # targets other than fevm-felix-demo we'd need to edit that constant
    # or parameterize the script — for now, call with a hint.
    env["BOOTSTRAP_PROFILE_HINT"] = profile
    cmd = [sys.executable, str(SCRIPT_DIR / "deploy_agents_fevm.py"), phase]
    rc = subprocess.run(cmd, env=env).returncode
    if rc != 0:
        raise SystemExit(f"phase {phase} failed (exit {rc})")


def emit_env_vars(state_file: Path) -> None:
    """Print the env-var block to paste into databricks.yml and app.yml."""
    print("\n" + "=" * 70)
    print("Env vars to wire into databricks.yml + app.yml")
    print("=" * 70)
    if not state_file.exists():
        print(f"  (no state file at {state_file})")
        return
    state = json.loads(state_file.read_text(encoding="utf-8"))
    g = state.get("genies", {})
    kas = state.get("kas", {})
    mas = state.get("mas", {})
    dbs = state.get("dashboards", {})

    def emit(name: str, value: str) -> None:
        print(f"  - name: {name}")
        print(f"    value: {value or '<unset>'}")

    emit("HB_SC_GENIE_SPACE_ID", g.get("hb_sc", ""))
    emit("HB_AQ_GENIE_SPACE_ID", g.get("hb_aq", ""))
    emit("ADTECH_GENIE_SPACE_ID", g.get("adtech", ""))
    emit("AECO_PROJECT_ANALYTICS_GENIE_SPACE_ID",
         g.get("aeco_project_analytics", ""))
    emit("AECO_OPERATIONS_INTELLIGENCE_GENIE_SPACE_ID",
         g.get("aeco_operations_intelligence", ""))
    emit("ADTECH_ISSUE_RESOLUTION_KA_TILE_ID",
         kas.get("issue_resolution", {}).get("tile_id", ""))
    emit("ADTECH_ISSUE_RESOLUTION_KA_ENDPOINT",
         kas.get("issue_resolution", {}).get("endpoint_name", ""))
    emit("ADTECH_CUSTOMER_RELATIONS_KA_TILE_ID",
         kas.get("customer_relations", {}).get("tile_id", ""))
    emit("ADTECH_CUSTOMER_RELATIONS_KA_ENDPOINT",
         kas.get("customer_relations", {}).get("endpoint_name", ""))
    emit("ADTECH_MAS_TILE_ID", mas.get("adtech", {}).get("tile_id", ""))
    emit("ADTECH_MAS_ENDPOINT_NAME", mas.get("adtech", {}).get("endpoint_name", ""))
    emit("HB_MAS_TILE_ID", mas.get("hb", {}).get("tile_id", ""))
    emit("HB_MAS_ENDPOINT_NAME", mas.get("hb", {}).get("endpoint_name", ""))
    emit("AECO_STANDARDS_COMPLIANCE_KA_TILE_ID",
         kas.get("aeco_standards_compliance", {}).get("tile_id", ""))
    emit("AECO_STANDARDS_COMPLIANCE_KA_ENDPOINT",
         kas.get("aeco_standards_compliance", {}).get("endpoint_name", ""))
    emit("AECO_MAS_TILE_ID", mas.get("aeco", {}).get("tile_id", ""))
    emit("AECO_MAS_ENDPOINT_NAME", mas.get("aeco", {}).get("endpoint_name", ""))
    emit("ADTECH_DASHBOARD_ID", dbs.get("adtech", ""))
    emit("HB_AQ_DASHBOARD_ID", dbs.get("hb_aq", ""))
    emit("HB_SC_DASHBOARD_ID", dbs.get("hb_sc", ""))
    emit("AECO_ENERGY_DASHBOARD_ID", dbs.get("aeco_energy", ""))


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--target",
        default="fevm-felix-demo",
        help="Databricks CLI profile to bootstrap against (default: fevm-felix-demo)",
    )
    parser.add_argument(
        "--skip-dashboards",
        action="store_true",
        help="Skip phase 9 (dashboard migration from source workspace)",
    )
    parser.add_argument(
        "--skip-embedding-config",
        action="store_true",
        help="Skip setting aibi-dashboard-embedding-approved-domains",
    )
    args = parser.parse_args()

    print(f"Bootstrapping Innovation Factory on profile: {args.target}")

    # NOTE: deploy_agents_fevm.py currently hard-codes PROFILE =
    # "fevm-felix-demo". For a truly portable bootstrap, edit that file
    # or wire in an env-var override. Left as Batch E follow-up.
    if args.target != "fevm-felix-demo":
        print(
            "\nWARNING: deploy_agents_fevm.py is currently pinned to "
            "PROFILE='fevm-felix-demo'. Edit it before running against "
            f"{args.target}."
        )

    # Phase 1-7 — UC schemas, volumes, KA docs, AdTech seed data, AECO seed
    # data, UC function, Genie spaces (incl. AECO Project Analytics + AECO
    # Operations Intelligence), Knowledge Assistants, Multi-Agent Supervisors.
    for phase in ("1", "2", "3", "3a", "4", "5", "6", "7"):
        print(f"\n=== Phase {phase} ===")
        run_phase(phase, args.target)

    # Phase 9 — migrate dashboards from source workspace. Optional because
    # the source workspace may not be accessible; in that case the user
    # creates dashboards manually or re-runs with credentials.
    if not args.skip_dashboards:
        print("\n=== Phase 9: dashboard migration ===")
        run_phase("9", args.target)

    # Workspace-level setting — unlock dashboard embedding.
    if not args.skip_embedding_config:
        configure_embedding(args.target)

    # Lakebase grant — the deployed app's SP needs CREATE on schema public
    # so future deploys can add new tables (Phase 6 follow-up).
    grant_lakebase_app_permissions(args.target)

    # Phase 8 — print the summary.
    print("\n=== Phase 8: summary ===")
    run_phase("8", args.target)

    state_file = SCRIPT_DIR / "fevm_agents_state.json"
    emit_env_vars(state_file)

    print("\nNext steps:")
    print("  1. Copy the env-var block above into databricks.yml and app.yml")
    print("     under the target's `config.env:` block.")
    print(f"  2. databricks bundle deploy -t <target> -p {args.target}")
    print("  3. databricks bundle run innovation-factory-app -p "
          f"{args.target}")


if __name__ == "__main__":
    main()
