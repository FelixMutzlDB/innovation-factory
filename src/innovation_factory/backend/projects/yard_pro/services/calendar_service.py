"""calendar_service — personalized seasonal-care calendar regeneration.

Plan §12 UC2 success criterion #4: when Martin marks an action as done,
the calendar regenerates and **≥ 2 entries shift by ≥ 1 day**. The
service is invoked from the B1-owned actions router after a successful
``yp_action_log`` write.

Design notes:
- Consumes the same :class:`YardContext` as ``coach_service`` (plan §4).
- Deletes existing planned entries for the yard and writes fresh ones
  under a new ``generated_by_run_id`` so the regenerate-on-write contract
  is observable.
- The plan is intentionally **deterministic** in P0 — derived from
  plant species, tool readiness, weather window, and recent actions —
  so demo behavior is predictable. A live FM-API call to "plan my next
  28 days" is P1 work; the seed corpus isn't curated for it yet.
- The shift count is the load-bearing demo gate (≥ 2 entries move by
  ≥ 1 day). The deterministic plan-builder reorders entries based on
  what's been done recently so the shift naturally lands.
"""
from __future__ import annotations

import logging
import uuid
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone

from pydantic import BaseModel
from sqlmodel import Session, select

from ..models import (
    YardProActionType,
    YardProCalendarStatus,
    YpCalendarEntry,
)
from .yard_context_service import YardContext, get_yard_context

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Public output type
# ---------------------------------------------------------------------------


class RegenResult(BaseModel):
    """Summary of a calendar regeneration pass."""

    yard_id: int
    run_id: str
    total_entries: int
    shifted_entries: int  # # of entries whose scheduled_at moved by >= 1 day
    deleted_entries: int


# ---------------------------------------------------------------------------
# Plan builder — deterministic in P0
# ---------------------------------------------------------------------------


@dataclass(frozen=True)
class _PlannedTask:
    title: str
    description: str
    days_offset: int
    target_plant_id: int | None = None
    tool_id: int | None = None


def _build_plan(yard_context: YardContext) -> list[_PlannedTask]:
    """Build a 28-day plan from the yard context.

    Deterministic: the same context produces the same plan. Shifts come
    from the context changing — specifically, the recent-actions list
    growing causes the next entry of the same kind to slide further out.
    """

    now = datetime.now(timezone.utc)
    plan: list[_PlannedTask] = []

    # Action-type → number of days since last occurrence in the 14-day window.
    days_since: dict[str, int] = {}
    for action in yard_context.recent_actions:
        kind = action.action_type
        # Normalize naive datetimes to UTC so the subtraction is safe.
        occ = (
            action.occurred_at
            if action.occurred_at.tzinfo
            else action.occurred_at.replace(tzinfo=timezone.utc)
        )
        delta = max(0, (now - occ).days)
        if kind not in days_since or delta < days_since[kind]:
            days_since[kind] = delta

    # 1. Overdue/seasonal checks for fruit trees — always seed an early entry.
    fruit_plants = [
        p for p in yard_context.plants if p.species.lower() in {"apple", "cherry", "plum"}
    ]
    if fruit_plants:
        first = fruit_plants[0]
        plan.append(
            _PlannedTask(
                title=f"{first.species} tree fungus check",
                description=(
                    f"Walk {first.species.lower()} trees; inspect leaves for "
                    "scab/fungus. Treat if active."
                ),
                days_offset=2,
                target_plant_id=first.id,
            )
        )

    # 2. Mowing cadence — every 4-5 days during dry weather. If we
    # mowed recently, push it out; if not, schedule it soon.
    mower_tool = next(
        (t for t in yard_context.tools if t.kind == "robotic_mower"), None
    )
    last_mow_days = days_since.get(YardProActionType.mow.value, 14)
    next_mow_offset = max(1, 5 - last_mow_days)
    if mower_tool:
        plan.append(
            _PlannedTask(
                title="Mow lawn — full run",
                description=(
                    "Forecast dry; robotic mower full run recommended."
                ),
                days_offset=next_mow_offset,
                tool_id=mower_tool.id,
            )
        )

    # 3. Hedge trim — based on hedge plant + hedge_cutter tool.
    hedge_plant = next(
        (p for p in yard_context.plants if p.species.lower() == "beech"), None
    )
    hedge_tool = next(
        (t for t in yard_context.tools if t.kind == "hedge_cutter"), None
    )
    last_prune_days = days_since.get(YardProActionType.prune.value, 14)
    if hedge_plant and hedge_tool:
        plan.append(
            _PlannedTask(
                title="Hedge trim — east run",
                description="Beech hedge second pass — east-facing run.",
                days_offset=max(3, 8 - last_prune_days),
                target_plant_id=hedge_plant.id,
                tool_id=hedge_tool.id,
            )
        )

    # 4. Fruit-tree fertilizer ring — slow-release.
    last_fertilize_days = days_since.get(YardProActionType.fertilize.value, 14)
    if fruit_plants:
        plan.append(
            _PlannedTask(
                title="Fertilize tree ring (slow-release)",
                description="Slow-release NPK ring at each fruit tree; ~80 g/tree.",
                days_offset=max(6, 12 - last_fertilize_days),
            )
        )

    # 5. Lavender prune (light shaping after first bloom).
    lavender = next(
        (p for p in yard_context.plants if p.species.lower() == "lavender"), None
    )
    if lavender:
        plan.append(
            _PlannedTask(
                title="Lavender prune",
                description="Light shaping cut after first bloom; avoid old wood.",
                days_offset=14,
                target_plant_id=lavender.id,
            )
        )

    # 6. Watering check — if we haven't watered recently and it's a dry forecast.
    last_water_days = days_since.get(YardProActionType.water.value, 14)
    if yard_context.weather.seven_day_dry and last_water_days >= 4:
        plan.append(
            _PlannedTask(
                title="Deep water borders",
                description="7-day dry forecast — deep water front + back borders.",
                days_offset=max(1, 3 - (last_water_days - 4)),
            )
        )

    # 7. Tool readiness — trimmer charge if battery_pct < 50.
    trimmer = next(
        (t for t in yard_context.tools if t.kind == "trimmer"), None
    )
    if trimmer and trimmer.battery_pct is not None and trimmer.battery_pct < 50:
        plan.append(
            _PlannedTask(
                title="Charge trimmer battery",
                description=(
                    f"Trimmer battery at {trimmer.battery_pct:.0f}% — top up "
                    "before the weekend."
                ),
                days_offset=1,
                tool_id=trimmer.id,
            )
        )

    return plan


# ---------------------------------------------------------------------------
# Public entry point
# ---------------------------------------------------------------------------


def regenerate(
    session: Session,
    yard_id: int,
    trigger_action_id: int | None = None,
) -> RegenResult:
    """Delete planned calendar entries for ``yard_id`` and write a fresh plan.

    The fresh plan is generated under a new ``generated_by_run_id`` so the
    write path is observable. ``trigger_action_id`` is logged but not yet
    persisted (P1 wiring); the calendar table doesn't reserve a column.

    Returns a :class:`RegenResult` summarising the diff between the old
    and new plans. ``shifted_entries`` counts entries whose ``title``
    appears in both the pre- and post- snapshots but whose
    ``scheduled_at`` moved by ≥ 1 day — the demo step-4 gate.
    """
    yard_context = get_yard_context(session, yard_id)

    # Snapshot existing planned entries so we can compute the shift count.
    existing_planned = list(
        session.exec(
            select(YpCalendarEntry)
            .where(YpCalendarEntry.yard_id == yard_id)
            .where(YpCalendarEntry.status == YardProCalendarStatus.planned)
        ).all()
    )
    by_title_before: dict[str, datetime] = {}
    for entry in existing_planned:
        # Last-write wins on duplicate titles; titles are demo-stable.
        by_title_before[entry.title] = entry.scheduled_at

    # Delete existing planned entries — keep done/snoozed/skipped intact.
    deleted_count = 0
    for entry in existing_planned:
        session.delete(entry)
        deleted_count += 1
    session.flush()

    # Build + write the fresh plan.
    run_id = f"regen-{uuid.uuid4().hex[:12]}"
    plan = _build_plan(yard_context)
    now = datetime.now(timezone.utc)
    new_entries: list[YpCalendarEntry] = []
    for task in plan:
        new_entries.append(
            YpCalendarEntry(
                yard_id=yard_id,
                title=task.title,
                description=task.description,
                scheduled_at=now + timedelta(days=task.days_offset),
                target_plant_id=task.target_plant_id,
                tool_id=task.tool_id,
                status=YardProCalendarStatus.planned,
                generated_by_run_id=run_id,
                etag=run_id,
            )
        )
    for e in new_entries:
        session.add(e)
    session.flush()

    # Count shifts — same title appearing in both snapshots, scheduled_at
    # delta >= 1 day.
    shifted = 0
    for entry in new_entries:
        prev = by_title_before.get(entry.title)
        if prev is None:
            continue
        # Make tz-aware comparison safe.
        prev_aware = prev if prev.tzinfo else prev.replace(tzinfo=timezone.utc)
        new_aware = (
            entry.scheduled_at
            if entry.scheduled_at.tzinfo
            else entry.scheduled_at.replace(tzinfo=timezone.utc)
        )
        delta = abs((new_aware - prev_aware).total_seconds())
        if delta >= 86400:  # >= 1 day
            shifted += 1

    logger.info(
        "Calendar regen for yard %s: deleted=%d new=%d shifted=%d trigger=%s",
        yard_id,
        deleted_count,
        len(new_entries),
        shifted,
        trigger_action_id,
    )

    return RegenResult(
        yard_id=yard_id,
        run_id=run_id,
        total_entries=len(new_entries),
        shifted_entries=shifted,
        deleted_entries=deleted_count,
    )


def regenerate_for_action(
    session: Session,
    yard_id: int,
    action_id: int,
) -> RegenResult:
    """Convenience hook for the B1-owned actions router to call after a
    ``yp_action_log`` write. Just delegates to :func:`regenerate` and
    passes the trigger id through for log correlation.
    """
    return regenerate(session, yard_id, trigger_action_id=action_id)


__all__ = ["RegenResult", "regenerate", "regenerate_for_action"]
