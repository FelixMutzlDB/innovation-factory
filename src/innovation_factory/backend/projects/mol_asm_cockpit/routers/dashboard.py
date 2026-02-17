"""Dashboard embedding endpoint for the ASM Cockpit."""
from typing import Optional

from fastapi import APIRouter, Request
from pydantic import BaseModel

from ..databricks_config import DASHBOARD_ID

router = APIRouter(prefix="/dashboard", tags=["mac-dashboard"])


class DashboardEmbedOut(BaseModel):
    embed_url: Optional[str] = None
    dashboard_id: Optional[str] = None
    configured: bool = False


@router.get(
    "/embed",
    response_model=DashboardEmbedOut,
    operation_id="mac_getDashboardEmbed",
)
def get_dashboard_embed(request: Request):
    """Get the embed URL for the AI/BI dashboard."""
    if not DASHBOARD_ID:
        return DashboardEmbedOut(configured=False)

    try:
        runtime = request.app.state.runtime
        host = runtime.ws.config.host
        host = host.rstrip("/")
        if not host.startswith("http"):
            host = f"https://{host}"

        embed_url = f"{host}/embed/dashboardsv3/{DASHBOARD_ID}"

        return DashboardEmbedOut(
            embed_url=embed_url,
            dashboard_id=DASHBOARD_ID,
            configured=True,
        )
    except Exception:
        return DashboardEmbedOut(
            dashboard_id=DASHBOARD_ID,
            configured=True,
        )
