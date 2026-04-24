"""Databricks resource IDs for MOL ASM Cockpit project.

Shared values (``WAREHOUSE_ID``, ``UC_CATALOG``) come from global env
vars. Project-specific values are prefixed with ``MAC_``. All resource
IDs default to empty — set them via env vars or ``app.yml`` for each
deployment target.
"""
from .._project_config import ProjectResourceConfig

_cfg = ProjectResourceConfig(prefix="MAC", default_schema="mac")

# Shared (unprefixed) values
WAREHOUSE_ID = _cfg.warehouse_id
UC_CATALOG = _cfg.uc_catalog

# Per-project core resources
UC_SCHEMA = _cfg.uc_schema
WORKSPACE_URL = _cfg.workspace_url
DASHBOARD_ID = _cfg.dashboard_id
MAS_ENDPOINT_NAME = _cfg.mas_endpoint_name
