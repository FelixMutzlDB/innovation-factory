"""Quality control inspection and defect endpoints."""

from typing import Annotated, Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from fastapi.responses import StreamingResponse
from sqlmodel import Session, func, select

from ....dependencies import SessionDep, get_session, get_runtime
from ....runtime import Runtime
from ..models import (
    HbChatMessageIn,
    HbProduct,
    HbProductOut,
    HbQualityDefect,
    HbQualityDefectOut,
    HbQualityInspection,
    HbQualityInspectionCreate,
    HbQualityInspectionOut,
    HbQualityInspectionUpdate,
    HbQualityStats,
    HbInspectionDetailOut,
    InspectionStatus,
)
from ..services.quality_service import run_quality_inspection
from ..services.quality_knowledge_service import QualityKnowledgeService

router = APIRouter(prefix="/quality", tags=["hb-product-center"])

_quality_assistant = QualityKnowledgeService()


@router.get("/inspections", response_model=list[HbQualityInspectionOut], operation_id="hb_listInspections")
def list_inspections(
    session: SessionDep,
    status: Optional[str] = Query(None),
    product_id: Optional[int] = Query(None),
    limit: int = Query(50, le=200),
    offset: int = Query(0),
):
    stmt = select(HbQualityInspection)
    if status:
        stmt = stmt.where(HbQualityInspection.status == status)
    if product_id:
        stmt = stmt.where(HbQualityInspection.product_id == product_id)
    stmt = stmt.order_by(HbQualityInspection.created_at.desc()).offset(offset).limit(limit)  # type: ignore[union-attr]
    return list(session.exec(stmt).all())


@router.get("/inspections/{inspection_id}", response_model=HbInspectionDetailOut, operation_id="hb_getInspection")
def get_inspection(inspection_id: int, session: SessionDep):
    inspection = session.get(HbQualityInspection, inspection_id)
    if not inspection:
        raise HTTPException(status_code=404, detail="Inspection not found")
    defects = list(session.exec(
        select(HbQualityDefect).where(HbQualityDefect.inspection_id == inspection_id)
    ).all())
    product = session.get(HbProduct, inspection.product_id)
    return HbInspectionDetailOut(
        **inspection.model_dump(),
        defects=[HbQualityDefectOut(**d.model_dump()) for d in defects],
        product=HbProductOut(**product.model_dump()) if product else None,
    )


@router.post("/inspections", response_model=HbQualityInspectionOut, operation_id="hb_createInspection")
def create_inspection(data: HbQualityInspectionCreate, session: SessionDep):
    product = session.get(HbProduct, data.product_id)
    if not product:
        raise HTTPException(status_code=404, detail="Product not found")
    inspection = HbQualityInspection(**data.model_dump())
    session.add(inspection)
    session.flush()
    inspection = run_quality_inspection(session, inspection)
    session.commit()
    return inspection


@router.patch("/inspections/{inspection_id}", response_model=HbQualityInspectionOut, operation_id="hb_updateInspection")
def update_inspection(inspection_id: int, data: HbQualityInspectionUpdate, session: SessionDep):
    inspection = session.get(HbQualityInspection, inspection_id)
    if not inspection:
        raise HTTPException(status_code=404, detail="Inspection not found")
    update_data = data.model_dump(exclude_unset=True)
    for key, value in update_data.items():
        setattr(inspection, key, value)
    session.add(inspection)
    session.commit()
    session.refresh(inspection)
    return inspection


@router.get("/stats", response_model=HbQualityStats, operation_id="hb_getQualityStats")
def get_quality_stats(session: SessionDep):
    inspections = list(session.exec(select(HbQualityInspection)).all())
    defects = list(session.exec(select(HbQualityDefect)).all())

    status_counts = {s.value: 0 for s in InspectionStatus}
    scores = []
    for insp in inspections:
        status_counts[insp.status.value] = status_counts.get(insp.status.value, 0) + 1
        if insp.overall_score > 0:
            scores.append(insp.overall_score)

    defect_counts: dict[str, int] = {}
    severity_counts: dict[str, int] = {}
    for d in defects:
        defect_counts[d.defect_type.value] = defect_counts.get(d.defect_type.value, 0) + 1
        severity_counts[d.severity.value] = severity_counts.get(d.severity.value, 0) + 1

    return HbQualityStats(
        total_inspections=len(inspections),
        approved=status_counts.get("approved", 0),
        rejected=status_counts.get("rejected", 0),
        pending=status_counts.get("pending", 0),
        in_review=status_counts.get("in_review", 0),
        avg_score=round(sum(scores) / len(scores), 1) if scores else 0.0,
        defect_counts=defect_counts,
        severity_counts=severity_counts,
    )


@router.post("/assistant-chat", operation_id="hb_sendQualityAssistantMessage")
async def send_quality_assistant_message(
    message: HbChatMessageIn,
    db: Annotated[Session, Depends(get_session)],
    runtime: Annotated[Runtime, Depends(get_runtime)],
):
    """Send a message to the Quality Knowledge Assistant (streaming)."""

    async def event_generator():
        async for chunk in _quality_assistant.stream_response(
            ws=runtime.ws,
            db=db,
            user_message=message.content,
            session_id=message.session_id,
        ):
            yield f"data: {chunk}\n\n"

    return StreamingResponse(
        event_generator(),
        media_type="text/event-stream",
        headers={"Cache-Control": "no-cache", "Connection": "keep-alive"},
    )
