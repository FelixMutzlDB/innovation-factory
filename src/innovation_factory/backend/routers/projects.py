from typing import List
from fastapi import APIRouter, HTTPException
from sqlmodel import select

from ..dependencies import SessionDep
from ..models import Project, ProjectOut

router = APIRouter(tags=["projects"])


@router.get("/projects", response_model=List[ProjectOut], operation_id="listProjects")
def list_projects(db: SessionDep):
    """List all available projects for the gallery."""
    statement = select(Project).order_by(Project.created_at.asc())  # type: ignore[unresolved-attribute]
    projects = db.exec(statement).all()
    return list(projects)


@router.get("/projects/{slug}", response_model=ProjectOut, operation_id="getProject")
def get_project(slug: str, db: SessionDep):
    """Get a project by slug."""
    statement = select(Project).where(Project.slug == slug)
    project = db.exec(statement).first()
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
    return project
