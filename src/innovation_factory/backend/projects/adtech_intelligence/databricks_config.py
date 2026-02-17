"""Databricks resource IDs for AdTech Intelligence project.

Shared values (``WAREHOUSE_ID``, ``UC_CATALOG``) come from global env vars.
Project-specific values are prefixed with ``ADTECH_``.
Defaults are provided for convenience but should be overridden via ``.env``
for each deployment target. See ``.env.example`` for the full list.
"""

import os

# Workspace
WORKSPACE_URL = os.getenv("ADTECH_WORKSPACE_URL", "")

# Shared: Unity Catalog
UC_CATALOG = os.getenv("UC_CATALOG", "innovation_factory_catalog")
UC_SCHEMA = os.getenv("ADTECH_UC_SCHEMA", "adtech_intelligence")

# AI/BI Dashboard
DASHBOARD_ID = os.getenv("ADTECH_DASHBOARD_ID", "")

# Genie Space
GENIE_SPACE_ID = os.getenv("ADTECH_GENIE_SPACE_ID", "")

# Knowledge Assistants
ISSUE_RESOLUTION_KA_TILE_ID = os.getenv("ADTECH_ISSUE_RESOLUTION_KA_TILE_ID", "")
ISSUE_RESOLUTION_KA_ENDPOINT = os.getenv("ADTECH_ISSUE_RESOLUTION_KA_ENDPOINT", "")
CUSTOMER_RELATIONS_KA_TILE_ID = os.getenv("ADTECH_CUSTOMER_RELATIONS_KA_TILE_ID", "")
CUSTOMER_RELATIONS_KA_ENDPOINT = os.getenv("ADTECH_CUSTOMER_RELATIONS_KA_ENDPOINT", "")

# Multi-Agent Supervisor
MAS_TILE_ID = os.getenv("ADTECH_MAS_TILE_ID", "")
MAS_ENDPOINT_NAME = os.getenv("ADTECH_MAS_ENDPOINT_NAME", "")

# Shared: SQL Warehouse
WAREHOUSE_ID = os.getenv("WAREHOUSE_ID", "")
