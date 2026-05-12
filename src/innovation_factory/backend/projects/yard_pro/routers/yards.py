"""Yard endpoints — single source of truth for the calling user's yard
plus the UC1 cockpit anchor payload.

Tenancy rail (plan §8, RT-016): every read filters by the caller's
``user_key`` (resolved from the ``X-Forwarded-User`` header — the
Databricks Apps proxy is the only writer; never user-set, lessons §21).
Other yard-pro routers import :func:`_resolve_user_key` and
:func:`get_caller_yard` from this module so the resolution rule is
defined in exactly one place.
"""
from __future__ import annotations

from datetime import datetime, timezone
from typing import Optional

from fastapi import APIRouter, HTTPException, Request
from sqlmodel import select

from ....dependencies import SessionDep
from ..models import (
    YardProActionType,
    YardProCalendarStatus,
    YardProDiagnosisStatus,
    YpActionLog,
    YpActionLogOut,
    YpCalendarEntry,
    YpCalendarEntryOut,
    YpCockpitOut,
    YpConsumable,
    YpConsumableOut,
    YpDiagnosis,
    YpDiagnosisOut,
    YpPlant,
    YpPlantOut,
    YpTool,
    YpToolOut,
    YpYard,
    YpYardOut,
)

router = APIRouter(tags=["yard-pro"])


# ---------------------------------------------------------------------------
# Tenancy helpers — shared by the other yard-pro routers
# ---------------------------------------------------------------------------

#: Local-dev fallback user_key. Matches the seed (Martin's Stuttgart yard) so
#: ``curl ... -H 'X-Forwarded-User: martin@yard-pro.local'`` AND a bare
#: ``curl`` both work in ``apx dev start``. The Databricks Apps proxy
#: never lets a user spoof this header, so trusting it in production is
#: safe (lessons §21).
_LOCAL_DEV_FALLBACK_USER_KEY = "martin@yard-pro.local"


def _resolve_user_key(request: Request) -> str:
    """Resolve the calling user's identity from the auth-proxy header.

    Mirrors :func:`backend.rate_limit._user_or_ip` precedence:
    ``X-Forwarded-User`` first, then ``X-Forwarded-Preferred-Username``.
    In local dev (no proxy) falls back to the seeded Martin key so a
    bare ``curl`` to ``yards/me`` returns something useful.
    """
    for header in ("X-Forwarded-User", "X-Forwarded-Preferred-Username"):
        value = request.headers.get(header)
        if value:
            return value
    return _LOCAL_DEV_FALLBACK_USER_KEY


def get_caller_yard(request: Request, db) -> YpYard:
    """Return the yard belonging to the calling user.

    Raises 404 when no yard is seeded for the caller (the cockpit UI
    surfaces this as "no yard yet" rather than a 500). Used by every
    other yard-pro router that needs to enforce RLS.
    """
    user_key = _resolve_user_key(request)
    yard = db.exec(select(YpYard).where(YpYard.user_key == user_key)).first()
    if not yard:
        raise HTTPException(status_code=404, detail="No yard found for caller")
    return yard


def assert_yard_owned_by_caller(request: Request, db, yard_id: int) -> YpYard:
    """Look up a yard by ID and assert the caller owns it.

    Returns 404 (not 403) on cross-household access — the goal is to
    leak as little information as possible about other households'
    yard IDs. RT-016 cross-tenant isolation test enumerates these
    attack vectors.
    """
    user_key = _resolve_user_key(request)
    yard = db.get(YpYard, yard_id)
    if yard is None or yard.user_key != user_key:
        raise HTTPException(status_code=404, detail="Yard not found")
    return yard


# ---------------------------------------------------------------------------
# Routes
# ---------------------------------------------------------------------------


@router.get(
    "/yards/me",
    response_model=YpYardOut,
    operation_id="yp_getMyYard",
)
def get_my_yard(request: Request, db: SessionDep) -> YpYardOut:
    """Return the calling user's yard (one yard per user in P0)."""
    yard = get_caller_yard(request, db)
    return YpYardOut(
        id=yard.id or 0,
        display_name=yard.display_name,
        region_code=yard.region_code,
        lat=yard.lat,
        lng=yard.lng,
        size_m2=yard.size_m2,
        yard_metadata=yard.yard_metadata,
    )


@router.get(
    "/yards/{yard_id}/cockpit",
    response_model=YpCockpitOut,
    operation_id="yp_getCockpit",
)
def get_cockpit(yard_id: int, request: Request, db: SessionDep) -> YpCockpitOut:
    """One-shot UC1 anchor payload: yard + plants + tools + consumables +
    upcoming/overdue calendar + recent actions + recent diagnoses.

    Designed for <1s first paint per the demo gate in plan §2; the
    cockpit's child cards each take a slice of this response instead of
    issuing N parallel fetches on cold load. RLS enforced via
    :func:`assert_yard_owned_by_caller` — never returns another
    household's data even if the caller knows their yard_id.
    """
    yard = assert_yard_owned_by_caller(request, db, yard_id)
    now = datetime.now(timezone.utc)

    plants = list(
        db.exec(
            select(YpPlant).where(YpPlant.yard_id == yard.id).order_by(YpPlant.id)  # type: ignore[invalid-argument-type]
        ).all()
    )
    tools = list(
        db.exec(
            select(YpTool).where(YpTool.yard_id == yard.id).order_by(YpTool.id)  # type: ignore[invalid-argument-type]
        ).all()
    )
    consumables = list(
        db.exec(
            select(YpConsumable)
            .where(YpConsumable.yard_id == yard.id)
            .order_by(YpConsumable.id)  # type: ignore[invalid-argument-type]
        ).all()
    )

    upcoming = list(
        db.exec(
            select(YpCalendarEntry)
            .where(
                YpCalendarEntry.yard_id == yard.id,
                YpCalendarEntry.scheduled_at >= now,
                YpCalendarEntry.status == YardProCalendarStatus.planned,
            )
            .order_by(YpCalendarEntry.scheduled_at)  # type: ignore[invalid-argument-type]
            .limit(20)
        ).all()
    )
    overdue = list(
        db.exec(
            select(YpCalendarEntry)
            .where(
                YpCalendarEntry.yard_id == yard.id,
                YpCalendarEntry.scheduled_at < now,
                YpCalendarEntry.status == YardProCalendarStatus.planned,
            )
            .order_by(YpCalendarEntry.scheduled_at.desc())  # type: ignore[unresolved-attribute]
            .limit(20)
        ).all()
    )

    recent_actions = list(
        db.exec(
            select(YpActionLog)
            .where(YpActionLog.yard_id == yard.id)
            .order_by(YpActionLog.occurred_at.desc())  # type: ignore[unresolved-attribute]
            .limit(20)
        ).all()
    )
    recent_diagnoses = list(
        db.exec(
            select(YpDiagnosis)
            .where(YpDiagnosis.yard_id == yard.id)
            .order_by(YpDiagnosis.created_at.desc())  # type: ignore[unresolved-attribute]
            .limit(10)
        ).all()
    )

    return YpCockpitOut(
        yard=YpYardOut(
            id=yard.id or 0,
            display_name=yard.display_name,
            region_code=yard.region_code,
            lat=yard.lat,
            lng=yard.lng,
            size_m2=yard.size_m2,
            yard_metadata=yard.yard_metadata,
        ),
        plants=[
            YpPlantOut(
                id=p.id or 0,
                yard_id=p.yard_id,
                species=p.species,
                variety=p.variety,
                planted_at=p.planted_at,
                notes=p.notes,
            )
            for p in plants
        ],
        tools=[
            YpToolOut(
                id=t.id or 0,
                yard_id=t.yard_id,
                kind=t.kind,
                display_name=t.display_name,
                model_year=t.model_year,
                battery_family=t.battery_family,
                last_serviced_at=t.last_serviced_at,
            )
            for t in tools
        ],
        consumables=[
            YpConsumableOut(
                id=c.id or 0,
                yard_id=c.yard_id,
                kind=c.kind,
                display_name=c.display_name,
                quantity=c.quantity,
                unit=c.unit,
                last_restock_at=c.last_restock_at,
            )
            for c in consumables
        ],
        upcoming_calendar=[
            YpCalendarEntryOut(
                id=e.id or 0,
                yard_id=e.yard_id,
                title=e.title,
                description=e.description,
                scheduled_at=e.scheduled_at,
                target_plant_id=e.target_plant_id,
                tool_id=e.tool_id,
                status=e.status,
            )
            for e in upcoming
        ],
        overdue_calendar=[
            YpCalendarEntryOut(
                id=e.id or 0,
                yard_id=e.yard_id,
                title=e.title,
                description=e.description,
                scheduled_at=e.scheduled_at,
                target_plant_id=e.target_plant_id,
                tool_id=e.tool_id,
                status=e.status,
            )
            for e in overdue
        ],
        recent_actions=[
            YpActionLogOut(
                id=a.id or 0,
                yard_id=a.yard_id,
                action_type=a.action_type,
                target_plant_id=a.target_plant_id,
                tool_id=a.tool_id,
                consumable_id=a.consumable_id,
                occurred_at=a.occurred_at,
                notes=a.notes,
                source=a.source,
                human_confirmed_at=a.human_confirmed_at,
            )
            for a in recent_actions
        ],
        recent_diagnoses=[
            YpDiagnosisOut(
                id=d.id or 0,
                yard_id=d.yard_id,
                photo_uri=d.photo_uri,
                model_version=d.model_version,
                predictions=d.predictions,
                top_label=d.top_label,
                top_confidence=d.top_confidence,
                accepted_label=d.accepted_label,
                status=d.status,
                created_at=d.created_at,
            )
            for d in recent_diagnoses
        ],
    )


__all__ = [
    "router",
    "_resolve_user_key",
    "get_caller_yard",
    "assert_yard_owned_by_caller",
]
