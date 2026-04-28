"""Main router for AECO Hub, mounting all sub-routers."""

from fastapi import APIRouter, Request
from pydantic import BaseModel

from .databricks_config import (
    ENERGY_DASHBOARD_ID,
    OPERATIONS_INTELLIGENCE_GENIE_SPACE_ID,
    PROJECT_ANALYTICS_GENIE_SPACE_ID,
    WORKSPACE_URL,
)
from .routers import build, design, documents, issues, operate, projects

router = APIRouter(tags=["aeco-hub"])

router.include_router(projects.router)
router.include_router(issues.router)
router.include_router(documents.router)
router.include_router(design.router)
router.include_router(build.router)
router.include_router(operate.router)


class AecoDatabricksResourcesOut(BaseModel):
    workspace_url: str
    energy_dashboard_id: str
    energy_dashboard_embed_url: str
    energy_dashboard_configured: bool = False
    project_analytics_genie_space_id: str
    operations_intelligence_genie_space_id: str
    configured: bool = False  # workspace URL resolved


def _resolve_workspace_url(request: Request) -> str:
    if WORKSPACE_URL:
        return WORKSPACE_URL
    try:
        host = request.app.state.runtime.ws.config.host or ""
        return host.replace("https://", "").rstrip("/")
    except Exception:
        return ""


@router.get(
    "/databricks-resources",
    response_model=AecoDatabricksResourcesOut,
    operation_id="aeco_getDatabricksResources",
)
async def get_databricks_resources(request: Request) -> AecoDatabricksResourcesOut:
    """Return Databricks resource IDs for frontend embedding."""
    ws_url = _resolve_workspace_url(request)
    base = f"https://{ws_url}" if ws_url else ""
    energy_ready = bool(base and ENERGY_DASHBOARD_ID)
    return AecoDatabricksResourcesOut(
        workspace_url=ws_url,
        energy_dashboard_id=ENERGY_DASHBOARD_ID,
        energy_dashboard_embed_url=(
            f"{base}/embed/dashboardsv3/{ENERGY_DASHBOARD_ID}?embed" if energy_ready else ""
        ),
        energy_dashboard_configured=energy_ready,
        project_analytics_genie_space_id=PROJECT_ANALYTICS_GENIE_SPACE_ID,
        operations_intelligence_genie_space_id=OPERATIONS_INTELLIGENCE_GENIE_SPACE_ID,
        configured=bool(ws_url),
    )
