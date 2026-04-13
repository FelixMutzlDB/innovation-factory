"""Databricks resource IDs for the HB Product Center project.

All resource IDs default to empty — set them via env vars or ``app.yml``
for each deployment target.
"""

import os

WORKSPACE_URL = os.getenv(
    "HB_WORKSPACE_URL",
    os.getenv("DATABRICKS_HOST", "").replace("https://", "").rstrip("/"),
)

UC_CATALOG = os.getenv("UC_CATALOG", "")
UC_SCHEMA = os.getenv("HB_UC_SCHEMA", "hb_product_center")

SC_DASHBOARD_ID = os.getenv("HB_SC_DASHBOARD_ID", "")
AQ_DASHBOARD_ID = os.getenv("HB_AQ_DASHBOARD_ID", "")

SC_GENIE_SPACE_ID = os.getenv("HB_SC_GENIE_SPACE_ID", "")
AQ_GENIE_SPACE_ID = os.getenv("HB_AQ_GENIE_SPACE_ID", "")

MAS_ENDPOINT_NAME = os.getenv("HB_MAS_ENDPOINT_NAME", "")

WAREHOUSE_ID = os.getenv("WAREHOUSE_ID", "")

VS_ENDPOINT_NAME = os.getenv("VS_ENDPOINT_NAME", "")
VS_INDEX_NAME = os.getenv("VS_INDEX_NAME", "")
VS_IMAGE_TABLE = os.getenv("VS_IMAGE_TABLE", "")
IMAGE_VOLUME_PATH = os.getenv("IMAGE_VOLUME_PATH", "")
