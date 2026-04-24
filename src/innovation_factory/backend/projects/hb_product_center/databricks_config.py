"""Databricks resource IDs for the HB Product Center project.

Shared values (``WAREHOUSE_ID``, ``UC_CATALOG``) come from global env
vars. Project-specific values are prefixed with ``HB_``. All resource
IDs default to empty — set them via env vars or ``app.yml`` for each
deployment target.

HB has two dashboards / two Genie spaces (Supply Chain + Authenticity &
Quality) plus a vector-search stack for CLIP-based image recognition.
"""
import os

from .._project_config import ProjectResourceConfig

_cfg = ProjectResourceConfig(prefix="HB", default_schema="hb_product_center")

# Shared (unprefixed) values
WAREHOUSE_ID = _cfg.warehouse_id
UC_CATALOG = _cfg.uc_catalog

# Per-project core resources
UC_SCHEMA = _cfg.uc_schema
WORKSPACE_URL = _cfg.workspace_url
MAS_ENDPOINT_NAME = _cfg.mas_endpoint_name

# HB-specific: two dashboards / two Genies (Supply Chain + Auth/Quality)
SC_DASHBOARD_ID = _cfg.get("SC_DASHBOARD_ID")
AQ_DASHBOARD_ID = _cfg.get("AQ_DASHBOARD_ID")
SC_GENIE_SPACE_ID = _cfg.get("SC_GENIE_SPACE_ID")
AQ_GENIE_SPACE_ID = _cfg.get("AQ_GENIE_SPACE_ID")

# HB-specific: vector-search stack for CLIP-based image recognition.
# These env vars are unprefixed because they may be reused by a shared
# VS client across projects in future.
VS_ENDPOINT_NAME = os.getenv("VS_ENDPOINT_NAME", "")
VS_INDEX_NAME = os.getenv("VS_INDEX_NAME", "")
VS_IMAGE_TABLE = os.getenv("VS_IMAGE_TABLE", "")
IMAGE_VOLUME_PATH = os.getenv("IMAGE_VOLUME_PATH", "")
