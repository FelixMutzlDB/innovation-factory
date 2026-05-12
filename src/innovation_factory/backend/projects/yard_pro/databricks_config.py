"""Databricks resource IDs for the yard-pro project.

yard-pro is a Stihl-adjacent AI gardening companion. The AI surfaces live in
three Databricks resources:

- ``COACH_MODEL`` / ``COACH_MODEL_FALLBACK`` — Foundation Model API model
  IDs for the seasonal coach (UC2). Default to ``""`` so a missing config
  surfaces as a "not configured" card per lessons §18, never a 500.
- ``COACH_KA_ENDPOINT`` — Knowledge Assistant endpoint serving the curated
  gardening corpus over Vector Search (``yard_pro_gardening_kb``).
- ``VISION_ENDPOINT`` — Mosaic AI Model Serving endpoint for plant/lawn/pest
  classification (UC3).
- ``DEALER_GENIE_SPACE_ID`` — Genie space for the dealer panel (P5, not
  load-bearing for P0).

Shared values (``WAREHOUSE_ID``, ``UC_CATALOG``) come from global env vars.
All values default to ``""`` so the app boots cleanly without Databricks
resources; the UI checks ``configured`` booleans before rendering panels.
"""
from .._project_config import ProjectResourceConfig

_cfg = ProjectResourceConfig(prefix="YARD_PRO", default_schema="yard_pro")

# Shared (unprefixed) values
WAREHOUSE_ID = _cfg.warehouse_id
UC_CATALOG = _cfg.uc_catalog

# Per-project core resources
UC_SCHEMA = _cfg.uc_schema
WORKSPACE_URL = _cfg.workspace_url

# Coach (UC2) — FM API + KA
COACH_MODEL = _cfg.get("COACH_MODEL", "databricks-meta-llama-3-3-70b")
COACH_MODEL_FALLBACK = _cfg.get("COACH_MODEL_FALLBACK", "databricks-claude-sonnet-4")
COACH_KA_ENDPOINT = _cfg.get("COACH_KA_ENDPOINT")

# Snap-and-diagnose (UC3) — Mosaic AI Vision
VISION_ENDPOINT = _cfg.get("VISION_ENDPOINT")

# Dealer panel (P5)
DEALER_GENIE_SPACE_ID = _cfg.get("DEALER_GENIE_SPACE_ID")

# Photo storage — UC Volume prefix per yard: yard_pro/photos/<yard_id>/...
PHOTOS_VOLUME_PATH = _cfg.get("PHOTOS_VOLUME_PATH")
