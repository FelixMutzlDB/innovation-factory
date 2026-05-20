"""Plant CRUD for yard-pro.

Every read/write filters by the caller's yard (RLS by ``user_key`` →
``yard_id``). A path that includes a plant_id verifies the plant belongs
to the caller's yard before mutating; cross-household access returns 404
to avoid leaking that the plant ID is valid for *somebody*.
"""
from __future__ import annotations

from fastapi import APIRouter, HTTPException, Request
from sqlmodel import select

from ....dependencies import SessionDep
from ....input_sanitize import sanitize_text
from ..models import YpPlant, YpPlantCreate, YpPlantOut
from .yards import get_caller_yard

router = APIRouter(tags=["yard-pro"])


def _safe(text: str) -> str:
    """Run the shared sanitizer and force a ``str`` return type.

    ``sanitize_text`` is typed ``(object) -> object`` so it can no-op on
    non-str input; the router only ever passes strings in, so we wrap
    the result to keep the SQLModel assignments well-typed.
    """
    cleaned = sanitize_text(text)
    return cleaned if isinstance(cleaned, str) else ""


def _to_out(p: YpPlant) -> YpPlantOut:
    return YpPlantOut(
        id=p.id or 0,
        yard_id=p.yard_id,
        species=p.species,
        variety=p.variety,
        planted_at=p.planted_at,
        notes=p.notes,
    )


@router.get(
    "/plants",
    response_model=list[YpPlantOut],
    operation_id="yp_listPlants",
)
def list_plants(request: Request, db: SessionDep) -> list[YpPlantOut]:
    """List the caller's plants (filtered by RLS-derived yard_id)."""
    yard = get_caller_yard(request, db)
    rows = db.exec(
        select(YpPlant).where(YpPlant.yard_id == yard.id).order_by(YpPlant.id)  # type: ignore[invalid-argument-type]
    ).all()
    return [_to_out(p) for p in rows]


@router.post(
    "/plants",
    response_model=YpPlantOut,
    operation_id="yp_createPlant",
    status_code=201,
)
def create_plant(
    request: Request, payload: YpPlantCreate, db: SessionDep
) -> YpPlantOut:
    """Create a plant in the caller's yard. The ``yard_id`` is taken from
    the caller's resolved yard — any client-supplied yard_id in the body
    would be ignored (the model has no such field), closing the RT-016
    "body override" attack vector."""
    yard = get_caller_yard(request, db)
    plant = YpPlant(
        yard_id=yard.id or 0,
        species=_safe(payload.species),
        variety=_safe(payload.variety),
        planted_at=payload.planted_at,
        notes=_safe(payload.notes),
    )
    db.add(plant)
    db.commit()
    db.refresh(plant)
    return _to_out(plant)


@router.patch(
    "/plants/{plant_id}",
    response_model=YpPlantOut,
    operation_id="yp_updatePlant",
)
def update_plant(
    plant_id: int, request: Request, payload: YpPlantCreate, db: SessionDep
) -> YpPlantOut:
    yard = get_caller_yard(request, db)
    plant = db.get(YpPlant, plant_id)
    if plant is None or plant.yard_id != yard.id:
        raise HTTPException(status_code=404, detail="Plant not found")
    plant.species = _safe(payload.species)
    plant.variety = _safe(payload.variety)
    plant.planted_at = payload.planted_at
    plant.notes = _safe(payload.notes)
    db.add(plant)
    db.commit()
    db.refresh(plant)
    return _to_out(plant)


@router.delete(
    "/plants/{plant_id}",
    response_model=dict[str, bool],
    operation_id="yp_deletePlant",
)
def delete_plant(
    plant_id: int, request: Request, db: SessionDep
) -> dict[str, bool]:
    yard = get_caller_yard(request, db)
    plant = db.get(YpPlant, plant_id)
    if plant is None or plant.yard_id != yard.id:
        raise HTTPException(status_code=404, detail="Plant not found")
    db.delete(plant)
    db.commit()
    return {"ok": True}
