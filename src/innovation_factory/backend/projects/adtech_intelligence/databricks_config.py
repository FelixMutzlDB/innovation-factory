"""Databricks resource IDs for AdTech Intelligence project.

Shared values (``WAREHOUSE_ID``, ``UC_CATALOG``) come from global env
vars. Project-specific values are prefixed with ``ADTECH_``. All
resource IDs default to empty — set them via env vars or ``app.yml``
for each deployment target.

Structure is enforced by :mod:`_project_config` so all projects read the
same set of fields with the same fallback logic. Project-specific extras
(like the two KAs here) use ``_cfg.get("...")`` for the remaining
prefixed env vars.
"""
from .._project_config import ProjectResourceConfig

_cfg = ProjectResourceConfig(prefix="ADTECH", default_schema="adtech_intelligence")

# Shared (unprefixed) values
WAREHOUSE_ID = _cfg.warehouse_id
UC_CATALOG = _cfg.uc_catalog

# Per-project core resources
UC_SCHEMA = _cfg.uc_schema
WORKSPACE_URL = _cfg.workspace_url
DASHBOARD_ID = _cfg.dashboard_id
GENIE_SPACE_ID = _cfg.genie_space_id
MAS_ENDPOINT_NAME = _cfg.mas_endpoint_name
MAS_TILE_ID = _cfg.mas_tile_id

# AdTech-specific: two Knowledge Assistants
ISSUE_RESOLUTION_KA_TILE_ID = _cfg.get("ISSUE_RESOLUTION_KA_TILE_ID")
ISSUE_RESOLUTION_KA_ENDPOINT = _cfg.get("ISSUE_RESOLUTION_KA_ENDPOINT")
CUSTOMER_RELATIONS_KA_TILE_ID = _cfg.get("CUSTOMER_RELATIONS_KA_TILE_ID")
CUSTOMER_RELATIONS_KA_ENDPOINT = _cfg.get("CUSTOMER_RELATIONS_KA_ENDPOINT")
