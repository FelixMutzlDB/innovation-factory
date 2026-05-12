"""Main router for yard-pro project, mounting all sub-routers.

Sub-routers are added incrementally as Phase B streams land. The Phase A
skeleton registers nothing; the ``/api/projects/yard-pro/databricks-resources``
endpoint surfaces config status so the cockpit can render a "not configured"
card when env vars are missing (lessons §18).
"""
from fastapi import APIRouter, Request
from pydantic import BaseModel

from .databricks_config import (
    COACH_KA_ENDPOINT,
    COACH_MODEL,
    COACH_MODEL_FALLBACK,
    DEALER_GENIE_SPACE_ID,
    VISION_ENDPOINT,
    WORKSPACE_URL,
)

router = APIRouter(tags=["yard-pro"])

# Stream B1 (foundation CRUD + Art. 22 rail) — keep this block to the five
# imports/includes B1 owns; B2 adds coach.py + diagnose.py below.
from .routers import actions, inventory, plants, tools, yards

router.include_router(yards.router)
router.include_router(plants.router)
router.include_router(tools.router)
router.include_router(inventory.router)
router.include_router(actions.router)

# Stream B2 (coach + diagnose + calendar regen) — owns these two includes only.
from .routers import coach, diagnose

router.include_router(coach.router)
router.include_router(diagnose.router)

# UC4 (P1) — telemetry synthesizer + nudges surface. Notifications-only;
# never writes into yp_action_log (Art. 22 invariant).
from .routers import nudges

router.include_router(nudges.router)


class YardProDatabricksResourcesOut(BaseModel):
    workspace_url: str
    coach_model: str
    coach_model_fallback: str
    coach_ka_endpoint: str
    coach_ka_configured: bool = False
    vision_endpoint: str
    vision_configured: bool = False
    dealer_genie_space_id: str
    dealer_genie_configured: bool = False
    configured: bool = False


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
    response_model=YardProDatabricksResourcesOut,
    operation_id="yp_getDatabricksResources",
)
async def get_databricks_resources(request: Request) -> YardProDatabricksResourcesOut:
    """Return Databricks resource configuration for the yard-pro frontend.

    Each ``*_configured`` flag is the UI's signal to render the live AI
    surface vs the "not configured" card (lessons §18).
    """
    ws_url = _resolve_workspace_url(request)
    return YardProDatabricksResourcesOut(
        workspace_url=ws_url,
        coach_model=COACH_MODEL,
        coach_model_fallback=COACH_MODEL_FALLBACK,
        coach_ka_endpoint=COACH_KA_ENDPOINT,
        coach_ka_configured=bool(COACH_KA_ENDPOINT),
        vision_endpoint=VISION_ENDPOINT,
        vision_configured=bool(VISION_ENDPOINT),
        dealer_genie_space_id=DEALER_GENIE_SPACE_ID,
        dealer_genie_configured=bool(DEALER_GENIE_SPACE_ID),
        configured=bool(ws_url),
    )
