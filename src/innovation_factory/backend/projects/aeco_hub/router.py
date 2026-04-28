"""Main router for AECO Hub, mounting all sub-routers."""

from fastapi import APIRouter, Request
from pydantic import BaseModel

from .databricks_config import (
    ENERGY_DASHBOARD_ID,
    MAS_ENDPOINT_NAME,
    OPERATIONS_INTELLIGENCE_GENIE_SPACE_ID,
    PROJECT_ANALYTICS_GENIE_SPACE_ID,
    STANDARDS_COMPLIANCE_KA_ENDPOINT,
    WORKSPACE_URL,
)
from .routers import build, chat, design, documents, issues, marketplace, operate, projects

router = APIRouter(tags=["aeco-hub"])

router.include_router(projects.router)
router.include_router(issues.router)
router.include_router(documents.router)
router.include_router(design.router)
router.include_router(build.router)
router.include_router(operate.router)
router.include_router(marketplace.router)
router.include_router(chat.router)


class AecoDatabricksResourcesOut(BaseModel):
    workspace_url: str
    energy_dashboard_id: str
    energy_dashboard_embed_url: str
    energy_dashboard_configured: bool = False
    project_analytics_genie_space_id: str
    operations_intelligence_genie_space_id: str
    standards_compliance_ka_endpoint: str
    standards_compliance_ka_configured: bool = False
    mas_endpoint_name: str
    mas_configured: bool = False
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
        standards_compliance_ka_endpoint=STANDARDS_COMPLIANCE_KA_ENDPOINT,
        standards_compliance_ka_configured=bool(STANDARDS_COMPLIANCE_KA_ENDPOINT),
        mas_endpoint_name=MAS_ENDPOINT_NAME,
        mas_configured=bool(MAS_ENDPOINT_NAME),
        configured=bool(ws_url),
    )
