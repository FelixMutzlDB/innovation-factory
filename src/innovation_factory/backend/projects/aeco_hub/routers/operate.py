"""Operate-phase endpoints: sensors, maintenance, energy, utilization, leases.

IoT sensor *readings* live in Unity Catalog (Phase 3) — only sensor *devices*
(the registry) are stored in Lakebase. Energy is pre-aggregated daily so the
dashboard can render fast trends without scanning the raw sensor table.
"""
from collections import defaultdict
from typing import Optional

from fastapi import APIRouter, HTTPException, Query
from sqlmodel import func, select

from ....dependencies import SessionDep
from ..models import (
    AecoLeaseStatus,
    AecoMaintenancePriority,
    AecoMaintenanceStatus,
    AecoSensorType,
    DtBuilding,
    DtEnergyConsumption,
    DtEnergyConsumptionOut,
    DtEnergyDailyPointOut,
    DtFloor,
    DtLeaseContract,
    DtLeaseContractOut,
    DtMaintenanceOrder,
    DtMaintenanceOrderOut,
    DtMaintenanceStatsOut,
    DtProject,
    DtSensorDevice,
    DtSensorDeviceOut,
    DtSpace,
    DtSpaceUtilization,
    DtSpaceUtilizationOut,
)

router = APIRouter(tags=["aeco-hub"])


# -- Sensors ----------------------------------------------------------


@router.get(
    "/projects/{project_id}/operate/sensors",
    response_model=list[DtSensorDeviceOut],
    operation_id="aeco_listSensors",
)
def list_sensors(
    project_id: int,
    db: SessionDep,
    sensor_type: Optional[AecoSensorType] = None,
    building_id: Optional[int] = None,
    limit: int = Query(default=100, ge=1, le=500),
    offset: int = Query(default=0, ge=0),
):
    if not db.get(DtProject, project_id):
        raise HTTPException(404, detail="Project not found")
    stmt = (
        select(DtSensorDevice)
        .join(DtBuilding, DtSensorDevice.building_id == DtBuilding.id)  # type: ignore[invalid-argument-type]
        .where(DtBuilding.project_id == project_id)
    )
    if sensor_type:
        stmt = stmt.where(DtSensorDevice.sensor_type == sensor_type)
    if building_id is not None:
        stmt = stmt.where(DtSensorDevice.building_id == building_id)
    stmt = stmt.order_by(DtSensorDevice.sensor_code).offset(offset).limit(limit)
    return db.exec(stmt).all()


@router.get(
    "/sensors/{sensor_id}",
    response_model=DtSensorDeviceOut,
    operation_id="aeco_getSensor",
)
def get_sensor(sensor_id: int, db: SessionDep):
    sensor = db.get(DtSensorDevice, sensor_id)
    if not sensor:
        raise HTTPException(404, detail="Sensor not found")
    return sensor


# -- Maintenance ------------------------------------------------------


@router.get(
    "/projects/{project_id}/operate/maintenance",
    response_model=list[DtMaintenanceOrderOut],
    operation_id="aeco_listMaintenanceOrders",
)
def list_maintenance_orders(
    project_id: int,
    db: SessionDep,
    status: Optional[AecoMaintenanceStatus] = None,
    priority: Optional[AecoMaintenancePriority] = None,
    limit: int = Query(default=50, ge=1, le=200),
    offset: int = Query(default=0, ge=0),
):
    if not db.get(DtProject, project_id):
        raise HTTPException(404, detail="Project not found")
    stmt = (
        select(DtMaintenanceOrder)
        .join(DtBuilding, DtMaintenanceOrder.building_id == DtBuilding.id)  # type: ignore[invalid-argument-type]
        .where(DtBuilding.project_id == project_id)
    )
    if status:
        stmt = stmt.where(DtMaintenanceOrder.status == status)
    if priority:
        stmt = stmt.where(DtMaintenanceOrder.priority == priority)
    stmt = stmt.order_by(DtMaintenanceOrder.created_at.desc()).offset(offset).limit(limit)  # type: ignore[unresolved-attribute]
    return db.exec(stmt).all()


@router.get(
    "/projects/{project_id}/operate/maintenance/stats",
    response_model=DtMaintenanceStatsOut,
    operation_id="aeco_getMaintenanceStats",
)
def get_maintenance_stats(project_id: int, db: SessionDep) -> DtMaintenanceStatsOut:
    if not db.get(DtProject, project_id):
        raise HTTPException(404, detail="Project not found")
    base = (
        select(DtMaintenanceOrder)
        .join(DtBuilding, DtMaintenanceOrder.building_id == DtBuilding.id)  # type: ignore[invalid-argument-type]
        .where(DtBuilding.project_id == project_id)
    )
    orders = list(db.exec(base).all())
    total = len(orders)
    open_count = sum(1 for o in orders if o.status == AecoMaintenanceStatus.open)
    in_progress = sum(1 for o in orders if o.status == AecoMaintenanceStatus.in_progress)
    completed = sum(1 for o in orders if o.status == AecoMaintenanceStatus.completed)
    from datetime import date as _date
    overdue = sum(
        1 for o in orders
        if o.due_date and o.due_date < _date.today() and o.status != AecoMaintenanceStatus.completed
    )
    completed_with_dates = [o for o in orders if o.status == AecoMaintenanceStatus.completed and o.completed_at]
    avg_days = 0.0
    if completed_with_dates:
        deltas = [(o.completed_at - o.created_at).total_seconds() / 86400.0 for o in completed_with_dates if o.completed_at]
        if deltas:
            avg_days = round(sum(deltas) / len(deltas), 1)
    return DtMaintenanceStatsOut(
        project_id=project_id,
        total=total,
        open=open_count,
        in_progress=in_progress,
        completed=completed,
        overdue=overdue,
        avg_days_to_complete=avg_days,
    )


# -- Energy -----------------------------------------------------------


@router.get(
    "/projects/{project_id}/operate/energy",
    response_model=list[DtEnergyConsumptionOut],
    operation_id="aeco_listEnergyConsumption",
)
def list_energy_consumption(
    project_id: int,
    db: SessionDep,
    building_id: Optional[int] = None,
    limit: int = Query(default=100, ge=1, le=500),
    offset: int = Query(default=0, ge=0),
):
    if not db.get(DtProject, project_id):
        raise HTTPException(404, detail="Project not found")
    stmt = (
        select(DtEnergyConsumption)
        .join(DtBuilding, DtEnergyConsumption.building_id == DtBuilding.id)  # type: ignore[invalid-argument-type]
        .where(DtBuilding.project_id == project_id)
    )
    if building_id is not None:
        stmt = stmt.where(DtEnergyConsumption.building_id == building_id)
    stmt = stmt.order_by(DtEnergyConsumption.period_start.desc()).offset(offset).limit(limit)  # type: ignore[unresolved-attribute]
    return db.exec(stmt).all()


@router.get(
    "/projects/{project_id}/operate/energy/trend",
    response_model=list[DtEnergyDailyPointOut],
    operation_id="aeco_getEnergyTrend",
)
def get_energy_trend(project_id: int, db: SessionDep) -> list[DtEnergyDailyPointOut]:
    """Project-wide daily energy trend (sum across all buildings)."""
    if not db.get(DtProject, project_id):
        raise HTTPException(404, detail="Project not found")
    rows = list(
        db.exec(
            select(DtEnergyConsumption)
            .join(DtBuilding, DtEnergyConsumption.building_id == DtBuilding.id)  # type: ignore[invalid-argument-type]
            .where(DtBuilding.project_id == project_id)
        ).all()
    )
    daily: dict[str, dict[str, float]] = defaultdict(lambda: {"kwh": 0.0, "cost": 0.0, "ts": 0.0})
    for row in rows:
        key = row.period_start.date().isoformat()
        daily[key]["kwh"] += row.kwh
        daily[key]["cost"] += row.cost_eur
        daily[key]["ts"] = row.period_start.timestamp()
    points = sorted(daily.items(), key=lambda kv: kv[0])
    from datetime import datetime as _dt, timezone as _tz
    return [
        DtEnergyDailyPointOut(
            period_start=_dt.fromtimestamp(v["ts"], tz=_tz.utc),
            kwh=round(v["kwh"], 1),
            cost_eur=round(v["cost"], 2),
        )
        for _, v in points
    ]


# -- Space utilization -----------------------------------------------


@router.get(
    "/projects/{project_id}/operate/utilization",
    response_model=list[DtSpaceUtilizationOut],
    operation_id="aeco_listSpaceUtilization",
)
def list_space_utilization(
    project_id: int,
    db: SessionDep,
    limit: int = Query(default=100, ge=1, le=500),
    offset: int = Query(default=0, ge=0),
):
    if not db.get(DtProject, project_id):
        raise HTTPException(404, detail="Project not found")
    stmt = (
        select(DtSpaceUtilization)
        .join(DtSpace, DtSpaceUtilization.space_id == DtSpace.id)  # type: ignore[invalid-argument-type]
        .join(DtFloor, DtSpace.floor_id == DtFloor.id)  # type: ignore[invalid-argument-type]
        .join(DtBuilding, DtFloor.building_id == DtBuilding.id)  # type: ignore[invalid-argument-type]
        .where(DtBuilding.project_id == project_id)
        .order_by(DtSpaceUtilization.period_start.desc())  # type: ignore[unresolved-attribute]
        .offset(offset)
        .limit(limit)
    )
    return db.exec(stmt).all()


# -- Leases -----------------------------------------------------------


@router.get(
    "/projects/{project_id}/operate/leases",
    response_model=list[DtLeaseContractOut],
    operation_id="aeco_listLeaseContracts",
)
def list_lease_contracts(
    project_id: int,
    db: SessionDep,
    status: Optional[AecoLeaseStatus] = None,
    limit: int = Query(default=50, ge=1, le=200),
    offset: int = Query(default=0, ge=0),
):
    if not db.get(DtProject, project_id):
        raise HTTPException(404, detail="Project not found")
    stmt = (
        select(DtLeaseContract)
        .join(DtSpace, DtLeaseContract.space_id == DtSpace.id)  # type: ignore[invalid-argument-type]
        .join(DtFloor, DtSpace.floor_id == DtFloor.id)  # type: ignore[invalid-argument-type]
        .join(DtBuilding, DtFloor.building_id == DtBuilding.id)  # type: ignore[invalid-argument-type]
        .where(DtBuilding.project_id == project_id)
    )
    if status:
        stmt = stmt.where(DtLeaseContract.status == status)
    stmt = stmt.order_by(DtLeaseContract.start_date.desc()).offset(offset).limit(limit)  # type: ignore[unresolved-attribute]
    return db.exec(stmt).all()
