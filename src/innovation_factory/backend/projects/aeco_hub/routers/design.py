"""Design-phase endpoints: BIM models, clash reports, room requirements."""
from typing import Optional

from fastapi import APIRouter, HTTPException, Query
from sqlmodel import select

from ....dependencies import SessionDep
from ..models import (
    AecoBimDiscipline,
    AecoIssueSeverity,
    AecoIssueStatus,
    DtBimModel,
    DtBimModelOut,
    DtBuilding,
    DtClashReport,
    DtClashReportOut,
    DtFloor,
    DtProject,
    DtRoomRequirement,
    DtRoomRequirementOut,
    DtSpace,
)

router = APIRouter(tags=["aeco-hub"])


# -- BIM models -------------------------------------------------------


@router.get(
    "/projects/{project_id}/design/bim-models",
    response_model=list[DtBimModelOut],
    operation_id="aeco_listBimModels",
)
def list_bim_models(
    project_id: int,
    db: SessionDep,
    discipline: Optional[AecoBimDiscipline] = None,
    building_id: Optional[int] = None,
):
    if not db.get(DtProject, project_id):
        raise HTTPException(404, detail="Project not found")
    stmt = select(DtBimModel).where(DtBimModel.project_id == project_id)
    if discipline:
        stmt = stmt.where(DtBimModel.discipline == discipline)
    if building_id is not None:
        stmt = stmt.where(DtBimModel.building_id == building_id)
    stmt = stmt.order_by(DtBimModel.uploaded_at.desc())  # type: ignore[unresolved-attribute]
    return db.exec(stmt).all()


@router.get(
    "/bim-models/{bim_model_id}",
    response_model=DtBimModelOut,
    operation_id="aeco_getBimModel",
)
def get_bim_model(bim_model_id: int, db: SessionDep):
    model = db.get(DtBimModel, bim_model_id)
    if not model:
        raise HTTPException(404, detail="BIM model not found")
    return model


# -- Clash reports ----------------------------------------------------


@router.get(
    "/projects/{project_id}/design/clashes",
    response_model=list[DtClashReportOut],
    operation_id="aeco_listClashReports",
)
def list_clash_reports(
    project_id: int,
    db: SessionDep,
    severity: Optional[AecoIssueSeverity] = None,
    status: Optional[AecoIssueStatus] = None,
    limit: int = Query(default=50, ge=1, le=200),
    offset: int = Query(default=0, ge=0),
):
    if not db.get(DtProject, project_id):
        raise HTTPException(404, detail="Project not found")
    stmt = select(DtClashReport).where(DtClashReport.project_id == project_id)
    if severity:
        stmt = stmt.where(DtClashReport.severity == severity)
    if status:
        stmt = stmt.where(DtClashReport.status == status)
    stmt = stmt.order_by(DtClashReport.detected_at.desc()).offset(offset).limit(limit)  # type: ignore[unresolved-attribute]
    return db.exec(stmt).all()


# -- Room requirements ------------------------------------------------


@router.get(
    "/projects/{project_id}/design/room-requirements",
    response_model=list[DtRoomRequirementOut],
    operation_id="aeco_listRoomRequirements",
)
def list_room_requirements(
    project_id: int,
    db: SessionDep,
    is_met: Optional[bool] = None,
    limit: int = Query(default=100, ge=1, le=500),
    offset: int = Query(default=0, ge=0),
):
    """Room requirements across all spaces in a project."""
    if not db.get(DtProject, project_id):
        raise HTTPException(404, detail="Project not found")
    stmt = (
        select(DtRoomRequirement)
        .join(DtSpace, DtRoomRequirement.space_id == DtSpace.id)  # type: ignore[invalid-argument-type]
        .join(DtFloor, DtSpace.floor_id == DtFloor.id)  # type: ignore[invalid-argument-type]
        .join(DtBuilding, DtFloor.building_id == DtBuilding.id)  # type: ignore[invalid-argument-type]
        .where(DtBuilding.project_id == project_id)
    )
    if is_met is not None:
        stmt = stmt.where(DtRoomRequirement.is_met == is_met)
    stmt = stmt.order_by(DtRoomRequirement.id).offset(offset).limit(limit)  # type: ignore[invalid-argument-type]
    return db.exec(stmt).all()


@router.get(
    "/spaces/{space_id}/room-requirements",
    response_model=list[DtRoomRequirementOut],
    operation_id="aeco_listSpaceRoomRequirements",
)
def list_space_room_requirements(space_id: int, db: SessionDep):
    if not db.get(DtSpace, space_id):
        raise HTTPException(404, detail="Space not found")
    stmt = select(DtRoomRequirement).where(DtRoomRequirement.space_id == space_id)
    return db.exec(stmt).all()
