"""API router for energy provider comparison."""
from fastapi import APIRouter, HTTPException, Query
from sqlmodel import select
from datetime import datetime, timedelta, timezone

from ....dependencies import SessionDep
from ..models import (
    VhHousehold,
    VhEnergyProvider,
    VhEnergyReading,
    VhEnergyProviderOut,
    VhProviderComparisonOut,
    VhAlternativeProviderOut,
)

router = APIRouter(prefix="/providers", tags=["vh-providers"])


@router.get("", response_model=list[VhEnergyProviderOut], operation_id="vh_list_providers")
def list_providers(db: SessionDep):
    """List all energy providers."""
    statement = select(VhEnergyProvider)
    providers = db.exec(statement).all()
    return list(providers)


@router.get("/compare", response_model=VhProviderComparisonOut, operation_id="vh_compare_providers")
def compare_providers(
    db: SessionDep,
    household_id: int = Query(..., description="Household ID to calculate costs for"),
    current_provider_id: int = Query(default=1, description="Current provider ID (default: E.ON)"),
):
    """Compare energy providers based on household consumption patterns."""
    household = db.get(VhHousehold, household_id)
    if not household:
        raise HTTPException(status_code=404, detail="Household not found")

    current_provider = db.get(VhEnergyProvider, current_provider_id)
    if not current_provider:
        raise HTTPException(status_code=404, detail="Current provider not found")

    thirty_days_ago = datetime.now(timezone.utc) - timedelta(days=30)
    readings_query = select(VhEnergyReading).where(
        VhEnergyReading.household_id == household_id,
        VhEnergyReading.timestamp >= thirty_days_ago
    )
    readings = db.exec(readings_query).all()

    if not readings:
        raise HTTPException(status_code=404, detail="No readings found for this household")

    current_monthly_cost = _calculate_monthly_cost(readings, current_provider)  # type: ignore[invalid-argument-type]

    all_providers = db.exec(select(VhEnergyProvider)).all()

    alternative_providers = []
    for provider in all_providers:
        if provider.id == current_provider_id:
            continue
        monthly_cost = _calculate_monthly_cost(readings, provider)  # type: ignore[invalid-argument-type]
        savings = current_monthly_cost - monthly_cost
        savings_percent = (savings / current_monthly_cost * 100) if current_monthly_cost > 0 else 0

        alternative_providers.append(VhAlternativeProviderOut(
            provider=VhEnergyProviderOut(
                id=provider.id,  # type: ignore[invalid-argument-type]
                name=provider.name, base_rate_eur=provider.base_rate_eur,
                kwh_rate_eur=provider.kwh_rate_eur, night_rate_eur=provider.night_rate_eur,
                feed_in_rate_eur=provider.feed_in_rate_eur,
            ),
            estimated_monthly_cost_eur=round(monthly_cost, 2),
            potential_savings_eur=round(savings, 2),
            potential_savings_percent=round(savings_percent, 1),
        ))

    alternative_providers.sort(key=lambda x: x.potential_savings_eur, reverse=True)

    return VhProviderComparisonOut(
        current_provider=VhEnergyProviderOut(
            id=current_provider.id,  # type: ignore[invalid-argument-type]
            name=current_provider.name,
            base_rate_eur=current_provider.base_rate_eur, kwh_rate_eur=current_provider.kwh_rate_eur,
            night_rate_eur=current_provider.night_rate_eur, feed_in_rate_eur=current_provider.feed_in_rate_eur,
        ),
        current_monthly_cost_eur=round(current_monthly_cost, 2),
        alternative_providers=alternative_providers,
    )


def _calculate_monthly_cost(readings: list[VhEnergyReading], provider: VhEnergyProvider) -> float:
    """Calculate monthly cost for a provider based on readings."""
    total_cost = provider.base_rate_eur
    for reading in readings:
        hour = reading.timestamp.hour
        is_night = False
        if provider.night_rate_eur:
            if provider.night_start_hour >= provider.night_end_hour:
                is_night = hour >= provider.night_start_hour or hour < provider.night_end_hour
            else:
                is_night = provider.night_start_hour <= hour < provider.night_end_hour

        if is_night and provider.night_rate_eur:
            total_cost += reading.grid_import_kwh * provider.night_rate_eur
        else:
            total_cost += reading.grid_import_kwh * provider.kwh_rate_eur

        total_cost -= reading.grid_export_kwh * provider.feed_in_rate_eur
    return total_cost
