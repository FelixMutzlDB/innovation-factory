"""API router for energy readings endpoints."""
from fastapi import APIRouter, HTTPException, Query
from sqlmodel import select
from datetime import datetime, timedelta

from ....dependencies import SessionDep
from ..models import VhEnergyReading, VhEnergyReadingOut

router = APIRouter(prefix="/energy", tags=["vh-energy"])


@router.get("/households/{household_id}/readings", response_model=list[VhEnergyReadingOut], operation_id="vh_get_energy_readings")
def get_energy_readings(
    household_id: int,
    db: SessionDep,
    hours: int = Query(default=24, description="Number of hours of data to retrieve"),
):
    """Get energy readings for a household."""
    start_time = datetime.utcnow() - timedelta(hours=hours)

    statement = select(VhEnergyReading).where(
        VhEnergyReading.household_id == household_id,
        VhEnergyReading.timestamp >= start_time
    ).order_by(VhEnergyReading.timestamp.desc())  # type: ignore[unresolved-attribute]

    readings = db.exec(statement).all()

    return [
        VhEnergyReadingOut(
            id=r.id,  # type: ignore[invalid-argument-type]
            household_id=r.household_id, timestamp=r.timestamp,
            pv_generation_kwh=r.pv_generation_kwh, battery_charge_kwh=r.battery_charge_kwh,
            battery_discharge_kwh=r.battery_discharge_kwh, battery_level_kwh=r.battery_level_kwh,
            grid_import_kwh=r.grid_import_kwh, grid_export_kwh=r.grid_export_kwh,
            ev_consumption_kwh=r.ev_consumption_kwh, heat_pump_consumption_kwh=r.heat_pump_consumption_kwh,
            household_consumption_kwh=r.household_consumption_kwh, total_consumption_kwh=r.total_consumption_kwh,
        )
        for r in readings
    ]


@router.get("/households/{household_id}/current", response_model=VhEnergyReadingOut, operation_id="vh_get_current_reading")
def get_current_reading(household_id: int, db: SessionDep):
    """Get the most recent energy reading for a household."""
    statement = select(VhEnergyReading).where(
        VhEnergyReading.household_id == household_id
    ).order_by(VhEnergyReading.timestamp.desc()).limit(1)  # type: ignore[unresolved-attribute]

    reading = db.exec(statement).first()

    if not reading:
        raise HTTPException(status_code=404, detail="No readings found for this household")

    return VhEnergyReadingOut(
        id=reading.id,  # type: ignore[invalid-argument-type]
        household_id=reading.household_id, timestamp=reading.timestamp,
        pv_generation_kwh=reading.pv_generation_kwh, battery_charge_kwh=reading.battery_charge_kwh,
        battery_discharge_kwh=reading.battery_discharge_kwh, battery_level_kwh=reading.battery_level_kwh,
        grid_import_kwh=reading.grid_import_kwh, grid_export_kwh=reading.grid_export_kwh,
        ev_consumption_kwh=reading.ev_consumption_kwh, heat_pump_consumption_kwh=reading.heat_pump_consumption_kwh,
        household_consumption_kwh=reading.household_consumption_kwh, total_consumption_kwh=reading.total_consumption_kwh,
    )
