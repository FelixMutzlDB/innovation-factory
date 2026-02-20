"""Main router for Hugo Boss Product Center, mounting all sub-routers."""

from fastapi import APIRouter
from pydantic import BaseModel

from .databricks_config import (
    AQ_DASHBOARD_ID,
    AQ_GENIE_SPACE_ID,
    SC_DASHBOARD_ID,
    SC_GENIE_SPACE_ID,
    WORKSPACE_URL,
)
from .routers import products, recognition, quality, authenticity, supply_chain, dashboard, chat

router = APIRouter(tags=["hb-product-center"])

router.include_router(products.router)
router.include_router(recognition.router)
router.include_router(quality.router)
router.include_router(authenticity.router)
router.include_router(supply_chain.router)
router.include_router(dashboard.router)
router.include_router(chat.router)


class HbDatabricksResourcesOut(BaseModel):
    workspace_url: str
    sc_dashboard_id: str
    sc_dashboard_embed_url: str
    aq_dashboard_id: str
    aq_dashboard_embed_url: str
    sc_genie_space_id: str
    aq_genie_space_id: str


@router.get(
    "/databricks-resources",
    response_model=HbDatabricksResourcesOut,
    operation_id="hb_getDatabricksResources",
)
async def get_databricks_resources() -> HbDatabricksResourcesOut:
    """Return Databricks resource IDs for frontend embedding."""
    base = f"https://{WORKSPACE_URL}"
    return HbDatabricksResourcesOut(
        workspace_url=WORKSPACE_URL,
        sc_dashboard_id=SC_DASHBOARD_ID,
        sc_dashboard_embed_url=f"{base}/embed/dashboardsv3/{SC_DASHBOARD_ID}",
        aq_dashboard_id=AQ_DASHBOARD_ID,
        aq_dashboard_embed_url=f"{base}/embed/dashboardsv3/{AQ_DASHBOARD_ID}",
        sc_genie_space_id=SC_GENIE_SPACE_ID,
        aq_genie_space_id=AQ_GENIE_SPACE_ID,
    )
