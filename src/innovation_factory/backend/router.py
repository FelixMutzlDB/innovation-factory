import threading
from pathlib import Path
from typing import Annotated

from databricks.sdk import WorkspaceClient
from databricks.sdk.service.iam import User as UserOut
from fastapi import APIRouter, Depends, HTTPException, Request
from pydantic import BaseModel

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


class DocListOut(BaseModel):
    slugs: list[str]


class DocContentOut(BaseModel):
    slug: str
    title: str
    content: str


_DOCS_DIR = Path(__file__).resolve().parent.parent.parent.parent / "docs" / "projects"


@api.get(
    "/docs/projects",
    response_model=DocListOut,
    operation_id="listProjectDocs",
)
async def list_project_docs():
    """List available project documentation slugs."""
    if not _DOCS_DIR.exists():
        return DocListOut(slugs=[])
    slugs = sorted(p.stem for p in _DOCS_DIR.glob("*.md"))
    return DocListOut(slugs=slugs)


@api.get(
    "/docs/projects/{slug}",
    response_model=DocContentOut,
    operation_id="getProjectDoc",
)
async def get_project_doc(slug: str):
    """Get markdown content for a project's documentation."""
    md_file = _DOCS_DIR / f"{slug}.md"
    if not md_file.exists():
        raise HTTPException(status_code=404, detail=f"Documentation not found for '{slug}'")
    content = md_file.read_text(encoding="utf-8")
    # Extract title from first markdown heading
    title = slug
    for line in content.splitlines():
        if line.startswith("# "):
            title = line[2:].strip()
            break
    return DocContentOut(slug=slug, title=title, content=content)


# Platform routers
from .routers import projects, ideas

api.include_router(projects.router)
api.include_router(ideas.router)

# Project-specific routers (mounted under /projects/{slug}/)
from .projects.vi_home_one.router import router as vh_router
from .projects.bsh_home_connect.router import router as bsh_router
from .projects.mol_asm_cockpit.router import router as mac_router
from .projects.adtech_intelligence.router import router as at_router
from .projects.hb_product_center.router import router as hb_router

api.include_router(vh_router, prefix="/projects/vi-home-one")
api.include_router(bsh_router, prefix="/projects/bsh-home-connect")
api.include_router(mac_router, prefix="/projects/mol-asm-cockpit")
api.include_router(at_router, prefix="/projects/adtech-intelligence")
api.include_router(hb_router, prefix="/projects/hb-product-center")
