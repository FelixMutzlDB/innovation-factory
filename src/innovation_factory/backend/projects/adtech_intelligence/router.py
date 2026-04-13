"""Main router for adtech-intelligence project, mounting all sub-routers."""
from fastapi import APIRouter, Request
from pydantic import BaseModel

from .routers import campaigns, inventory, anomalies, issues, chat
from .databricks_config import (
    DASHBOARD_ID,
    GENIE_SPACE_ID,
    MAS_TILE_ID,
    MAS_ENDPOINT_NAME,
    WAREHOUSE_ID,
    WORKSPACE_URL,
)

router = APIRouter(tags=["adtech-intelligence"])

router.include_router(campaigns.router)
router.include_router(inventory.router)
router.include_router(anomalies.router)
router.include_router(issues.router)
router.include_router(chat.router)


class DatabricksResourcesOut(BaseModel):
    dashboard_id: str
    dashboard_embed_url: str
    genie_space_id: str
    mas_tile_id: str
    mas_endpoint_name: str
    warehouse_id: str
    workspace_url: str
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
    response_model=DatabricksResourcesOut,
    operation_id="at_getDatabricksResources",
)
async def get_databricks_resources(request: Request) -> DatabricksResourcesOut:
    """Return Databricks resource IDs for frontend embedding."""
    ws_url = _resolve_workspace_url(request)
    embed_url = ""
    if ws_url and DASHBOARD_ID:
        embed_url = f"https://{ws_url}/embed/dashboardsv3/{DASHBOARD_ID}?embed"
    return DatabricksResourcesOut(
        dashboard_id=DASHBOARD_ID,
        dashboard_embed_url=embed_url,
        genie_space_id=GENIE_SPACE_ID,
        mas_tile_id=MAS_TILE_ID,
        mas_endpoint_name=MAS_ENDPOINT_NAME,
        warehouse_id=WAREHOUSE_ID,
        workspace_url=ws_url,
        configured=bool(ws_url and DASHBOARD_ID),
    )
