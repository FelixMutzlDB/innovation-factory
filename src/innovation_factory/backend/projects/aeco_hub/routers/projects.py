"""Construction-project, building, floor, and space CRUD for AECO Hub.

These endpoints serve the portfolio overview, project detail, and the
spatial drilldown for the twin view (project → building → floor → space).
They use Lakebase (SQLModel) — IoT sensor readings are read from UC and
will land in Phase 3 in a separate router.

URL design note: this router mounts under ``/projects/aeco-hub`` (in
``backend/router.py``), so a "construction project" lives at e.g.
``/api/projects/aeco-hub/projects/{id}``. The redundancy is intentional:
the platform's ``/api/projects`` lists accelerators, and the per-accelerator
``/projects`` lists construction projects. The ``aeco_*`` operation_id
prefix keeps the OpenAPI namespace clean.
"""
from typing import Optional

from fastapi import APIRouter, HTTPException, Query
from sqlmodel import func, select

from ....dependencies import SessionDep
from ..models import (
    AecoIssueStatus,
    AecoProjectPhase,
    AecoProjectStatus,
    DtBuilding,
    DtBuildingOut,
    DtDocument,
    DtFloor,
    DtFloorOut,
    DtIssue,
    DtPortfolioStatsOut,
    DtProject,
    DtProjectKpiOut,
    DtProjectMember,
    DtProjectMemberOut,
    DtProjectOut,
    DtSpace,
    DtSpaceOut,
    DtTwinBuildingOut,
    DtTwinFloorOut,
    DtTwinOut,
    DtTwinSpaceOut,
)

router = APIRouter(tags=["aeco-hub"])


# -- Portfolio ----------------------------------------------------------


@router.get(
    "/portfolio/stats",
    response_model=DtPortfolioStatsOut,
    operation_id="aeco_getPortfolioStats",
)
def get_portfolio_stats(db: SessionDep) -> DtPortfolioStatsOut:
    """Return high-level portfolio KPIs for the AECO Hub home page."""
    total_projects = db.exec(select(func.count(DtProject.id))).one()
    active_projects = db.exec(
        select(func.count(DtProject.id)).where(DtProject.status == AecoProjectStatus.active)
    ).one()
    operating = db.exec(
        select(func.count(DtProject.id)).where(DtProject.phase == AecoProjectPhase.operate)
    ).one()
    constructing = db.exec(
        select(func.count(DtProject.id)).where(DtProject.phase == AecoProjectPhase.build)
    ).one()
    designing = db.exec(
        select(func.count(DtProject.id)).where(DtProject.phase == AecoProjectPhase.design)
    ).one()
    total_budget = db.exec(select(func.coalesce(func.sum(DtProject.budget_eur), 0))).one()
    total_actual = db.exec(select(func.coalesce(func.sum(DtProject.actual_cost_eur), 0))).one()
    total_buildings = db.exec(select(func.count(DtBuilding.id))).one()

    return DtPortfolioStatsOut(
        total_projects=total_projects,
        active_projects=active_projects,
        operating_projects=operating,
        constructing_projects=constructing,
        design_projects=designing,
        total_budget_eur=round(float(total_budget), 2),
        total_actual_cost_eur=round(float(total_actual), 2),
        total_buildings=total_buildings,
    )


# -- Projects ----------------------------------------------------------


@router.get(
    "/projects",
    response_model=list[DtProjectOut],
    operation_id="aeco_listProjects",
)
def list_projects(
    db: SessionDep,
    phase: Optional[AecoProjectPhase] = None,
    status: Optional[AecoProjectStatus] = None,
    limit: int = Query(default=50, ge=1, le=200),
    offset: int = Query(default=0, ge=0),
):
    """List construction projects with optional phase/status filters."""
    stmt = select(DtProject)
    if phase:
        stmt = stmt.where(DtProject.phase == phase)
    if status:
        stmt = stmt.where(DtProject.status == status)
    stmt = stmt.order_by(DtProject.code).offset(offset).limit(limit)
    return db.exec(stmt).all()


@router.get(
    "/projects/{project_id}",
    response_model=DtProjectOut,
    operation_id="aeco_getProject",
)
def get_project(project_id: int, db: SessionDep):
    project = db.get(DtProject, project_id)
    if not project:
        raise HTTPException(404, detail="Project not found")
    return project


@router.get(
    "/projects/{project_id}/kpis",
    response_model=DtProjectKpiOut,
    operation_id="aeco_getProjectKpis",
)
def get_project_kpis(project_id: int, db: SessionDep) -> DtProjectKpiOut:
    """Aggregated KPIs for the project overview page."""
    project = db.get(DtProject, project_id)
    if not project:
        raise HTTPException(404, detail="Project not found")

    building_count = db.exec(
        select(func.count(DtBuilding.id)).where(DtBuilding.project_id == project_id)
    ).one()
    floor_count = db.exec(
        select(func.count(DtFloor.id))
        .join(DtBuilding, DtFloor.building_id == DtBuilding.id)
        .where(DtBuilding.project_id == project_id)
    ).one()
    space_count = db.exec(
        select(func.count(DtSpace.id))
        .join(DtFloor, DtSpace.floor_id == DtFloor.id)
        .join(DtBuilding, DtFloor.building_id == DtBuilding.id)
        .where(DtBuilding.project_id == project_id)
    ).one()
    member_count = db.exec(
        select(func.count(DtProjectMember.id)).where(DtProjectMember.project_id == project_id)
    ).one()
    open_issues = db.exec(
        select(func.count(DtIssue.id)).where(
            DtIssue.project_id == project_id,
            DtIssue.status.in_([AecoIssueStatus.open, AecoIssueStatus.in_review, AecoIssueStatus.in_progress]),  # type: ignore[unresolved-attribute]
        )
    ).one()
    documents_count = db.exec(
        select(func.count(DtDocument.id)).where(DtDocument.project_id == project_id)
    ).one()

    cost_variance_pct = 0.0
    if project.budget_eur > 0:
        cost_variance_pct = round(
            ((project.actual_cost_eur - project.budget_eur) / project.budget_eur) * 100.0, 2
        )

    return DtProjectKpiOut(
        project_id=project_id,
        building_count=building_count,
        floor_count=floor_count,
        space_count=space_count,
        member_count=member_count,
        open_issues=open_issues,
        documents_count=documents_count,
        progress_pct=project.progress_pct,
        budget_eur=project.budget_eur,
        actual_cost_eur=project.actual_cost_eur,
        cost_variance_pct=cost_variance_pct,
    )


@router.get(
    "/projects/{project_id}/twin",
    response_model=DtTwinOut,
    operation_id="aeco_getProjectTwin",
)
def get_project_twin(project_id: int, db: SessionDep) -> DtTwinOut:
    """Full spatial hierarchy for the twin view (project → building → floor → space).

    Single-shot endpoint to avoid N+1 queries from the tree UI. Bounded by
    the seed-data caps (~3 buildings × ~6 floors × ~14 spaces ≤ 250 nodes).
    """
    project = db.get(DtProject, project_id)
    if not project:
        raise HTTPException(404, detail="Project not found")

    buildings = list(
        db.exec(select(DtBuilding).where(DtBuilding.project_id == project_id).order_by(DtBuilding.name)).all()
    )
    out_buildings: list[DtTwinBuildingOut] = []
    for bldg in buildings:
        floors = list(
            db.exec(select(DtFloor).where(DtFloor.building_id == bldg.id).order_by(DtFloor.level)).all()  # type: ignore[invalid-argument-type]
        )
        out_floors: list[DtTwinFloorOut] = []
        for floor in floors:
            spaces = list(
                db.exec(select(DtSpace).where(DtSpace.floor_id == floor.id).order_by(DtSpace.room_number)).all()
            )
            out_floors.append(
                DtTwinFloorOut(
                    id=floor.id or 0,
                    name=floor.name,
                    level=floor.level,
                    area_sqm=floor.area_sqm,
                    spaces=[
                        DtTwinSpaceOut(
                            id=s.id or 0,
                            name=s.name,
                            space_type=s.space_type,
                            area_sqm=s.area_sqm,
                            capacity=s.capacity,
                            room_number=s.room_number,
                        )
                        for s in spaces
                    ],
                )
            )
        out_buildings.append(
            DtTwinBuildingOut(
                id=bldg.id or 0,
                name=bldg.name,
                building_type=bldg.building_type,
                floor_count=bldg.floor_count,
                gross_floor_area_sqm=bldg.gross_floor_area_sqm,
                floors=out_floors,
            )
        )
    return DtTwinOut(
        project_id=project_id,
        project_name=project.name,
        project_phase=project.phase,
        buildings=out_buildings,
    )


@router.get(
    "/projects/{project_id}/members",
    response_model=list[DtProjectMemberOut],
    operation_id="aeco_listProjectMembers",
)
def list_project_members(project_id: int, db: SessionDep):
    if not db.get(DtProject, project_id):
        raise HTTPException(404, detail="Project not found")
    stmt = select(DtProjectMember).where(DtProjectMember.project_id == project_id)
    return db.exec(stmt).all()


# -- Buildings ----------------------------------------------------------


@router.get(
    "/projects/{project_id}/buildings",
    response_model=list[DtBuildingOut],
    operation_id="aeco_listBuildings",
)
def list_buildings(project_id: int, db: SessionDep):
    if not db.get(DtProject, project_id):
        raise HTTPException(404, detail="Project not found")
    stmt = (
        select(DtBuilding)
        .where(DtBuilding.project_id == project_id)
        .order_by(DtBuilding.name)
    )
    return db.exec(stmt).all()


@router.get(
    "/buildings/{building_id}",
    response_model=DtBuildingOut,
    operation_id="aeco_getBuilding",
)
def get_building(building_id: int, db: SessionDep):
    building = db.get(DtBuilding, building_id)
    if not building:
        raise HTTPException(404, detail="Building not found")
    return building


# -- Floors -------------------------------------------------------------


@router.get(
    "/buildings/{building_id}/floors",
    response_model=list[DtFloorOut],
    operation_id="aeco_listFloors",
)
def list_floors(building_id: int, db: SessionDep):
    if not db.get(DtBuilding, building_id):
        raise HTTPException(404, detail="Building not found")
    stmt = select(DtFloor).where(DtFloor.building_id == building_id).order_by(DtFloor.level)  # type: ignore[invalid-argument-type]
    return db.exec(stmt).all()


@router.get(
    "/floors/{floor_id}",
    response_model=DtFloorOut,
    operation_id="aeco_getFloor",
)
def get_floor(floor_id: int, db: SessionDep):
    floor = db.get(DtFloor, floor_id)
    if not floor:
        raise HTTPException(404, detail="Floor not found")
    return floor


# -- Spaces -------------------------------------------------------------


@router.get(
    "/floors/{floor_id}/spaces",
    response_model=list[DtSpaceOut],
    operation_id="aeco_listSpaces",
)
def list_spaces(floor_id: int, db: SessionDep):
    if not db.get(DtFloor, floor_id):
        raise HTTPException(404, detail="Floor not found")
    stmt = select(DtSpace).where(DtSpace.floor_id == floor_id).order_by(DtSpace.room_number)
    return db.exec(stmt).all()


@router.get(
    "/spaces/{space_id}",
    response_model=DtSpaceOut,
    operation_id="aeco_getSpace",
)
def get_space(space_id: int, db: SessionDep):
    space = db.get(DtSpace, space_id)
    if not space:
        raise HTTPException(404, detail="Space not found")
    return space
