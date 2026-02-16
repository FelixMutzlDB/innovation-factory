"""Anomaly detection routes for AdTech Intelligence."""
from typing import Annotated, Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlmodel import Session, func, select
from datetime import datetime

from ....dependencies import get_session
from ..models import (
    AnomalySeverity,
    AnomalyStatus,
    AnomalyType,
    AtAnomaly,
    AtAnomalyOut,
    AtAnomalyRule,
    AtAnomalyRuleOut,
    AtAnomalyUpdate,
)

router = APIRouter(tags=["adtech-anomalies"])


# -- Anomaly counts (for badges) ----------------------------------------


@router.get(
    "/anomalies/counts",
    operation_id="at_getAnomalyCounts",
)
def get_anomaly_counts(
    db: Annotated[Session, Depends(get_session)],
):
    """Return anomaly counts grouped by severity for active anomalies."""
    active_statuses = [AnomalyStatus.new, AnomalyStatus.acknowledged, AnomalyStatus.investigating]
    stmt = (
        select(AtAnomaly.severity, func.count(AtAnomaly.id))
        .where(AtAnomaly.status.in_(active_statuses))
        .group_by(AtAnomaly.severity)
    )
    rows = db.exec(stmt).all()
    counts = {s.value: 0 for s in AnomalySeverity}
    for severity, count in rows:
        counts[severity] = count
    counts["total"] = sum(counts.values())
    return counts


# -- Anomalies ----------------------------------------------------------


@router.get(
    "/anomalies",
    response_model=list[AtAnomalyOut],
    operation_id="at_listAnomalies",
)
def list_anomalies(
    db: Annotated[Session, Depends(get_session)],
    status: Optional[AnomalyStatus] = None,
    severity: Optional[AnomalySeverity] = None,
    anomaly_type: Optional[AnomalyType] = None,
    campaign_id: Optional[int] = None,
    limit: int = Query(default=50, le=200),
    offset: int = 0,
):
    """List anomalies with optional filters."""
    stmt = select(AtAnomaly)
    if status:
        stmt = stmt.where(AtAnomaly.status == status)
    if severity:
        stmt = stmt.where(AtAnomaly.severity == severity)
    if anomaly_type:
        stmt = stmt.where(AtAnomaly.anomaly_type == anomaly_type)
    if campaign_id:
        stmt = stmt.where(AtAnomaly.campaign_id == campaign_id)
    stmt = stmt.order_by(AtAnomaly.detected_at.desc()).offset(offset).limit(limit)
    return db.exec(stmt).all()


@router.get(
    "/anomalies/{anomaly_id}",
    response_model=AtAnomalyOut,
    operation_id="at_getAnomaly",
)
def get_anomaly(
    anomaly_id: int,
    db: Annotated[Session, Depends(get_session)],
):
    anomaly = db.get(AtAnomaly, anomaly_id)
    if not anomaly:
        raise HTTPException(404, detail="Anomaly not found")
    return anomaly


@router.patch(
    "/anomalies/{anomaly_id}",
    response_model=AtAnomalyOut,
    operation_id="at_updateAnomaly",
)
def update_anomaly(
    anomaly_id: int,
    body: AtAnomalyUpdate,
    db: Annotated[Session, Depends(get_session)],
):
    anomaly = db.get(AtAnomaly, anomaly_id)
    if not anomaly:
        raise HTTPException(404, detail="Anomaly not found")
    for key, value in body.model_dump(exclude_unset=True).items():
        setattr(anomaly, key, value)
    if body.status in (AnomalyStatus.resolved, AnomalyStatus.dismissed):
        anomaly.resolved_at = datetime.utcnow()
    db.add(anomaly)
    db.commit()
    db.refresh(anomaly)
    return anomaly


# -- Anomaly Rules -------------------------------------------------------


@router.get(
    "/anomaly-rules",
    response_model=list[AtAnomalyRuleOut],
    operation_id="at_listAnomalyRules",
)
def list_anomaly_rules(
    db: Annotated[Session, Depends(get_session)],
):
    return db.exec(select(AtAnomalyRule).order_by(AtAnomalyRule.name)).all()
