"""Inventory routes for AdTech Intelligence."""
from typing import Annotated, Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlmodel import Session, select

from ....dependencies import get_session
from ..models import (
    AtAdInventory,
    AtAdInventoryOut,
    InventoryStatus,
    InventoryType,
    LocationType,
)

router = APIRouter(tags=["adtech-inventory"])


@router.get(
    "/inventory",
    response_model=list[AtAdInventoryOut],
    operation_id="at_listInventory",
)
def list_inventory(
    db: Annotated[Session, Depends(get_session)],
    inventory_type: Optional[InventoryType] = None,
    location_type: Optional[LocationType] = None,
    status: Optional[InventoryStatus] = None,
    city: Optional[str] = None,
    limit: int = Query(default=50, le=500),
    offset: int = 0,
):
    """List ad inventory with optional filters."""
    stmt = select(AtAdInventory)
    if inventory_type:
        stmt = stmt.where(AtAdInventory.inventory_type == inventory_type)
    if location_type:
        stmt = stmt.where(AtAdInventory.location_type == location_type)
    if status:
        stmt = stmt.where(AtAdInventory.status == status)
    if city:
        stmt = stmt.where(AtAdInventory.city == city)
    stmt = stmt.order_by(AtAdInventory.created_at.desc()).offset(offset).limit(limit)
    return db.exec(stmt).all()


@router.get(
    "/inventory/{inventory_id}",
    response_model=AtAdInventoryOut,
    operation_id="at_getInventoryItem",
)
def get_inventory_item(
    inventory_id: int,
    db: Annotated[Session, Depends(get_session)],
):
    item = db.get(AtAdInventory, inventory_id)
    if not item:
        raise HTTPException(404, detail="Inventory item not found")
    return item
