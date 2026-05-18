"""Deploy the yard-pro dealer Lakeview dashboard (UC6 demo surface).

Reads the dashboard JSON template from
``src/innovation_factory/backend/projects/yard_pro/dashboard_dealer.json``,
substitutes the catalog placeholder, POSTs to
``/api/2.0/lakeview/dashboards``, then publishes with
``embed_credentials=True`` so the iframe in the dealer panel can serve
the dashboard without per-user SSO inside the iframe.

State file: ``scripts/yard_pro/dashboard_state.json`` — re-runs are
idempotent. ``--force`` recreates.

Pattern mirrors ``scripts/deploy_agents_fevm.py::create_aeco_dashboard``.
"""
from __future__ import annotations

import argparse
import json
import subprocess
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
STATE_FILE = Path(__file__).resolve().parent / "dashboard_state.json"
TEMPLATE = (
    REPO_ROOT
    / "src/innovation_factory/backend/projects/yard_pro/dashboard_dealer.json"
)

DEFAULT_PROFILE = "fevm-felix-demo"
DEFAULT_CATALOG = "felix_demo_catalog"
DEFAULT_WAREHOUSE_ID = "f7cdb11888c4799e"
DEFAULT_DISPLAY_NAME = "yard-pro Dealer Cockpit"


def _api(method: str, path: str, body: dict | None, profile: str) -> dict:
    cmd = ["databricks", "api", method, path, "--profile", profile]
    if body is not None:
        cmd += ["--json", json.dumps(body)]
    res = subprocess.run(cmd, capture_output=True, text=True, timeout=120)
    if res.returncode != 0:
        sys.exit(f"API call failed: {' '.join(cmd)}\nstderr: {res.stderr}")
    if not res.stdout.strip():
        return {}
    return json.loads(res.stdout)


def _load_state() -> dict:
    if STATE_FILE.exists():
        try:
            return json.loads(STATE_FILE.read_text())
        except json.JSONDecodeError:
            return {}
    return {}


def _save_state(state: dict) -> None:
    STATE_FILE.write_text(json.dumps(state, indent=2) + "\n")


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--profile", default=DEFAULT_PROFILE)
    parser.add_argument("--catalog", default=DEFAULT_CATALOG)
    parser.add_argument("--warehouse-id", default=DEFAULT_WAREHOUSE_ID)
    parser.add_argument("--display-name", default=DEFAULT_DISPLAY_NAME)
    parser.add_argument("--force", action="store_true",
                        help="Recreate even if a dashboard ID is in state")
    args = parser.parse_args()

    if not TEMPLATE.exists():
        sys.exit(f"template not found: {TEMPLATE}")

    state = _load_state()
    serialized = TEMPLATE.read_text().replace("{{CATALOG}}", args.catalog)

    body = {
        "display_name": args.display_name,
        "warehouse_id": args.warehouse_id,
        "serialized_dashboard": serialized,
    }

    if state.get("dashboard_id") and not args.force:
        # Update existing dashboard in place (preserves the ID so env
        # vars and the running app keep pointing at the right thing).
        dashboard_id = state["dashboard_id"]
        print(f"Updating existing dashboard: {dashboard_id}")
        _api(
            "patch",
            f"/api/2.0/lakeview/dashboards/{dashboard_id}",
            body,
            args.profile,
        )
        print("  Patched")
    else:
        print(f"Creating dashboard: {args.display_name}")
        resp = _api("post", "/api/2.0/lakeview/dashboards", body, args.profile)
        dashboard_id = resp.get("dashboard_id")
        if not dashboard_id:
            sys.exit(f"create failed: {resp}")
        print(f"  Created: {dashboard_id}")

        state["dashboard_id"] = dashboard_id
        state["display_name"] = args.display_name
        _save_state(state)

    print("Publishing with embed_credentials=true")
    pub = _api(
        "post",
        f"/api/2.0/lakeview/dashboards/{dashboard_id}/published",
        {"embed_credentials": True, "warehouse_id": args.warehouse_id},
        args.profile,
    )
    if pub is None:
        print("  WARN: publish call returned no body — iframe embed may 404")
    else:
        print("  Published")

    print()
    print("Set in app.yml / databricks.yml / .env:")
    print(f"    YARD_PRO_DEALER_DASHBOARD_ID={dashboard_id}")
    print()
    print("Then redeploy the app:")
    print(
        f"    uv run apx build && databricks bundle deploy -t dev --profile {args.profile}"
    )


if __name__ == "__main__":
    main()
