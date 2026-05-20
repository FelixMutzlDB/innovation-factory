"""yard_context_service — the single source of truth shared by coach + calendar.

Plan §4 architecture decision: both ``coach_service.synthesize`` and
``calendar_service.regenerate`` consume the same typed :class:`YardContext`
so the two AI surfaces can't drift in what they see about Martin's yard.

What lives here (P0):
- Yard summary (display_name, region_code, lat/lng, size_m2, metadata)
- Plant list (species, variety, notes only — no PII expansion)
- Tool list (kind, battery_family, last_serviced_at) + readiness snapshot
- Last 14 days of action-log entries (so the coach knows what's been done)
- Upcoming + overdue calendar entries
- Weather window — **stubbed to a static "Stuttgart, partly cloudy, 18°C,
  7-day dry forecast" in P0**. Real weather integration is P1.

The shape is a Pydantic ``BaseModel`` so it's snapshot-testable and the
coach + calendar consume the same typed object. No SQLAlchemy ORM
instances escape this module — callers get plain typed values.
"""
from __future__ import annotations

from datetime import datetime, timedelta, timezone
from typing import Optional

from pydantic import BaseModel
from sqlmodel import Session, select

from ..models import (
    YardProCalendarStatus,
    YpActionLog,
    YpCalendarEntry,
    YpConsumable,
    YpPlant,
    YpTool,
    YpToolReadiness,
    YpYard,
)


def _event_type_value(readiness: Optional[YpToolReadiness]) -> Optional[str]:
    """Safely extract the last-event-type enum value from a readiness row.

    Returns ``None`` when the readiness row is missing or its
    ``last_event_type`` is None. Keeps the type-checker happy when the
    same upstream lookup is used both to gate the lookup and to read the
    enum's ``.value`` attribute.
    """
    if readiness is None or readiness.last_event_type is None:
        return None
    return readiness.last_event_type.value


# ---------------------------------------------------------------------------
# Typed context shape — Pydantic BaseModel for snapshot-testability
# ---------------------------------------------------------------------------


class YardSummary(BaseModel):
    id: int
    display_name: str
    region_code: str
    lat: float
    lng: float
    size_m2: float
    yard_metadata: dict


class PlantContext(BaseModel):
    id: int
    species: str
    variety: str
    notes: str


class ToolContext(BaseModel):
    id: int
    kind: str
    display_name: str
    battery_family: str
    last_serviced_at: Optional[str]  # ISO date or None
    battery_pct: Optional[float] = None
    blade_hours_since_sharpening: Optional[float] = None
    last_event_type: Optional[str] = None


class ConsumableContext(BaseModel):
    id: int
    kind: str
    display_name: str
    quantity: float
    unit: str


class ActionLogContext(BaseModel):
    id: int
    action_type: str
    notes: str
    occurred_at: datetime
    target_plant_id: Optional[int]
    tool_id: Optional[int]
    source: str


class CalendarEntryContext(BaseModel):
    id: int
    title: str
    description: str
    scheduled_at: datetime
    status: str
    target_plant_id: Optional[int]
    tool_id: Optional[int]


class WeatherWindow(BaseModel):
    """Stuttgart weather stub for P0. Real provider wired in P1."""

    location: str = "Stuttgart, Baden-Württemberg, DE"
    summary: str = "Partly cloudy, 18°C, 7-day dry forecast"
    seven_day_dry: bool = True
    temperature_c: float = 18.0
    source: str = "stub"  # 'stub' in P0; 'meteo-api' in P1


class YardContext(BaseModel):
    """Typed snapshot consumed by coach + calendar services."""

    yard: YardSummary
    plants: list[PlantContext]
    tools: list[ToolContext]
    consumables: list[ConsumableContext]
    recent_actions: list[ActionLogContext]  # last 14 days
    upcoming_calendar: list[CalendarEntryContext]  # status=planned, scheduled_at >= now
    overdue_calendar: list[CalendarEntryContext]  # status=planned, scheduled_at < now
    weather: WeatherWindow


# ---------------------------------------------------------------------------
# Public entry point
# ---------------------------------------------------------------------------


_RECENT_ACTIONS_DAYS = 14


def get_yard_context(session: Session, yard_id: int) -> YardContext:
    """Return the single-source-of-truth ``YardContext`` for ``yard_id``.

    Raises ``ValueError`` if the yard does not exist — callers should map
    this to a 404 at the HTTP boundary.
    """
    yard = session.get(YpYard, yard_id)
    if yard is None or yard.id is None:
        raise ValueError(f"Yard {yard_id} not found")

    plants = list(session.exec(select(YpPlant).where(YpPlant.yard_id == yard.id)).all())
    tools = list(session.exec(select(YpTool).where(YpTool.yard_id == yard.id)).all())
    consumables = list(
        session.exec(select(YpConsumable).where(YpConsumable.yard_id == yard.id)).all()
    )

    # Tool readiness keyed by tool_id (zero or one row per tool).
    readiness_by_tool: dict[int, YpToolReadiness] = {}
    if tools:
        tool_ids = [t.id for t in tools if t.id is not None]
        if tool_ids:
            readiness_rows = session.exec(
                select(YpToolReadiness).where(YpToolReadiness.tool_id.in_(tool_ids))  # type: ignore[union-attr]
            ).all()
            for r in readiness_rows:
                readiness_by_tool[r.tool_id] = r

    now = datetime.now(timezone.utc)
    cutoff = now - timedelta(days=_RECENT_ACTIONS_DAYS)
    recent_action_rows = list(
        session.exec(
            select(YpActionLog)
            .where(YpActionLog.yard_id == yard.id)
            .where(YpActionLog.occurred_at >= cutoff)
            .order_by(YpActionLog.occurred_at.desc())  # type: ignore[union-attr]
        ).all()
    )

    calendar_rows = list(
        session.exec(
            select(YpCalendarEntry)
            .where(YpCalendarEntry.yard_id == yard.id)
            .where(YpCalendarEntry.status == YardProCalendarStatus.planned)
            .order_by(YpCalendarEntry.scheduled_at)  # type: ignore[union-attr]
        ).all()
    )
    # Normalize the in-row datetimes to UTC so comparisons against ``now``
    # (tz-aware UTC) don't blow up on SQLite-naive datetimes.
    def _to_utc(dt: datetime) -> datetime:
        return dt if dt.tzinfo else dt.replace(tzinfo=timezone.utc)

    upcoming = [c for c in calendar_rows if _to_utc(c.scheduled_at) >= now]
    overdue = [c for c in calendar_rows if _to_utc(c.scheduled_at) < now]

    return YardContext(
        yard=YardSummary(
            id=yard.id,
            display_name=yard.display_name,
            region_code=yard.region_code,
            lat=yard.lat,
            lng=yard.lng,
            size_m2=yard.size_m2,
            yard_metadata=yard.yard_metadata or {},
        ),
        plants=[
            PlantContext(
                id=p.id or 0,
                species=p.species,
                variety=p.variety,
                notes=p.notes,
            )
            for p in plants
            if p.id is not None
        ],
        tools=[
            ToolContext(
                id=t.id or 0,
                kind=t.kind.value if hasattr(t.kind, "value") else str(t.kind),
                display_name=t.display_name,
                battery_family=(
                    t.battery_family.value
                    if hasattr(t.battery_family, "value")
                    else str(t.battery_family)
                ),
                last_serviced_at=t.last_serviced_at.isoformat()
                if t.last_serviced_at
                else None,
                battery_pct=(
                    readiness_by_tool[t.id].battery_pct
                    if t.id in readiness_by_tool
                    else None
                ),
                blade_hours_since_sharpening=(
                    readiness_by_tool[t.id].blade_hours_since_sharpening
                    if t.id in readiness_by_tool
                    else None
                ),
                last_event_type=_event_type_value(readiness_by_tool.get(t.id)),
            )
            for t in tools
            if t.id is not None
        ],
        consumables=[
            ConsumableContext(
                id=c.id or 0,
                kind=c.kind.value if hasattr(c.kind, "value") else str(c.kind),
                display_name=c.display_name,
                quantity=c.quantity,
                unit=c.unit,
            )
            for c in consumables
            if c.id is not None
        ],
        recent_actions=[
            ActionLogContext(
                id=a.id or 0,
                action_type=(
                    a.action_type.value
                    if hasattr(a.action_type, "value")
                    else str(a.action_type)
                ),
                notes=a.notes,
                occurred_at=a.occurred_at,
                target_plant_id=a.target_plant_id,
                tool_id=a.tool_id,
                source=a.source.value if hasattr(a.source, "value") else str(a.source),
            )
            for a in recent_action_rows
            if a.id is not None
        ],
        upcoming_calendar=[
            CalendarEntryContext(
                id=c.id or 0,
                title=c.title,
                description=c.description,
                scheduled_at=c.scheduled_at,
                status=c.status.value if hasattr(c.status, "value") else str(c.status),
                target_plant_id=c.target_plant_id,
                tool_id=c.tool_id,
            )
            for c in upcoming
            if c.id is not None
        ],
        overdue_calendar=[
            CalendarEntryContext(
                id=c.id or 0,
                title=c.title,
                description=c.description,
                scheduled_at=c.scheduled_at,
                status=c.status.value if hasattr(c.status, "value") else str(c.status),
                target_plant_id=c.target_plant_id,
                tool_id=c.tool_id,
            )
            for c in overdue
            if c.id is not None
        ],
        weather=WeatherWindow(),
    )
