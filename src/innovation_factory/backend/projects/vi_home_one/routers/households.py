"""API router for household endpoints."""
from fastapi import APIRouter, HTTPException
from sqlmodel import select
from datetime import datetime, timedelta, timezone

from ....dependencies import SessionDep
from ..models import (
    VhHousehold,
    VhEnergyDevice,
    VhEnergyReading,
    ConsumptionCategory,
    VhHouseholdOut,
    VhHouseholdCockpitOut,
    VhEnergyReadingOut,
    VhConsumptionBreakdownOut,
    VhEnergySourcesOut,
    VhEnergyDeviceOut,
    VhOptimizationModeUpdate,
)

router = APIRouter(prefix="/households", tags=["vh-households"])


@router.get("/{household_id}", response_model=VhHouseholdOut, operation_id="vh_get_household")
def get_household(household_id: int, db: SessionDep):
    """Get household details."""
    household = db.get(VhHousehold, household_id)
    if not household:
        raise HTTPException(status_code=404, detail="Household not found")
    return household


@router.put("/{household_id}/optimization-mode", response_model=VhHouseholdOut, operation_id="vh_update_optimization_mode")
def update_optimization_mode(household_id: int, mode_update: VhOptimizationModeUpdate, db: SessionDep):
    """Update household optimization mode."""
    household = db.get(VhHousehold, household_id)
    if not household:
        raise HTTPException(status_code=404, detail="Household not found")

    household.optimization_mode = mode_update.optimization_mode
    household.updated_at = datetime.now(timezone.utc)

    db.add(household)
    db.commit()
    db.refresh(household)

    return household


@router.get("/{household_id}/cockpit", response_model=VhHouseholdCockpitOut, operation_id="vh_get_household_cockpit")
def get_household_cockpit(household_id: int, db: SessionDep):
    """Get comprehensive household energy cockpit data."""
    household = db.get(VhHousehold, household_id)
    if not household:
        raise HTTPException(status_code=404, detail="Household not found")

    latest_reading_query = select(VhEnergyReading).where(
        VhEnergyReading.household_id == household_id
    ).order_by(VhEnergyReading.timestamp.desc()).limit(1)  # type: ignore[unresolved-attribute]
    latest_reading = db.exec(latest_reading_query).first()

    current_consumption_kw = latest_reading.total_consumption_kwh if latest_reading else 0.0

    consumption_breakdown = []
    if latest_reading:
        total = latest_reading.total_consumption_kwh
        if total > 0:
            categories = [
                (ConsumptionCategory.climate_control, latest_reading.heat_pump_consumption_kwh),
                (ConsumptionCategory.ev_charging, latest_reading.ev_consumption_kwh),
                (ConsumptionCategory.household_appliances, latest_reading.household_consumption_kwh),
            ]
            for category, value_kwh in categories:
                if value_kwh > 0:
                    percentage = (value_kwh / total) * 100
                    consumption_breakdown.append(VhConsumptionBreakdownOut(
                        category=category,
                        value_kwh=round(value_kwh, 3),
                        percentage=round(percentage, 1),
                    ))

    energy_sources = VhEnergySourcesOut(
        pv_generation_kw=latest_reading.pv_generation_kwh if latest_reading else 0.0,
        battery_discharge_kw=latest_reading.battery_discharge_kwh if latest_reading else 0.0,
        grid_import_kw=latest_reading.grid_import_kwh if latest_reading else 0.0,
        total_available_kw=0.0,
    )
    energy_sources.total_available_kw = (
        energy_sources.pv_generation_kw +
        energy_sources.battery_discharge_kw +
        energy_sources.grid_import_kw
    )

    one_day_ago = datetime.now(timezone.utc) - timedelta(hours=24)
    recent_readings_query = select(VhEnergyReading).where(
        VhEnergyReading.household_id == household_id,
        VhEnergyReading.timestamp >= one_day_ago
    ).order_by(VhEnergyReading.timestamp.desc()).limit(24)  # type: ignore[unresolved-attribute]
    recent_readings_raw = db.exec(recent_readings_query).all()

    recent_readings = [
        VhEnergyReadingOut(
            id=r.id,  # type: ignore[invalid-argument-type]
            household_id=r.household_id, timestamp=r.timestamp,
            pv_generation_kwh=r.pv_generation_kwh, battery_charge_kwh=r.battery_charge_kwh,
            battery_discharge_kwh=r.battery_discharge_kwh, battery_level_kwh=r.battery_level_kwh,
            grid_import_kwh=r.grid_import_kwh, grid_export_kwh=r.grid_export_kwh,
            ev_consumption_kwh=r.ev_consumption_kwh, heat_pump_consumption_kwh=r.heat_pump_consumption_kwh,
            household_consumption_kwh=r.household_consumption_kwh, total_consumption_kwh=r.total_consumption_kwh,
        )
        for r in recent_readings_raw
    ]

    # Calculate costs
    cost_today = 0.0
    cost_this_month = 0.0

    today_start = datetime.now(timezone.utc).replace(hour=0, minute=0, second=0, microsecond=0)
    today_readings = db.exec(select(VhEnergyReading).where(
        VhEnergyReading.household_id == household_id,
        VhEnergyReading.timestamp >= today_start
    )).all()

    for reading in today_readings:
        cost_today += reading.grid_import_kwh * 0.32
        cost_today -= reading.grid_export_kwh * 0.082

    month_start = datetime.now(timezone.utc).replace(day=1, hour=0, minute=0, second=0, microsecond=0)
    month_readings = db.exec(select(VhEnergyReading).where(
        VhEnergyReading.household_id == household_id,
        VhEnergyReading.timestamp >= month_start
    )).all()

    for reading in month_readings:
        cost_this_month += reading.grid_import_kwh * 0.32
        cost_this_month -= reading.grid_export_kwh * 0.082

    devices_query = select(VhEnergyDevice).where(VhEnergyDevice.household_id == household_id)
    devices_raw = db.exec(devices_query).all()

    devices = [
        VhEnergyDeviceOut(
            id=d.id,  # type: ignore[invalid-argument-type]
            household_id=d.household_id, device_type=d.device_type,
            brand=d.brand, model=d.model, capacity_kw=d.capacity_kw,
            installation_date=d.installation_date, last_maintenance_date=d.last_maintenance_date,
            next_maintenance_date=d.next_maintenance_date, serial_number=d.serial_number,
            specifications=d.specifications,
        )
        for d in devices_raw
    ]

    return VhHouseholdCockpitOut(
        household=VhHouseholdOut(
            id=household.id,  # type: ignore[invalid-argument-type]
            neighborhood_id=household.neighborhood_id,
            owner_name=household.owner_name, address=household.address,
            optimization_mode=household.optimization_mode,
            has_pv=household.has_pv, has_battery=household.has_battery,
            has_ev=household.has_ev, has_heat_pump=household.has_heat_pump,
            created_at=household.created_at, updated_at=household.updated_at,
        ),
        current_consumption_kw=round(current_consumption_kw, 2),
        consumption_breakdown=consumption_breakdown,
        energy_sources=energy_sources,
        recent_readings=recent_readings,
        cost_today_eur=round(cost_today, 2),
        cost_this_month_eur=round(cost_this_month, 2),
        devices=devices,
    )
