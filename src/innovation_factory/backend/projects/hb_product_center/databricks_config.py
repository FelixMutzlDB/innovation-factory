"""Databricks resource IDs for the HB Product Center project."""

import os

WORKSPACE_URL = os.getenv(
    "HB_WORKSPACE_URL",
    "e2-demo-field-eng.cloud.databricks.com",
)

UC_CATALOG = os.getenv("UC_CATALOG", "innovation_factory_catalog")
UC_SCHEMA = os.getenv("HB_UC_SCHEMA", "hb_product_center")

SC_DASHBOARD_ID = os.getenv("HB_SC_DASHBOARD_ID", "01f10dd258f7149d8e77b6dcae7fcd36")
AQ_DASHBOARD_ID = os.getenv("HB_AQ_DASHBOARD_ID", "01f10dd25a091cb583999906bfb01dc3")

SC_GENIE_SPACE_ID = os.getenv("HB_SC_GENIE_SPACE_ID", "01f10dce917e158093ef87c43e5f66f3")
AQ_GENIE_SPACE_ID = os.getenv("HB_AQ_GENIE_SPACE_ID", "01f10dcf2ecd1b26a5dd22b98cff8a73")

MAS_ENDPOINT_NAME = os.getenv("HB_MAS_ENDPOINT_NAME", "mas-fac40cde-endpoint")

LLM_ENDPOINT_NAME = os.getenv("HB_LLM_ENDPOINT_NAME", "databricks-claude-sonnet-4-6")

WAREHOUSE_ID = os.getenv("WAREHOUSE_ID", "862f1d757f0424f7")
