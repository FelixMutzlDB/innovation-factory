"""API router for neighborhood endpoints."""
from fastapi import APIRouter, HTTPException
from sqlmodel import select
from datetime import datetime, timedelta

from ....dependencies import SessionDep
from ..models import (
    VhNeighborhood,
    VhHousehold,
    VhEnergyReading,
    VhEnergyDevice,
    DeviceType,
    VhNeighborhoodOut,
    VhNeighborhoodSummaryOut,
    VhHouseholdSummaryOut,
)

router = APIRouter(prefix="/neighborhoods", tags=["vh-neighborhoods"])


@router.get("", response_model=list[VhNeighborhoodOut], operation_id="vh_list_neighborhoods")
def list_neighborhoods(db: SessionDep):
    """List all neighborhoods."""
    statement = select(VhNeighborhood)
    neighborhoods = db.exec(statement).all()
    return list(neighborhoods)


@router.get("/{neighborhood_id}/summary", response_model=VhNeighborhoodSummaryOut, operation_id="vh_get_neighborhood_summary")
def get_neighborhood_summary(neighborhood_id: int, db: SessionDep):
    """Get comprehensive neighborhood summary with energy metrics."""
    neighborhood = db.get(VhNeighborhood, neighborhood_id)
    if not neighborhood:
        raise HTTPException(status_code=404, detail="Neighborhood not found")

    households_query = select(VhHousehold).where(VhHousehold.neighborhood_id == neighborhood_id)
    households = db.exec(households_query).all()

    one_day_ago = datetime.utcnow() - timedelta(hours=24)

    total_consumption = 0.0
    total_generation = 0.0
    total_storage_capacity = 0.0
    household_summaries = []

    for household in households:
        latest_reading_query = select(VhEnergyReading).where(
            VhEnergyReading.household_id == household.id
        ).order_by(VhEnergyReading.timestamp.desc()).limit(1)  # type: ignore[unresolved-attribute]
        latest_reading = db.exec(latest_reading_query).first()

        battery_query = select(VhEnergyDevice).where(
            VhEnergyDevice.household_id == household.id,
            VhEnergyDevice.device_type == DeviceType.battery
        )
        battery = db.exec(battery_query).first()
        battery_capacity = battery.capacity_kw if battery else 0.0

        if battery_capacity > 0:  # type: ignore[unsupported-operator]
            total_storage_capacity += battery_capacity  # type: ignore[unsupported-operator]

        readings_24h_query = select(VhEnergyReading).where(
            VhEnergyReading.household_id == household.id,
            VhEnergyReading.timestamp >= one_day_ago
        )
        readings_24h = db.exec(readings_24h_query).all()

        hh_consumption = sum(r.total_consumption_kwh for r in readings_24h)
        hh_generation = sum(r.pv_generation_kwh for r in readings_24h)

        total_consumption += hh_consumption
        total_generation += hh_generation

        current_consumption_kw = latest_reading.total_consumption_kwh if latest_reading else 0.0
        current_generation_kw = latest_reading.pv_generation_kwh if latest_reading else 0.0
        battery_level_percent = 0.0
        if latest_reading and battery_capacity > 0:  # type: ignore[unsupported-operator]
            battery_level_percent = (latest_reading.battery_level_kwh / battery_capacity) * 100  # type: ignore[unsupported-operator]

        household_summaries.append(VhHouseholdSummaryOut(
            id=household.id,  # type: ignore[invalid-argument-type]
            owner_name=household.owner_name,
            address=household.address,
            optimization_mode=household.optimization_mode,
            current_consumption_kw=round(current_consumption_kw, 2),
            current_generation_kw=round(current_generation_kw, 2),
            battery_level_percent=round(battery_level_percent, 1),
        ))

    return VhNeighborhoodSummaryOut(
        id=neighborhood.id,  # type: ignore[invalid-argument-type]
        name=neighborhood.name,
        location=neighborhood.location,
        total_households=neighborhood.total_households,
        total_consumption_kwh=round(total_consumption, 2),
        total_generation_kwh=round(total_generation, 2),
        total_storage_capacity_kwh=round(total_storage_capacity, 2),
        households=household_summaries,
    )
