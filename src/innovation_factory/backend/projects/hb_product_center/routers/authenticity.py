"""Authenticity verification and alert endpoints."""

from typing import Optional

from fastapi import APIRouter, HTTPException, Query
from sqlmodel import select

from ....dependencies import SessionDep
from ..models import (
    HbAuthAlert,
    HbAuthAlertOut,
    HbAuthAlertUpdate,
    HbAuthVerification,
    HbAuthVerificationCreate,
    HbAuthVerificationOut,
)
from ..services.authenticity_service import verify_product

router = APIRouter(prefix="/authenticity", tags=["hb-product-center"])


@router.get("/verifications", response_model=list[HbAuthVerificationOut], operation_id="hb_listVerifications")
def list_verifications(
    session: SessionDep,
    status: Optional[str] = Query(None),
    requester_type: Optional[str] = Query(None),
    limit: int = Query(50, le=200),
    offset: int = Query(0),
):
    stmt = select(HbAuthVerification)
    if status:
        stmt = stmt.where(HbAuthVerification.status == status)
    if requester_type:
        stmt = stmt.where(HbAuthVerification.requester_type == requester_type)
    stmt = stmt.order_by(HbAuthVerification.created_at.desc()).offset(offset).limit(limit)  # type: ignore[union-attr]
    return list(session.exec(stmt).all())


@router.get("/verifications/{verification_id}", response_model=HbAuthVerificationOut, operation_id="hb_getVerification")
def get_verification(verification_id: int, session: SessionDep):
    v = session.get(HbAuthVerification, verification_id)
    if not v:
        raise HTTPException(status_code=404, detail="Verification not found")
    return v


@router.post("/verify", response_model=HbAuthVerificationOut, operation_id="hb_createVerification")
def create_verification(data: HbAuthVerificationCreate, session: SessionDep):
    verification = HbAuthVerification(**data.model_dump())
    session.add(verification)
    session.flush()
    verification = verify_product(session, verification)
    session.commit()
    return verification


@router.get("/alerts", response_model=list[HbAuthAlertOut], operation_id="hb_listAlerts")
def list_alerts(
    session: SessionDep,
    resolution: Optional[str] = Query(None),
    limit: int = Query(50, le=200),
    offset: int = Query(0),
):
    stmt = select(HbAuthAlert)
    if resolution:
        stmt = stmt.where(HbAuthAlert.resolution == resolution)
    stmt = stmt.order_by(HbAuthAlert.created_at.desc()).offset(offset).limit(limit)  # type: ignore[union-attr]
    return list(session.exec(stmt).all())


@router.patch("/alerts/{alert_id}", response_model=HbAuthAlertOut, operation_id="hb_updateAlert")
def update_alert(alert_id: int, data: HbAuthAlertUpdate, session: SessionDep):
    alert = session.get(HbAuthAlert, alert_id)
    if not alert:
        raise HTTPException(status_code=404, detail="Alert not found")
    update_data = data.model_dump(exclude_unset=True)
    for key, value in update_data.items():
        setattr(alert, key, value)
    session.add(alert)
    session.commit()
    session.refresh(alert)
    return alert
