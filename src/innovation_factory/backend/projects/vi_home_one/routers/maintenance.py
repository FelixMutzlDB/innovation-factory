"""API router for maintenance alerts."""
from datetime import datetime
from fastapi import APIRouter, HTTPException
from sqlmodel import select

from ....dependencies import SessionDep
from ..models import (
    VhMaintenanceAlert,
    VhEnergyDevice,
    DeviceType,
    VhMaintenanceAlertOut,
    VhMaintenanceAlertAcknowledge,
)

router = APIRouter(prefix="/maintenance", tags=["vh-maintenance"])


@router.get("/households/{household_id}/alerts", response_model=list[VhMaintenanceAlertOut], operation_id="vh_list_maintenance_alerts")
def list_maintenance_alerts(household_id: int, db: SessionDep, include_acknowledged: bool = False):
    """List maintenance alerts for a household's devices."""
    devices_query = select(VhEnergyDevice).where(VhEnergyDevice.household_id == household_id)
    devices = db.exec(devices_query).all()
    device_ids = [d.id for d in devices]

    if not device_ids:
        return []

    query = select(VhMaintenanceAlert).where(VhMaintenanceAlert.device_id.in_(device_ids))  # type: ignore[unresolved-attribute]

    if not include_acknowledged:
        query = query.where(VhMaintenanceAlert.is_acknowledged == False)

    query = query.order_by(VhMaintenanceAlert.severity.desc(), VhMaintenanceAlert.created_at.desc())  # type: ignore[unresolved-attribute]
    alerts = db.exec(query).all()

    result = []
    for alert in alerts:
        device = db.get(VhEnergyDevice, alert.device_id)
        if device:
            result.append(VhMaintenanceAlertOut(
                id=alert.id, device_id=alert.device_id,  # type: ignore[invalid-argument-type]
                device_type=device.device_type, device_model=device.model,
                alert_type=alert.alert_type, severity=alert.severity,
                message=alert.message, predicted_date=alert.predicted_date,
                is_acknowledged=alert.is_acknowledged, created_at=alert.created_at,
            ))
    return result


@router.post("/alerts/{alert_id}/acknowledge", response_model=VhMaintenanceAlertOut, operation_id="vh_acknowledge_alert")
def acknowledge_alert(alert_id: int, acknowledge: VhMaintenanceAlertAcknowledge, db: SessionDep):
    """Acknowledge or unacknowledge a maintenance alert."""
    alert = db.get(VhMaintenanceAlert, alert_id)
    if not alert:
        raise HTTPException(status_code=404, detail="Alert not found")

    alert.is_acknowledged = acknowledge.is_acknowledged
    if acknowledge.is_acknowledged:
        alert.acknowledged_at = datetime.utcnow()
    else:
        alert.acknowledged_at = None

    db.add(alert)
    db.commit()
    db.refresh(alert)

    device = db.get(VhEnergyDevice, alert.device_id)
    return VhMaintenanceAlertOut(
        id=alert.id, device_id=alert.device_id,  # type: ignore[invalid-argument-type]
        device_type=device.device_type if device else DeviceType.heat_pump,
        device_model=device.model if device else "Unknown",
        alert_type=alert.alert_type, severity=alert.severity,
        message=alert.message, predicted_date=alert.predicted_date,
        is_acknowledged=alert.is_acknowledged, created_at=alert.created_at,
    )
