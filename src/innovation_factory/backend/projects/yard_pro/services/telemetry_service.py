"""Telemetry synthesizer for yard-pro (UC4 — plan-phase P4 backend half).

The plan documents UC4 as "tool-readiness nudges" with **simulated telemetry**
in P1-P3 and real telemetry deferred to P4 (Zerobus gRPC ingestion client).
This module owns the simulated half: deterministic per-tool pseudo-events
written into ``yp_tool_readiness`` (a snapshot table; raw telemetry-at-volume
lives in Delta — lessons §3, §27).

**Determinism.** The synthesizer is keyed on ``tool_id`` (seeded
``random.Random``) so a given ``(tool_id, now)`` input produces the same
readiness snapshot. The UC1 demo "show a battery_low nudge" is therefore
stable across reloads — no flakiness in the demo gate.

**Art. 22 boundary.** Synthesizing events / dismissing nudges does **NOT**
write into ``yp_action_log``. Nudges are notifications; the user promotes a
nudge to a confirmed action via the ``<MarkAsDone>`` affordance (which calls
``POST /actions`` with ``source='telemetry_nudge' + human_confirmed_at``).
Plan §2 forbids any "do it for me" affordance — this module respects that.

**Nudge identity.** Nudges are derived from the readiness snapshot (one row
per tool); a nudge's ``nudge_id`` is a stable hash of ``(tool_id, event_type,
last_event_at)`` so a re-synthesis of the same state yields the same nudge_id
(and prior dismissals continue to suppress it). When the underlying state
changes, a new nudge_id is generated and the nudge re-surfaces.
"""
from __future__ import annotations

import hashlib
import random
from datetime import datetime, timedelta, timezone
from typing import Optional

from sqlmodel import Session, select

from ..models import (
    YardProActionType,
    YardProBatteryFamily,
    YardProTelemetryEventType,
    YardProToolKind,
    YpNudgeDismissal,
    YpNudgeOut,
    YpSynthesisResult,
    YpTool,
    YpToolReadiness,
)


# ---------------------------------------------------------------------------
# Tunables — small constants kept here so the test can import + assert
# ---------------------------------------------------------------------------

#: Below this battery percentage the synthesizer emits ``battery_low``.
BATTERY_LOW_THRESHOLD = 30.0

#: Blade hours since sharpening above which we emit ``maintenance_due``
#: for cutting tools (robotic mower, trimmer, hedge cutter).
BLADE_MAINTENANCE_THRESHOLD_H = 40.0

#: How many blade-hours the synthesizer assumes a robotic-mower session
#: accumulates — used for the deterministic drift calculation.
BLADE_HOURS_PER_SESSION = 2.0

#: How fast (in % per day since last session) a cordless battery drifts
#: down. Real packs hold charge much better — this is dialled high so a
#: P0 demo always has a fresh nudge to show.
BATTERY_DRIFT_PCT_PER_DAY = 1.5


def _nudge_id(tool_id: int, event_type: str, anchor_at: datetime) -> str:
    """Stable hash for nudge identity — see module docstring."""
    seed = f"{tool_id}|{event_type}|{anchor_at.isoformat()}"
    return "nudge-" + hashlib.sha1(seed.encode("utf-8")).hexdigest()[:12]


# ---------------------------------------------------------------------------
# Synthesizer — one-shot, deterministic
# ---------------------------------------------------------------------------


def synthesize_for_yard(
    session: Session,
    yard_id: int,
    *,
    now: Optional[datetime] = None,
) -> YpSynthesisResult:
    """Walk the yard's tools and upsert ``YpToolReadiness``.

    Idempotent: calling twice with the same ``now`` produces the same
    readiness state (the per-tool ``random.Random`` seed is the tool_id
    plus the calendar day of ``now``).
    """
    if now is None:
        now = datetime.now(timezone.utc)

    tools = list(
        session.exec(select(YpTool).where(YpTool.yard_id == yard_id)).all()
    )
    events_emitted: dict[str, int] = {}
    nudges_active = 0

    for tool in tools:
        readiness, event_type = _readiness_for_tool(tool, now)

        # Upsert: SQLModel primary key on tool_id, so .get + replace.
        existing = session.get(YpToolReadiness, tool.id)
        if existing is None:
            session.add(readiness)
        else:
            existing.battery_pct = readiness.battery_pct
            existing.blade_hours_since_sharpening = readiness.blade_hours_since_sharpening
            existing.last_session_at = readiness.last_session_at
            existing.last_event_type = readiness.last_event_type
            existing.last_event_at = readiness.last_event_at
            existing.payload = readiness.payload
            existing.updated_at = readiness.updated_at
            session.add(existing)

        if event_type is not None:
            events_emitted[event_type.value] = (
                events_emitted.get(event_type.value, 0) + 1
            )
        if _is_nudge_worthy(readiness):
            nudges_active += 1

    session.commit()
    return YpSynthesisResult(
        yard_id=yard_id,
        tools_updated=len(tools),
        events_emitted=events_emitted,
        nudges_active=nudges_active,
    )


def _readiness_for_tool(
    tool: YpTool, now: datetime
) -> tuple[YpToolReadiness, Optional[YardProTelemetryEventType]]:
    """Deterministic readiness snapshot for one tool.

    Returns the row + the dominant event_type (used for nudge derivation).
    Rules per tool kind:

    - Trimmer / hedge cutter / blower (cordless, AP/ASA pack): battery_pct
      drifts down ~1.5%/day since last service; ``battery_low`` fires when
      crossing the threshold.
    - Robotic mower: blade_hours accumulates ~2h per simulated session
      derived from days-since-service; ``maintenance_due`` fires when
      crossing ``BLADE_MAINTENANCE_THRESHOLD_H``.
    - Petrol chainsaw: no battery; only ``session_ended`` events when used.
    - Other / unknown: ``session_ended`` only.
    """
    rng = random.Random(f"{tool.id}|{now.date().isoformat()}")

    # Days since the tool was last serviced (the seed only carries
    # ``last_serviced_at``; we use that as the deterministic anchor).
    last_service = tool.last_serviced_at
    days_since_service = (now.date() - last_service).days if last_service else 30
    days_since_service = max(0, days_since_service)

    is_cordless = tool.battery_family in (
        YardProBatteryFamily.ap,
        YardProBatteryFamily.asa,
    )

    battery_pct: Optional[float] = None
    blade_hours: Optional[float] = None
    event_type: Optional[YardProTelemetryEventType] = None
    payload: dict = {"synthesized_at": now.isoformat()}

    if tool.kind == YardProToolKind.robotic_mower:
        sessions = max(1, days_since_service // 3)
        blade_hours = float(sessions * BLADE_HOURS_PER_SESSION)
        # Robotic mower keeps itself charged at the dock.
        battery_pct = round(85.0 + rng.uniform(-5.0, 10.0), 1)
        if blade_hours >= BLADE_MAINTENANCE_THRESHOLD_H:
            event_type = YardProTelemetryEventType.maintenance_due
            payload["reason"] = "blade hours exceed sharpening interval"
        else:
            event_type = YardProTelemetryEventType.session_ended
    elif is_cordless:
        # Battery drifts down from 100% based on days since last session.
        battery_pct = round(
            max(0.0, 100.0 - BATTERY_DRIFT_PCT_PER_DAY * days_since_service),
            1,
        )
        if battery_pct < BATTERY_LOW_THRESHOLD:
            event_type = YardProTelemetryEventType.battery_low
            payload["reason"] = "battery_pct below low threshold"
        else:
            event_type = YardProTelemetryEventType.session_ended
    elif tool.kind == YardProToolKind.chainsaw:
        event_type = YardProTelemetryEventType.session_ended
        payload["last_use"] = (now - timedelta(days=days_since_service)).isoformat()
    else:
        event_type = YardProTelemetryEventType.session_ended

    return (
        YpToolReadiness(
            tool_id=tool.id or 0,
            battery_pct=battery_pct,
            blade_hours_since_sharpening=blade_hours,
            last_session_at=now - timedelta(days=min(days_since_service, 30)),
            last_event_type=event_type,
            last_event_at=now,
            payload=payload,
            updated_at=now,
        ),
        event_type,
    )


def _is_nudge_worthy(readiness: YpToolReadiness) -> bool:
    """A readiness row produces a nudge when it carries an actionable
    event_type. ``session_ended`` is informational only."""
    return readiness.last_event_type in (
        YardProTelemetryEventType.battery_low,
        YardProTelemetryEventType.maintenance_due,
        YardProTelemetryEventType.stuck,
    )


# ---------------------------------------------------------------------------
# Nudge derivation — pure projection from readiness rows
# ---------------------------------------------------------------------------


def list_nudges_for_yard(session: Session, yard_id: int) -> list[YpNudgeOut]:
    """Return active nudges for a yard.

    Walks ``YpToolReadiness`` for tools belonging to this yard, projects
    each nudge-worthy row into a ``YpNudgeOut``, and suppresses any
    nudge_id that's already present in ``YpNudgeDismissal``.
    """
    rows = list(
        session.exec(
            select(YpToolReadiness, YpTool)
            .join(YpTool, YpTool.id == YpToolReadiness.tool_id)  # type: ignore[arg-type]
            .where(YpTool.yard_id == yard_id)
        ).all()
    )
    dismissed = {
        d.nudge_id
        for d in session.exec(
            select(YpNudgeDismissal).where(YpNudgeDismissal.yard_id == yard_id)
        ).all()
    }
    nudges: list[YpNudgeOut] = []
    for readiness, tool in rows:
        if not _is_nudge_worthy(readiness):
            continue
        if readiness.last_event_type is None or readiness.last_event_at is None:
            continue
        nid = _nudge_id(tool.id or 0, readiness.last_event_type.value, readiness.last_event_at)
        if nid in dismissed:
            continue
        nudges.append(_nudge_for(tool, readiness, nid))
    return nudges


def _nudge_for(
    tool: YpTool, readiness: YpToolReadiness, nudge_id: str
) -> YpNudgeOut:
    """Build a user-facing nudge payload from a readiness row."""
    et = readiness.last_event_type
    severity = "medium"
    title = "Tool needs attention"
    body = f"{tool.display_name} reports a readiness event."
    suggested: Optional[YardProActionType] = None

    if et == YardProTelemetryEventType.battery_low:
        severity = "medium"
        title = f"{tool.display_name} battery low"
        body = (
            f"Charge before the weekend — last reading "
            f"{readiness.battery_pct:.0f}%."
            if readiness.battery_pct is not None
            else f"{tool.display_name} battery is below 30%."
        )
        suggested = YardProActionType.other
    elif et == YardProTelemetryEventType.maintenance_due:
        severity = "high"
        title = f"{tool.display_name}: maintenance due"
        if readiness.blade_hours_since_sharpening is not None:
            body = (
                f"{readiness.blade_hours_since_sharpening:.0f} blade-hours "
                f"since last sharpening. Replace or sharpen blades."
            )
        else:
            body = f"{tool.display_name} is due for maintenance."
        suggested = YardProActionType.other
    elif et == YardProTelemetryEventType.stuck:
        severity = "high"
        title = f"{tool.display_name}: stuck"
        body = "Tool reported it is stuck. Free it and resume."

    return YpNudgeOut(
        nudge_id=nudge_id,
        tool_id=tool.id or 0,
        title=title,
        body=body,
        severity=severity,
        suggested_action_type=suggested,
        event_type=et,
        created_at=readiness.last_event_at or readiness.updated_at,
        dismissed_at=None,
        advisory=True,
    )


def dismiss_nudge(session: Session, yard_id: int, nudge_id: str) -> bool:
    """Record a dismissal. Idempotent — second dismiss is a no-op.

    Returns ``True`` when a new dismissal row was written, ``False`` when
    the dismissal already existed. Does NOT write into ``yp_action_log``
    (Art. 22 invariant — see module docstring).
    """
    existing = session.exec(
        select(YpNudgeDismissal).where(
            YpNudgeDismissal.yard_id == yard_id,
            YpNudgeDismissal.nudge_id == nudge_id,
        )
    ).first()
    if existing is not None:
        return False
    session.add(YpNudgeDismissal(yard_id=yard_id, nudge_id=nudge_id))
    session.commit()
    return True


def list_readiness_for_yard(session: Session, yard_id: int) -> list[YpToolReadiness]:
    """Return all ``YpToolReadiness`` rows for tools owned by the yard."""
    return list(
        session.exec(
            select(YpToolReadiness)
            .join(YpTool, YpTool.id == YpToolReadiness.tool_id)  # type: ignore[arg-type]
            .where(YpTool.yard_id == yard_id)
        ).all()
    )
