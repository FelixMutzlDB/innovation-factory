"""Databricks resource IDs for AdTech Intelligence project.

Shared values (``WAREHOUSE_ID``, ``UC_CATALOG``) come from global env vars.
Project-specific values are prefixed with ``ADTECH_``.
Defaults point to the e2-demo-field-eng deployment but can be overridden
via ``.env`` for each deployment target.
"""

import os

# Workspace
WORKSPACE_URL = os.getenv(
    "ADTECH_WORKSPACE_URL",
    "e2-demo-field-eng.cloud.databricks.com",
)

# Shared: Unity Catalog
UC_CATALOG = os.getenv("UC_CATALOG", "innovation_factory_catalog")
UC_SCHEMA = os.getenv("ADTECH_UC_SCHEMA", "adtech_intelligence")

# AI/BI Dashboard
DASHBOARD_ID = os.getenv("ADTECH_DASHBOARD_ID", "01f10966118d1943b95d82e441e35342")

# Genie Space
GENIE_SPACE_ID = os.getenv("ADTECH_GENIE_SPACE_ID", "01f10964dc5f1b11adf9ddde510fe092")

# Knowledge Assistants
ISSUE_RESOLUTION_KA_TILE_ID = os.getenv("ADTECH_ISSUE_RESOLUTION_KA_TILE_ID", "d6607f71-98a9-42d4-af12-31c0263d7c9a")
ISSUE_RESOLUTION_KA_ENDPOINT = os.getenv("ADTECH_ISSUE_RESOLUTION_KA_ENDPOINT", "ka-d6607f71-endpoint")
CUSTOMER_RELATIONS_KA_TILE_ID = os.getenv("ADTECH_CUSTOMER_RELATIONS_KA_TILE_ID", "68904ea9-4c19-4389-a729-2fc0987feb98")
CUSTOMER_RELATIONS_KA_ENDPOINT = os.getenv("ADTECH_CUSTOMER_RELATIONS_KA_ENDPOINT", "ka-68904ea9-endpoint")

# Multi-Agent Supervisor
MAS_TILE_ID = os.getenv("ADTECH_MAS_TILE_ID", "82f779a2-31da-43cc-86c5-36a202e716ae")
MAS_ENDPOINT_NAME = os.getenv("ADTECH_MAS_ENDPOINT_NAME", "mas-82f779a2-endpoint")

# Shared: SQL Warehouse
WAREHOUSE_ID = os.getenv("WAREHOUSE_ID", "862f1d757f0424f7")
