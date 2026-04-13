"""Databricks resource IDs for MOL ASM Cockpit project.

Shared values (``WAREHOUSE_ID``, ``UC_CATALOG``) come from global env vars.
Project-specific values are prefixed with ``MAC_``.
All resource IDs default to empty — set them via env vars or ``app.yml``
for each deployment target.
"""

import os

# AI/BI Dashboard
DASHBOARD_ID = os.getenv("MAC_DASHBOARD_ID", "")

# Multi-Agent Supervisor
MAS_ENDPOINT_NAME = os.getenv("MAC_MAS_ENDPOINT_NAME", "")

# Shared: SQL Warehouse
WAREHOUSE_ID = os.getenv("WAREHOUSE_ID", "")

# Shared: Unity Catalog
UC_CATALOG = os.getenv("UC_CATALOG", "")
UC_SCHEMA = os.getenv("MAC_UC_SCHEMA", "mac")
