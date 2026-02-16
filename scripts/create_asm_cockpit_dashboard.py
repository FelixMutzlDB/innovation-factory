#!/usr/bin/env python3
"""
Create ASM Cockpit - Demand & Inventory Explorer dashboard on Databricks.
Run with: uv run python scripts/create_asm_cockpit_dashboard.py

Requires: Databricks CLI configured (databricks auth login) or env vars:
  DATABRICKS_HOST, DATABRICKS_TOKEN
"""

import json
from pathlib import Path

from databricks.sdk import WorkspaceClient
from databricks.sdk.service.dashboards import Dashboard


def main():
    w = WorkspaceClient()

    dashboard_json_path = Path(__file__).parent / "asm_cockpit_dashboard.json"
    with open(dashboard_json_path) as f:
        serialized = json.load(f)

    # Build Dashboard object for Lakeview API
    # The API expects display_name, parent_path, and serialized_dashboard content
    dashboard = Dashboard(
        display_name="ASM Cockpit - Demand & Inventory Explorer",
        parent_path="/Workspace/Users/felix.mutzl@databricks.com",
        serialized_dashboard=json.dumps(serialized),
    )

    created = w.lakeview.create(dashboard)
    dashboard_id = created.dashboard_id
    print(f"Created dashboard: {dashboard_id}")

    # Publish with embedded credentials for iframe embedding
    published = w.lakeview.publish(
        dashboard_id=dashboard_id,  # type: ignore[invalid-argument-type]
        warehouse_id="0024da9c9e9a4dc2",
        embed_credentials=True,
    )
    host = w.config.host.rstrip("/")
    if not host.startswith("http"):
        host = f"https://{host}"
    url = f"{host}/sql/dashboardsv3/{dashboard_id}"
    embed_url = f"{host}/embed/dashboardsv3/{dashboard_id}"

    print(f"\nDashboard created and published successfully!")
    print(f"  Dashboard ID : {dashboard_id}")
    print(f"  View URL     : {url}")
    print(f"  Embed URL    : {embed_url}")
    print(f"\nTo enable embedding in the app, set the environment variable:")
    print(f"  export MAC_DASHBOARD_ID={dashboard_id}")
    print(f"\nOr update the DASHBOARD_ID constant in:")
    print(f"  src/innovation_factory/backend/projects/mol_asm_cockpit/routers/dashboard.py")


if __name__ == "__main__":
    main()
