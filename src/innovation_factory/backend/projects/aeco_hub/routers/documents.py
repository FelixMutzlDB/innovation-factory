"""Document library endpoints with lifecycle-phase filtering."""
from typing import Optional

from fastapi import APIRouter, HTTPException, Query
from sqlmodel import func, select

from ....dependencies import SessionDep
from ..models import (
    AecoDocumentType,
    AecoProjectPhase,
    DtDocument,
    DtDocumentOut,
    DtProject,
)
from pydantic import BaseModel

router = APIRouter(tags=["aeco-hub"])


class DtDocumentStatsOut(BaseModel):
    project_id: int
    total: int
    by_phase: dict[str, int]
    by_type: dict[str, int]


@router.get(
    "/projects/{project_id}/documents",
    response_model=list[DtDocumentOut],
    operation_id="aeco_listDocuments",
)
def list_documents(
    project_id: int,
    db: SessionDep,
    phase: Optional[AecoProjectPhase] = None,
    document_type: Optional[AecoDocumentType] = None,
    limit: int = Query(default=50, ge=1, le=200),
    offset: int = Query(default=0, ge=0),
):
    if not db.get(DtProject, project_id):
        raise HTTPException(404, detail="Project not found")
    stmt = select(DtDocument).where(DtDocument.project_id == project_id)
    if phase:
        stmt = stmt.where(DtDocument.phase == phase)
    if document_type:
        stmt = stmt.where(DtDocument.document_type == document_type)
    stmt = stmt.order_by(DtDocument.created_at.desc()).offset(offset).limit(limit)  # type: ignore[unresolved-attribute]
    return db.exec(stmt).all()


@router.get(
    "/projects/{project_id}/documents/stats",
    response_model=DtDocumentStatsOut,
    operation_id="aeco_getDocumentStats",
)
def get_document_stats(project_id: int, db: SessionDep) -> DtDocumentStatsOut:
    if not db.get(DtProject, project_id):
        raise HTTPException(404, detail="Project not found")
    base = select(func.count(DtDocument.id)).where(DtDocument.project_id == project_id)
    total = db.exec(base).one()
    by_phase = {p.value: db.exec(base.where(DtDocument.phase == p)).one() for p in AecoProjectPhase}
    by_type = {t.value: db.exec(base.where(DtDocument.document_type == t)).one() for t in AecoDocumentType}
    return DtDocumentStatsOut(
        project_id=project_id,
        total=total,
        by_phase=by_phase,
        by_type=by_type,
    )


@router.get(
    "/documents/{document_id}",
    response_model=DtDocumentOut,
    operation_id="aeco_getDocument",
)
def get_document(document_id: int, db: SessionDep):
    doc = db.get(DtDocument, document_id)
    if not doc:
        raise HTTPException(404, detail="Document not found")
    return doc
