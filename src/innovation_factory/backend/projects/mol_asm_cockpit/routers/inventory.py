"""Inventory and supply endpoints for the ASM Cockpit."""
from datetime import date, timedelta
from typing import Optional

from fastapi import APIRouter, Query
from sqlmodel import select

from ....dependencies import SessionDep
from ..models import (
    MacInventory,
    MacInventoryOut,
    MacCompetitorPrice,
    MacCompetitorPriceOut,
    MacPriceHistory,
    MacPriceHistoryOut,
)

router = APIRouter(prefix="/inventory", tags=["mac-inventory"])


@router.get("", response_model=list[MacInventoryOut], operation_id="mac_listInventory")
def list_inventory(
    session: SessionDep,
    station_id: Optional[int] = Query(None),
    product_category: Optional[str] = Query(None),
    days: int = Query(7, ge=1, le=90),
    limit: int = Query(1000, ge=1, le=10000),
):
    """List inventory records with filters."""
    cutoff = date.today() - timedelta(days=days)
    q = select(MacInventory).where(MacInventory.record_date >= cutoff)
    if station_id is not None:
        q = q.where(MacInventory.station_id == station_id)
    if product_category:
        q = q.where(MacInventory.product_category == product_category)
    q = q.order_by(MacInventory.record_date.desc()).limit(limit)  # type: ignore[unresolved-attribute]
    return session.exec(q).all()


@router.get("/competitor-prices", response_model=list[MacCompetitorPriceOut], operation_id="mac_listCompetitorPrices")
def list_competitor_prices(
    session: SessionDep,
    station_id: Optional[int] = Query(None),
    days: int = Query(30, ge=1, le=365),
    limit: int = Query(500, ge=1, le=5000),
):
    """List competitor fuel prices."""
    cutoff = date.today() - timedelta(days=days)
    q = select(MacCompetitorPrice).where(MacCompetitorPrice.price_date >= cutoff)
    if station_id is not None:
        q = q.where(MacCompetitorPrice.station_id == station_id)
    q = q.order_by(MacCompetitorPrice.price_date.desc()).limit(limit)  # type: ignore[unresolved-attribute]
    return session.exec(q).all()


@router.get("/price-history", response_model=list[MacPriceHistoryOut], operation_id="mac_listPriceHistory")
def list_price_history(
    session: SessionDep,
    station_id: Optional[int] = Query(None),
    fuel_type: Optional[str] = Query(None),
    days: int = Query(30, ge=1, le=365),
    limit: int = Query(500, ge=1, le=5000),
):
    """List our price history."""
    cutoff = date.today() - timedelta(days=days)
    q = select(MacPriceHistory).where(MacPriceHistory.price_date >= cutoff)
    if station_id is not None:
        q = q.where(MacPriceHistory.station_id == station_id)
    if fuel_type:
        q = q.where(MacPriceHistory.fuel_type == fuel_type)
    q = q.order_by(MacPriceHistory.price_date.desc()).limit(limit)  # type: ignore[unresolved-attribute]
    return session.exec(q).all()
