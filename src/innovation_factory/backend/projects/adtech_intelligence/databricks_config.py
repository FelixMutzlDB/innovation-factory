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
    "fe-sandbox-felix-demo-sandbox.cloud.databricks.com",
)

# Shared: Unity Catalog
UC_CATALOG = os.getenv("UC_CATALOG", "innovation_factory_catalog")
UC_SCHEMA = os.getenv("ADTECH_UC_SCHEMA", "adtech_intelligence")

# AI/BI Dashboard
DASHBOARD_ID = os.getenv("ADTECH_DASHBOARD_ID", "01f12399316a1a828aa75cf7e90d7aae")

# Genie Space
GENIE_SPACE_ID = os.getenv("ADTECH_GENIE_SPACE_ID", "01f1269032301e2ab448180e1accb1df")

# Knowledge Assistants
ISSUE_RESOLUTION_KA_TILE_ID = os.getenv("ADTECH_ISSUE_RESOLUTION_KA_TILE_ID", "9b426cbe-0de4-425e-903d-27ddff9a794c")
ISSUE_RESOLUTION_KA_ENDPOINT = os.getenv("ADTECH_ISSUE_RESOLUTION_KA_ENDPOINT", "ka-9b426cbe-endpoint")
CUSTOMER_RELATIONS_KA_TILE_ID = os.getenv("ADTECH_CUSTOMER_RELATIONS_KA_TILE_ID", "1e46e5cf-252d-4339-abee-f29f34fea764")
CUSTOMER_RELATIONS_KA_ENDPOINT = os.getenv("ADTECH_CUSTOMER_RELATIONS_KA_ENDPOINT", "ka-1e46e5cf-endpoint")

# Multi-Agent Supervisor
MAS_TILE_ID = os.getenv("ADTECH_MAS_TILE_ID", "6d1add8f-08b5-4613-a014-30cf4c5e51ff")
MAS_ENDPOINT_NAME = os.getenv("ADTECH_MAS_ENDPOINT_NAME", "mas-6d1add8f-endpoint")

# Shared: SQL Warehouse
WAREHOUSE_ID = os.getenv("WAREHOUSE_ID", "8af6100313039ba2")
