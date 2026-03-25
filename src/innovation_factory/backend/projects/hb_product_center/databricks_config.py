"""Databricks resource IDs for the HB Product Center project."""

import os

WORKSPACE_URL = os.getenv(
    "HB_WORKSPACE_URL",
    "fe-sandbox-felix-demo-sandbox.cloud.databricks.com",
)

UC_CATALOG = os.getenv("UC_CATALOG", "innovation_factory_catalog")
UC_SCHEMA = os.getenv("HB_UC_SCHEMA", "hb_product_center")

SC_DASHBOARD_ID = os.getenv("HB_SC_DASHBOARD_ID", "01f123992f21169d9ddc821e1dc8c12b")
AQ_DASHBOARD_ID = os.getenv("HB_AQ_DASHBOARD_ID", "01f1239930521243bc18f567917dd6c0")

SC_GENIE_SPACE_ID = os.getenv("HB_SC_GENIE_SPACE_ID", "01f10dce917e158093ef87c43e5f66f3")
AQ_GENIE_SPACE_ID = os.getenv("HB_AQ_GENIE_SPACE_ID", "01f10dcf2ecd1b26a5dd22b98cff8a73")

MAS_ENDPOINT_NAME = os.getenv("HB_MAS_ENDPOINT_NAME", "mas-d6c8b06f-endpoint")

WAREHOUSE_ID = os.getenv("WAREHOUSE_ID", "8af6100313039ba2")

VS_ENDPOINT_NAME = os.getenv("VS_ENDPOINT_NAME", "image_similarity_endpoint")
VS_INDEX_NAME = os.getenv(
    "VS_INDEX_NAME",
    "innovation_factory_catalog.image_similarity.image_similarity_index",
)
VS_IMAGE_TABLE = os.getenv(
    "VS_IMAGE_TABLE",
    "innovation_factory_catalog.image_similarity.image_embeddings",
)
IMAGE_VOLUME_PATH = os.getenv(
    "IMAGE_VOLUME_PATH",
    "/Volumes/innovation_factory_catalog/image_similarity/images",
)
