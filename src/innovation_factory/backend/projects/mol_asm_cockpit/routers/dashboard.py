"""Dashboard embedding endpoint for the ASM Cockpit."""
import os
from typing import Optional

from fastapi import APIRouter, Request
from pydantic import BaseModel

router = APIRouter(prefix="/dashboard", tags=["mac-dashboard"])

# Dashboard ID - created via scripts/create_asm_cockpit_dashboard.py
# Can also be overridden via environment variable MAC_DASHBOARD_ID
DASHBOARD_ID: Optional[str] = "01f10b3a58ee1f78b2179c1cb31c485d"


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
    dashboard_id = DASHBOARD_ID or os.environ.get("MAC_DASHBOARD_ID")

    if not dashboard_id:
        return DashboardEmbedOut(configured=False)

    try:
        runtime = request.app.state.runtime
        host = runtime.ws.config.host
        # Strip trailing slash and protocol
        host = host.rstrip("/")
        if not host.startswith("http"):
            host = f"https://{host}"

        embed_url = f"{host}/embed/dashboardsv3/{dashboard_id}"

        return DashboardEmbedOut(
            embed_url=embed_url,
            dashboard_id=dashboard_id,
            configured=True,
        )
    except Exception:
        return DashboardEmbedOut(
            dashboard_id=dashboard_id,
            configured=True,
            embed_url=f"https://e2-demo-field-eng.cloud.databricks.com/embed/dashboardsv3/{dashboard_id}",
        )
