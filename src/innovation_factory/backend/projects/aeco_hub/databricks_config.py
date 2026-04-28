"""Databricks resource IDs for the AECO Hub project.

Shared values (``WAREHOUSE_ID``, ``UC_CATALOG``) come from global env vars.
Project-specific values are prefixed with ``AECO_``. All resource IDs default
to empty — set them via env vars or ``app.yml`` for each deployment target.

AECO Hub uses two Genie spaces (Project Analytics + Operations Intelligence),
one AI/BI dashboard (Energy & Sustainability), and one Knowledge Assistant
(Standards & Compliance) orchestrated by a Multi-Agent Supervisor.
"""
from .._project_config import ProjectResourceConfig

_cfg = ProjectResourceConfig(prefix="AECO", default_schema="aeco_hub")

# Shared (unprefixed) values
WAREHOUSE_ID = _cfg.warehouse_id
UC_CATALOG = _cfg.uc_catalog

# Per-project core resources
UC_SCHEMA = _cfg.uc_schema
WORKSPACE_URL = _cfg.workspace_url
MAS_ENDPOINT_NAME = _cfg.mas_endpoint_name

# AECO-specific resources
ENERGY_DASHBOARD_ID = _cfg.get("ENERGY_DASHBOARD_ID")
PROJECT_ANALYTICS_GENIE_SPACE_ID = _cfg.get("PROJECT_ANALYTICS_GENIE_SPACE_ID")
OPERATIONS_INTELLIGENCE_GENIE_SPACE_ID = _cfg.get("OPERATIONS_INTELLIGENCE_GENIE_SPACE_ID")
STANDARDS_COMPLIANCE_KA_ENDPOINT = _cfg.get("STANDARDS_COMPLIANCE_KA_ENDPOINT")
STANDARDS_COMPLIANCE_KA_TILE_ID = _cfg.get("STANDARDS_COMPLIANCE_KA_TILE_ID")
COMPLIANCE_DOCS_VOLUME_PATH = _cfg.get("COMPLIANCE_DOCS_VOLUME_PATH")
MAS_TILE_ID = _cfg.get("MAS_TILE_ID")
