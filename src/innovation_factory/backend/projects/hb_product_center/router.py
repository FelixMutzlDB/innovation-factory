"""Main router for Hugo Boss Product Center, mounting all sub-routers."""

from fastapi import APIRouter, Request
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
    configured: bool = False


def _resolve_workspace_url(request: Request) -> str:
    """Return the workspace URL from config or derive from runtime."""
    if WORKSPACE_URL:
        return WORKSPACE_URL
    try:
        host = request.app.state.runtime.ws.config.host or ""
        return host.replace("https://", "").rstrip("/")
    except Exception:
        return ""


@router.get(
    "/databricks-resources",
    response_model=HbDatabricksResourcesOut,
    operation_id="hb_getDatabricksResources",
)
async def get_databricks_resources(request: Request) -> HbDatabricksResourcesOut:
    """Return Databricks resource IDs for frontend embedding."""
    ws_url = _resolve_workspace_url(request)
    base = f"https://{ws_url}" if ws_url else ""
    return HbDatabricksResourcesOut(
        workspace_url=ws_url,
        sc_dashboard_id=SC_DASHBOARD_ID,
        sc_dashboard_embed_url=f"{base}/embed/dashboardsv3/{SC_DASHBOARD_ID}?embed" if base and SC_DASHBOARD_ID else "",
        aq_dashboard_id=AQ_DASHBOARD_ID,
        aq_dashboard_embed_url=f"{base}/embed/dashboardsv3/{AQ_DASHBOARD_ID}?embed" if base and AQ_DASHBOARD_ID else "",
        sc_genie_space_id=SC_GENIE_SPACE_ID,
        aq_genie_space_id=AQ_GENIE_SPACE_ID,
        configured=bool(ws_url),
    )
