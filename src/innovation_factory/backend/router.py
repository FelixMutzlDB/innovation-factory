import threading
from typing import Annotated

from databricks.sdk import WorkspaceClient
from databricks.sdk.service.iam import User as UserOut
from fastapi import APIRouter, Depends, Request

from .._metadata import api_prefix
from .dependencies import get_obo_ws
from .models import VersionOut

api = APIRouter(prefix=api_prefix)

_seed_started = False


@api.get("/version", response_model=VersionOut, operation_id="version")
async def version():
    return VersionOut.from_metadata()


@api.get("/current-user", operation_id="currentUser")
def me(obo_ws: Annotated[WorkspaceClient, Depends(get_obo_ws)]):
    """Get current user information."""
    user = obo_ws.current_user.me()
    if hasattr(user, "as_dict"):
        return user.as_dict()
    return {
        "id": getattr(user, "id", "local-dev-user"),
        "user_name": getattr(user, "user_name", "local@developer.com"),
        "display_name": getattr(user, "display_name", "Local Developer"),
        "active": getattr(user, "active", True),
        "emails": [{"value": "local@developer.com", "primary": True}],
        "name": {"given_name": "Local", "family_name": "Developer"},
    }


@api.post("/seed", operation_id="seedDatabase")
def seed_database(request: Request):
    """Trigger database seeding (local dev only)."""
    global _seed_started
    runtime = request.app.state.runtime
    if not runtime._dev_db_port:
        return {"status": "skipped", "message": "Seeding only available in local dev mode"}
    if _seed_started:
        return {"status": "already_started"}

    _seed_started = True

    def _do_seed():
        from .seed import check_and_seed_if_empty
        check_and_seed_if_empty(runtime)

    threading.Thread(target=_do_seed, daemon=True).start()
    return {"status": "started"}


# Platform routers
from .routers import projects, ideas

api.include_router(projects.router)
api.include_router(ideas.router)

# Project-specific routers (mounted under /projects/{slug}/)
from .projects.vi_home_one.router import router as vh_router
from .projects.bsh_home_connect.router import router as bsh_router

api.include_router(vh_router, prefix="/projects/vi-home-one")
api.include_router(bsh_router, prefix="/projects/bsh-home-connect")
