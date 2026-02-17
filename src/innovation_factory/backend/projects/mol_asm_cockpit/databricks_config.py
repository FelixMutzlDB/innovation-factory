"""Databricks resource IDs for MOL ASM Cockpit project.

All values are read from environment variables (prefixed with ``MAC_``).
Defaults are provided for convenience but should be overridden via ``.env``
for each deployment target. See ``.env.example`` for the full list.
"""

import os

# AI/BI Dashboard
DASHBOARD_ID = os.getenv("MAC_DASHBOARD_ID", "")

# Multi-Agent Supervisor
MAS_ENDPOINT_NAME = os.getenv("MAC_MAS_ENDPOINT_NAME", "")

# SQL Warehouse (used by dashboard creation script)
WAREHOUSE_ID = os.getenv("MAC_WAREHOUSE_ID", "")
