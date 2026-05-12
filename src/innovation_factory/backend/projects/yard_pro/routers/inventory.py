"""Consumables CRUD (UC5) for yard-pro.

URL prefix is ``/inventory`` per the operation_id contract — the data
model calls them ``yp_consumables`` but the user-facing concept is
"inventory" (oil, fertilizer, blades). Same RLS pattern as plants and
tools.
"""
from __future__ import annotations

from fastapi import APIRouter, HTTPException, Request
from sqlmodel import select

from ....dependencies import SessionDep
from ....input_sanitize import sanitize_text
from ..models import YpConsumable, YpConsumableCreate, YpConsumableOut
from .yards import get_caller_yard

router = APIRouter(tags=["yard-pro"])


def _safe(text: str) -> str:
    """Sanitize and coerce to ``str`` — see plants.py for the rationale."""
    cleaned = sanitize_text(text)
    return cleaned if isinstance(cleaned, str) else ""


def _to_out(c: YpConsumable) -> YpConsumableOut:
    return YpConsumableOut(
        id=c.id or 0,
        yard_id=c.yard_id,
        kind=c.kind,
        display_name=c.display_name,
        quantity=c.quantity,
        unit=c.unit,
        last_restock_at=c.last_restock_at,
    )


@router.get(
    "/inventory",
    response_model=list[YpConsumableOut],
    operation_id="yp_listConsumables",
)
def list_consumables(
    request: Request, db: SessionDep
) -> list[YpConsumableOut]:
    yard = get_caller_yard(request, db)
    rows = db.exec(
        select(YpConsumable)
        .where(YpConsumable.yard_id == yard.id)
        .order_by(YpConsumable.id)  # type: ignore[invalid-argument-type]
    ).all()
    return [_to_out(c) for c in rows]


@router.post(
    "/inventory",
    response_model=YpConsumableOut,
    operation_id="yp_createConsumable",
    status_code=201,
)
def create_consumable(
    request: Request, payload: YpConsumableCreate, db: SessionDep
) -> YpConsumableOut:
    yard = get_caller_yard(request, db)
    cons = YpConsumable(
        yard_id=yard.id or 0,
        kind=payload.kind,
        display_name=_safe(payload.display_name),
        quantity=payload.quantity,
        unit=_safe(payload.unit),
        last_restock_at=payload.last_restock_at,
    )
    db.add(cons)
    db.commit()
    db.refresh(cons)
    return _to_out(cons)


@router.patch(
    "/inventory/{consumable_id}",
    response_model=YpConsumableOut,
    operation_id="yp_updateConsumable",
)
def update_consumable(
    consumable_id: int,
    request: Request,
    payload: YpConsumableCreate,
    db: SessionDep,
) -> YpConsumableOut:
    yard = get_caller_yard(request, db)
    cons = db.get(YpConsumable, consumable_id)
    if cons is None or cons.yard_id != yard.id:
        raise HTTPException(status_code=404, detail="Consumable not found")
    cons.kind = payload.kind
    cons.display_name = _safe(payload.display_name)
    cons.quantity = payload.quantity
    cons.unit = _safe(payload.unit)
    cons.last_restock_at = payload.last_restock_at
    db.add(cons)
    db.commit()
    db.refresh(cons)
    return _to_out(cons)


@router.delete(
    "/inventory/{consumable_id}",
    response_model=dict[str, bool],
    operation_id="yp_deleteConsumable",
)
def delete_consumable(
    consumable_id: int, request: Request, db: SessionDep
) -> dict[str, bool]:
    yard = get_caller_yard(request, db)
    cons = db.get(YpConsumable, consumable_id)
    if cons is None or cons.yard_id != yard.id:
        raise HTTPException(status_code=404, detail="Consumable not found")
    db.delete(cons)
    db.commit()
    return {"ok": True}
