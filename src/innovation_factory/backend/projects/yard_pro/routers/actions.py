"""Action log + calendar read endpoints for yard-pro.

This router owns the **GDPR Art. 22 load-bearing rail** (plan §2,
§8 row, §10 RT-016 isolation). ``POST /actions`` is the single point
where a coach recommendation or a telemetry nudge can land in the
``yp_action_log`` — and it MUST refuse any non-user-sourced row that
lacks a ``human_confirmed_at`` timestamp. The frontend's "Mark as done"
button is what makes that timestamp non-null; without that click,
nothing happens. There is no "do it for me" backend affordance.

The matching ``PATCH /actions/{id}/confirm`` route is the
review-and-confirm rail: a coach recommendation may be persisted with
``human_confirmed_at=None`` by an internal worker in a later phase
(only via internal code paths that bypass this router), but it stays
invisible to the cockpit's "what's done" feed until a user clicks
confirm. Right now P0 forbids the unconfirmed write entirely at the
API boundary; confirm exists so the same shape will work in P1+ when
the worker arrives.

Idempotency-Key (lessons §9-style replay safety, plan §9):
``yp_action_log.idempotency_key`` is populated from the optional HTTP
header on POST, but the 24h-cache replay-detection logic is **deferred
to P1** per plan §12. The column ships in P0 so the index can be built
without a migration when the cache turns on.
"""
from __future__ import annotations

from datetime import datetime, timezone
from typing import Annotated, Optional

from fastapi import APIRouter, Header, HTTPException, Request
from sqlmodel import select

from ....dependencies import SessionDep
from ....input_sanitize import sanitize_text
from ....pagination import Pagination


def _safe(text: str) -> str:
    """Sanitize and coerce to ``str`` — see ``routers/plants.py``."""
    cleaned = sanitize_text(text)
    return cleaned if isinstance(cleaned, str) else ""
from ..models import (
    YardProActionSource,
    YpActionLog,
    YpActionLogCreate,
    YpActionLogOut,
    YpCalendarEntry,
    YpCalendarEntryOut,
    YpConsumable,
    YpPlant,
    YpTool,
)
from .yards import get_caller_yard

router = APIRouter(tags=["yard-pro"])


def _to_action_out(a: YpActionLog) -> YpActionLogOut:
    return YpActionLogOut(
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


def _to_calendar_out(e: YpCalendarEntry) -> YpCalendarEntryOut:
    return YpCalendarEntryOut(
        id=e.id or 0,
        yard_id=e.yard_id,
        title=e.title,
        description=e.description,
        scheduled_at=e.scheduled_at,
        target_plant_id=e.target_plant_id,
        tool_id=e.tool_id,
        status=e.status,
    )


@router.get(
    "/actions",
    response_model=list[YpActionLogOut],
    operation_id="yp_listActions",
)
def list_actions(
    request: Request,
    page: Pagination,
    db: SessionDep,
) -> list[YpActionLogOut]:
    """Paginated history of the caller's action log (newest first).

    Uses the shared :class:`Pagination` dep (lessons §22) — bounds
    enforced at the dep layer; this handler can't accidentally return
    a 50k-row payload even if a future query string sneaks one in.
    """
    yard = get_caller_yard(request, db)
    rows = db.exec(
        select(YpActionLog)
        .where(YpActionLog.yard_id == yard.id)
        .order_by(YpActionLog.occurred_at.desc())  # type: ignore[unresolved-attribute]
        .offset(page.skip)
        .limit(page.limit)
    ).all()
    return [_to_action_out(a) for a in rows]


@router.post(
    "/actions",
    response_model=YpActionLogOut,
    operation_id="yp_logAction",
    status_code=201,
)
def log_action(
    request: Request,
    payload: YpActionLogCreate,
    db: SessionDep,
    idempotency_key: Annotated[
        Optional[str], Header(alias="Idempotency-Key")
    ] = None,
) -> YpActionLogOut:
    """Append a row to ``yp_action_log`` for the caller's yard.

    Art. 22 invariant (plan §2 non-negotiable):
        ``source != 'user'`` AND ``human_confirmed_at is None`` → 400.

    This is the load-bearing rail: a coach recommendation or a
    telemetry nudge cannot land in the log as a "done" action without
    an explicit human-confirm timestamp. The error body intentionally
    names "Art. 22" so the regression test in
    ``test_art22_invariant.py`` asserts on the symptom, not the
    implementation. Any future refactor that drops this check will
    break the test by name.
    """
    if (
        payload.source != YardProActionSource.user
        and payload.human_confirmed_at is None
    ):
        raise HTTPException(
            status_code=400,
            detail=(
                "Art. 22: human_confirmed_at required when source != 'user'"
            ),
        )

    yard = get_caller_yard(request, db)

    # Cross-household isolation for FK references — a coach turn could
    # try to attach the action to a plant/tool/consumable that belongs
    # to another household. Verify ownership before commit (RT-016).
    if payload.target_plant_id is not None:
        plant = db.get(YpPlant, payload.target_plant_id)
        if plant is None or plant.yard_id != yard.id:
            raise HTTPException(status_code=404, detail="Plant not found")
    if payload.tool_id is not None:
        tool = db.get(YpTool, payload.tool_id)
        if tool is None or tool.yard_id != yard.id:
            raise HTTPException(status_code=404, detail="Tool not found")
    if payload.consumable_id is not None:
        cons = db.get(YpConsumable, payload.consumable_id)
        if cons is None or cons.yard_id != yard.id:
            raise HTTPException(status_code=404, detail="Consumable not found")

    # The header takes precedence over the body-supplied key — clients
    # generally set the header (lessons §9 idempotency-replay convention)
    # but accept either for flexibility.
    resolved_idempotency_key = idempotency_key or payload.idempotency_key

    entry = YpActionLog(
        yard_id=yard.id or 0,
        action_type=payload.action_type,
        target_plant_id=payload.target_plant_id,
        tool_id=payload.tool_id,
        consumable_id=payload.consumable_id,
        occurred_at=payload.occurred_at or datetime.now(timezone.utc),
        notes=_safe(payload.notes),
        source=payload.source,
        human_confirmed_at=payload.human_confirmed_at,
        idempotency_key=resolved_idempotency_key,
    )
    db.add(entry)
    db.commit()
    db.refresh(entry)
    return _to_action_out(entry)


@router.patch(
    "/actions/{action_id}/confirm",
    response_model=YpActionLogOut,
    operation_id="yp_confirmAction",
)
def confirm_action(
    action_id: int, request: Request, db: SessionDep
) -> YpActionLogOut:
    """Set ``human_confirmed_at`` to now on an existing action row.

    Pairs with the "Mark as done" UI affordance. Idempotent — a second
    confirm leaves the existing timestamp untouched and returns 200.
    Cross-household access returns 404.
    """
    yard = get_caller_yard(request, db)
    entry = db.get(YpActionLog, action_id)
    if entry is None or entry.yard_id != yard.id:
        raise HTTPException(status_code=404, detail="Action not found")
    if entry.human_confirmed_at is None:
        entry.human_confirmed_at = datetime.now(timezone.utc)
        db.add(entry)
        db.commit()
        db.refresh(entry)
    return _to_action_out(entry)


@router.get(
    "/calendar",
    response_model=list[YpCalendarEntryOut],
    operation_id="yp_listCalendar",
)
def list_calendar(
    request: Request,
    page: Pagination,
    db: SessionDep,
) -> list[YpCalendarEntryOut]:
    """Paginated calendar entries for the caller's yard, scheduled-soonest
    first. Regeneration on action-log writes is B2's calendar_service
    responsibility — this is the read-side rail."""
    yard = get_caller_yard(request, db)
    rows = db.exec(
        select(YpCalendarEntry)
        .where(YpCalendarEntry.yard_id == yard.id)
        .order_by(YpCalendarEntry.scheduled_at)  # type: ignore[invalid-argument-type]
        .offset(page.skip)
        .limit(page.limit)
    ).all()
    return [_to_calendar_out(e) for e in rows]
