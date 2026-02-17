"""Anomaly alert endpoints for the ASM Cockpit."""
from datetime import datetime, timezone
from typing import Optional

from fastapi import APIRouter, HTTPException, Query
from sqlmodel import select

from ....dependencies import SessionDep
from ..models import (
    MacAnomalyAlert,
    MacAnomalyAlertOut,
    MacAnomalyAlertUpdate,
    MacAlertStatus,
    MacAlertSeverity,
)

router = APIRouter(prefix="/anomalies", tags=["mac-anomalies"])


@router.get("", response_model=list[MacAnomalyAlertOut], operation_id="mac_listAnomalyAlerts")
def list_anomaly_alerts(
    session: SessionDep,
    station_id: Optional[int] = Query(None),
    status: Optional[str] = Query(None),
    severity: Optional[str] = Query(None),
    limit: int = Query(100, ge=1, le=500),
):
    """List anomaly alerts with filters."""
    q = select(MacAnomalyAlert)
    if station_id is not None:
        q = q.where(MacAnomalyAlert.station_id == station_id)
    if status:
        q = q.where(MacAnomalyAlert.status == status)
    if severity:
        q = q.where(MacAnomalyAlert.severity == severity)
    q = q.order_by(MacAnomalyAlert.detected_at.desc()).limit(limit)  # type: ignore[unresolved-attribute]
    return session.exec(q).all()


@router.get("/{alert_id}", response_model=MacAnomalyAlertOut, operation_id="mac_getAnomalyAlert")
def get_anomaly_alert(alert_id: int, session: SessionDep):
    """Get a single anomaly alert by ID."""
    alert = session.get(MacAnomalyAlert, alert_id)
    if not alert:
        raise HTTPException(status_code=404, detail="Alert not found")
    return alert


@router.patch("/{alert_id}", response_model=MacAnomalyAlertOut, operation_id="mac_updateAnomalyAlert")
def update_anomaly_alert(alert_id: int, update: MacAnomalyAlertUpdate, session: SessionDep):
    """Update an anomaly alert (e.g. acknowledge, resolve, dismiss)."""
    alert = session.get(MacAnomalyAlert, alert_id)
    if not alert:
        raise HTTPException(status_code=404, detail="Alert not found")
    if update.status is not None:
        alert.status = update.status
        if update.status in (MacAlertStatus.resolved, MacAlertStatus.dismissed):
            alert.resolved_at = datetime.now(timezone.utc)
    session.add(alert)
    session.commit()
    session.refresh(alert)
    return alert
