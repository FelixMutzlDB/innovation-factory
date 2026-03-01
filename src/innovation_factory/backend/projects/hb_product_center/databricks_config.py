"""Databricks resource IDs for the HB Product Center project."""

import os

WORKSPACE_URL = os.getenv(
    "HB_WORKSPACE_URL",
    "e2-demo-field-eng.cloud.databricks.com",
)

UC_CATALOG = os.getenv("UC_CATALOG", "innovation_factory_catalog")
UC_SCHEMA = os.getenv("HB_UC_SCHEMA", "hb_product_center")

SC_DASHBOARD_ID = os.getenv("HB_SC_DASHBOARD_ID", "01f110d62bfb1ba9ae6d99f9dc1b0f0b")
AQ_DASHBOARD_ID = os.getenv("HB_AQ_DASHBOARD_ID", "01f110ce1d7d1fbc8832730291f05ef07")

SC_GENIE_SPACE_ID = os.getenv("HB_SC_GENIE_SPACE_ID", "01f10dce917e158093ef87c43e5f66f3")
AQ_GENIE_SPACE_ID = os.getenv("HB_AQ_GENIE_SPACE_ID", "01f10dcf2ecd1b26a5dd22b98cff8a73")

MAS_ENDPOINT_NAME = os.getenv("HB_MAS_ENDPOINT_NAME", "mas-2f3fba77-endpoint")

WAREHOUSE_ID = os.getenv("WAREHOUSE_ID", "862f1d757f0424f7")

VS_ENDPOINT_NAME = os.getenv("VS_ENDPOINT_NAME", "image_similarity_endpoint")
VS_INDEX_NAME = os.getenv(
    "VS_INDEX_NAME",
    "saschas.image_similarity.image_similarity_index",
)
VS_IMAGE_TABLE = os.getenv(
    "VS_IMAGE_TABLE",
    "saschas.image_similarity.image_embeddings",
)
IMAGE_VOLUME_PATH = os.getenv(
    "IMAGE_VOLUME_PATH",
    "/Volumes/saschas/image_similarity/images",
)
