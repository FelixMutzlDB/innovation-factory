"""Station endpoints for the ASM Cockpit."""
from typing import Optional

from fastapi import APIRouter, Query
from sqlmodel import col, func, select

from ....dependencies import SessionDep
from ..models import (
    MacAnomalyAlert,
    AlertStatus,
    MacFuelSale,
    MacNonfuelSale,
    MacRegion,
    MacStation,
    MacRegionOut,
    MacStationOut,
    MacStationKPI,
)

router = APIRouter(prefix="/stations", tags=["mac-stations"])


@router.get("/regions", response_model=list[MacRegionOut], operation_id="mac_listRegions")
def list_regions(session: SessionDep):
    """List all regions."""
    return session.exec(select(MacRegion).order_by(MacRegion.name)).all()


@router.get("", response_model=list[MacStationOut], operation_id="mac_listStations")
def list_stations(
    session: SessionDep,
    region_id: Optional[int] = Query(None),
    station_type: Optional[str] = Query(None),
):
    """List stations with optional filters."""
    q = select(MacStation)
    if region_id is not None:
        q = q.where(MacStation.region_id == region_id)
    if station_type:
        q = q.where(MacStation.station_type == station_type)
    return session.exec(q.order_by(MacStation.station_code)).all()


@router.get("/kpis", response_model=list[MacStationKPI], operation_id="mac_stationKPIs")
def station_kpis(
    session: SessionDep,
    days: int = Query(30, ge=1, le=365),
):
    """Get aggregated KPIs for all stations over the last N days."""
    from datetime import date, timedelta

    cutoff = date.today() - timedelta(days=days)

    # Sub-queries for fuel and non-fuel aggregates
    fuel_sub = (
        select(
            MacFuelSale.station_id,
            func.sum(MacFuelSale.volume_liters).label("total_fuel_volume"),
            func.sum(MacFuelSale.revenue).label("total_fuel_revenue"),
            func.sum(MacFuelSale.margin).label("total_fuel_margin"),
        )
        .where(MacFuelSale.sale_date >= cutoff)
        .group_by(MacFuelSale.station_id)
        .subquery()
    )

    nonfuel_sub = (
        select(
            MacNonfuelSale.station_id,
            func.sum(MacNonfuelSale.revenue).label("total_nonfuel_revenue"),
            func.sum(MacNonfuelSale.margin).label("total_nonfuel_margin"),
        )
        .where(MacNonfuelSale.sale_date >= cutoff)
        .group_by(MacNonfuelSale.station_id)
        .subquery()
    )

    alert_sub = (
        select(
            MacAnomalyAlert.station_id,
            func.count(MacAnomalyAlert.id).label("active_alerts"),
        )
        .where(MacAnomalyAlert.status == AlertStatus.active)
        .group_by(MacAnomalyAlert.station_id)
        .subquery()
    )

    q = (
        select(
            MacStation.id,
            MacStation.station_code,
            MacStation.name,
            MacStation.city,
            MacRegion.name.label("region_name"),  # type: ignore[unresolved-attribute]
            fuel_sub.c.total_fuel_volume,
            fuel_sub.c.total_fuel_revenue,
            fuel_sub.c.total_fuel_margin,
            nonfuel_sub.c.total_nonfuel_revenue,
            nonfuel_sub.c.total_nonfuel_margin,
            alert_sub.c.active_alerts,
        )  # type: ignore[no-matching-overload]
        .join(MacRegion, MacStation.region_id == MacRegion.id)
        .outerjoin(fuel_sub, MacStation.id == fuel_sub.c.station_id)
        .outerjoin(nonfuel_sub, MacStation.id == nonfuel_sub.c.station_id)
        .outerjoin(alert_sub, MacStation.id == alert_sub.c.station_id)
        .order_by(col(MacStation.station_code))
    )

    rows = session.exec(q).all()
    return [
        MacStationKPI(
            station_id=r[0],
            station_code=r[1],
            station_name=r[2],
            city=r[3],
            region_name=r[4],
            total_fuel_volume=r[5] or 0,
            total_fuel_revenue=r[6] or 0,
            total_fuel_margin=r[7] or 0,
            total_nonfuel_revenue=r[8] or 0,
            total_nonfuel_margin=r[9] or 0,
            active_alerts=r[10] or 0,
        )
        for r in rows
    ]


@router.get("/{station_id}", response_model=MacStationOut, operation_id="mac_getStation")
def get_station(station_id: int, session: SessionDep):
    """Get a single station by ID."""
    station = session.get(MacStation, station_id)
    if not station:
        from fastapi import HTTPException
        raise HTTPException(status_code=404, detail="Station not found")
    return station
