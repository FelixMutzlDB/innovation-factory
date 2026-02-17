#!/usr/bin/env python3
"""
Create ASM Cockpit - Demand & Inventory Explorer dashboard on Databricks.

Run from the repo root:
    uv run python -m innovation_factory.backend.projects.mol_asm_cockpit.create_dashboard

Requires: Databricks CLI configured (databricks auth login) or env vars:
  DATABRICKS_HOST, DATABRICKS_TOKEN
"""

import json
import os
from pathlib import Path

from databricks.sdk import WorkspaceClient
from databricks.sdk.service.dashboards import Dashboard

from .databricks_config import WAREHOUSE_ID


def main():
    w = WorkspaceClient()

    dashboard_json_path = Path(__file__).parent / "dashboard_definition.json"
    with open(dashboard_json_path) as f:
        serialized = json.load(f)

    user = w.current_user.me().user_name
    parent_path = f"/Workspace/Users/{user}"

    dashboard = Dashboard(
        display_name="ASM Cockpit - Demand & Inventory Explorer",
        parent_path=parent_path,
        serialized_dashboard=json.dumps(serialized),
    )

    created = w.lakeview.create(dashboard)
    dashboard_id = created.dashboard_id
    print(f"Created dashboard: {dashboard_id}")

    warehouse_id = WAREHOUSE_ID
    if not warehouse_id:
        print("WARNING: WAREHOUSE_ID not set, skipping publish step.")
        print(f"  Dashboard ID : {dashboard_id}")
        return

    w.lakeview.publish(
        dashboard_id=dashboard_id,  # type: ignore[invalid-argument-type]
        warehouse_id=warehouse_id,
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


if __name__ == "__main__":
    main()
