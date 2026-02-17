"""Sales endpoints for the ASM Cockpit (fuel and non-fuel)."""
from datetime import date, timedelta
from typing import Optional

from fastapi import APIRouter, Query
from sqlmodel import select

from ....dependencies import SessionDep
from ..models import (
    MacFuelSale,
    MacFuelSaleOut,
    MacNonfuelSale,
    MacNonfuelSaleOut,
    MacLoyaltyMetric,
    MacLoyaltyMetricOut,
)

router = APIRouter(prefix="/sales", tags=["mac-sales"])


@router.get("/fuel", response_model=list[MacFuelSaleOut], operation_id="mac_listFuelSales")
def list_fuel_sales(
    session: SessionDep,
    station_id: Optional[int] = Query(None),
    fuel_type: Optional[str] = Query(None),
    days: int = Query(30, ge=1, le=365),
    limit: int = Query(1000, ge=1, le=10000),
):
    """List fuel sales records with filters."""
    cutoff = date.today() - timedelta(days=days)
    q = select(MacFuelSale).where(MacFuelSale.sale_date >= cutoff)
    if station_id is not None:
        q = q.where(MacFuelSale.station_id == station_id)
    if fuel_type:
        q = q.where(MacFuelSale.fuel_type == fuel_type)
    q = q.order_by(MacFuelSale.sale_date.desc()).limit(limit)  # type: ignore[unresolved-attribute]
    return session.exec(q).all()


@router.get("/nonfuel", response_model=list[MacNonfuelSaleOut], operation_id="mac_listNonfuelSales")
def list_nonfuel_sales(
    session: SessionDep,
    station_id: Optional[int] = Query(None),
    category: Optional[str] = Query(None),
    days: int = Query(30, ge=1, le=365),
    limit: int = Query(1000, ge=1, le=10000),
):
    """List non-fuel sales records with filters."""
    cutoff = date.today() - timedelta(days=days)
    q = select(MacNonfuelSale).where(MacNonfuelSale.sale_date >= cutoff)
    if station_id is not None:
        q = q.where(MacNonfuelSale.station_id == station_id)
    if category:
        q = q.where(MacNonfuelSale.category == category)
    q = q.order_by(MacNonfuelSale.sale_date.desc()).limit(limit)  # type: ignore[unresolved-attribute]
    return session.exec(q).all()


@router.get("/loyalty", response_model=list[MacLoyaltyMetricOut], operation_id="mac_listLoyaltyMetrics")
def list_loyalty_metrics(
    session: SessionDep,
    station_id: Optional[int] = Query(None),
    limit: int = Query(100, ge=1, le=1000),
):
    """List loyalty metrics (monthly)."""
    q = select(MacLoyaltyMetric)
    if station_id is not None:
        q = q.where(MacLoyaltyMetric.station_id == station_id)
    q = q.order_by(MacLoyaltyMetric.month.desc()).limit(limit)  # type: ignore[unresolved-attribute]
    return session.exec(q).all()
