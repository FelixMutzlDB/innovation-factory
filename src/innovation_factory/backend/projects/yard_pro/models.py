"""Data models for the yard-pro project.

yard-pro is an AI gardening companion: connected-tool telemetry + yard
imagery + season-by-season care plan for homeowners. Tables follow the
``yp_*`` prefix; enums are prefixed ``YardPro`` to avoid OpenAPI schema
collisions with the other six accelerators (lessons §13).

3-model pattern (lessons CLAUDE.md): ``Yp<Entity>`` is the SQLModel table,
``Yp<Entity>Out`` is the API response, ``Yp<Entity>Create`` is the API
input. Models surfaced via the API expose Out/Create variants; internal
tables (e.g. ``YpToolReadiness``, ``YpCoachFeedback``) keep only the table
model until the corresponding route ships.

Non-negotiables encoded in this file:

- ``yp_action_log.source`` and ``human_confirmed_at`` together enforce
  GDPR Art. 22 (no solely-automated decisions). Backend rejects any
  ``source != 'user'`` write that lacks ``human_confirmed_at`` — the
  load-bearing rail. See plan §2 + §8.
- ``yp_action_log.idempotency_key`` + ``yp_diagnoses.idempotency_key``
  ship the schema in P0; the 24h replay-cache logic is deferred to P1
  (plan §12).
- ``yp_coach_feedback`` lands as a schema-only table in P0; the thumbs
  UI surfaces in P1.
"""
from __future__ import annotations

from datetime import date, datetime, timezone
from enum import Enum
from typing import Optional

from pydantic import BaseModel
from sqlmodel import Column, Field, JSON, SQLModel, Text


# ============================================================================
# Enums (YardPro-prefixed — avoid OpenAPI collisions, lessons §13)
# ============================================================================


class YardProToolKind(str, Enum):
    trimmer = "trimmer"
    hedge_cutter = "hedge_cutter"
    robotic_mower = "robotic_mower"
    chainsaw = "chainsaw"
    blower = "blower"
    other = "other"


class YardProBatteryFamily(str, Enum):
    """Battery families across cordless tools. Petrol tools = ``none``."""

    ap = "ap"
    asa = "asa"
    none = "none"


class YardProConsumableKind(str, Enum):
    fertilizer = "fertilizer"
    oil = "oil"
    lubricant = "lubricant"
    blade = "blade"
    fuel = "fuel"
    spray = "spray"
    seed = "seed"
    other = "other"


class YardProActionType(str, Enum):
    mow = "mow"
    fertilize = "fertilize"
    prune = "prune"
    water = "water"
    spray = "spray"
    plant = "plant"
    diagnose = "diagnose"
    other = "other"


class YardProActionSource(str, Enum):
    """Where the action originated. Drives the Art. 22 invariant."""

    user = "user"
    coach_recommendation = "coach_recommendation"
    telemetry_nudge = "telemetry_nudge"


class YardProDiagnosisStatus(str, Enum):
    pending = "pending"
    reviewed = "reviewed"
    acted_upon = "acted_upon"
    dismissed = "dismissed"


class YardProCalendarStatus(str, Enum):
    planned = "planned"
    done = "done"
    snoozed = "snoozed"
    skipped = "skipped"


class YardProTelemetryEventType(str, Enum):
    battery_low = "battery_low"
    maintenance_due = "maintenance_due"
    stuck = "stuck"
    session_started = "session_started"
    session_ended = "session_ended"


class YardProConsentState(str, Enum):
    none_ = "none"
    pending = "pending"
    granted = "granted"
    revoked = "revoked"


class YardProCoachFeedbackSignal(str, Enum):
    thumbs_up = "thumbs_up"
    thumbs_down = "thumbs_down"


class YardProChatRole(str, Enum):
    user = "user"
    assistant = "assistant"
    system = "system"


# ============================================================================
# Core tables (yp_*)
# ============================================================================


class YpYard(SQLModel, table=True):
    """One row per household (Martin's Stuttgart yard in seed)."""

    __tablename__ = "yp_yards"

    id: Optional[int] = Field(default=None, primary_key=True)
    user_key: str = Field(index=True)  # X-Forwarded-User equivalent; RLS key
    display_name: str
    region_code: str = Field(default="DE-BW")
    lat: float = Field(default=0.0)
    lng: float = Field(default=0.0)
    size_m2: float = Field(default=0.0)
    yard_metadata: dict = Field(default_factory=dict, sa_column=Column(JSON))
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))


class YpPlant(SQLModel, table=True):
    """Plant inventory per yard."""

    __tablename__ = "yp_plants"

    id: Optional[int] = Field(default=None, primary_key=True)
    yard_id: int = Field(foreign_key="yp_yards.id", index=True)
    species: str
    variety: str = Field(default="")
    planted_at: Optional[date] = None
    notes: str = Field(default="", sa_column=Column(Text))
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))


class YpTool(SQLModel, table=True):
    """Tools owned per household."""

    __tablename__ = "yp_tools"

    id: Optional[int] = Field(default=None, primary_key=True)
    yard_id: int = Field(foreign_key="yp_yards.id", index=True)
    kind: YardProToolKind
    display_name: str
    model_year: Optional[int] = None
    battery_family: YardProBatteryFamily = Field(default=YardProBatteryFamily.none)
    last_serviced_at: Optional[date] = None
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))


class YpConsumable(SQLModel, table=True):
    """Consumables stock (fertilizer, oil, blades, etc.)."""

    __tablename__ = "yp_consumables"

    id: Optional[int] = Field(default=None, primary_key=True)
    yard_id: int = Field(foreign_key="yp_yards.id", index=True)
    kind: YardProConsumableKind
    display_name: str
    quantity: float = Field(default=0.0)
    unit: str = Field(default="")
    last_restock_at: Optional[date] = None
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))


class YpActionLog(SQLModel, table=True):
    """Append-only event log. Carries the Art. 22 invariant columns.

    ``source != 'user'`` rows MUST carry a ``human_confirmed_at`` timestamp;
    the actions router rejects with 400 otherwise. ``idempotency_key`` is
    populated in P0 (UNIQUE partial index, see plan §5) but the 24h replay-
    cache lookup is deferred to P1.
    """

    __tablename__ = "yp_action_log"

    id: Optional[int] = Field(default=None, primary_key=True)
    yard_id: int = Field(foreign_key="yp_yards.id", index=True)
    action_type: YardProActionType
    target_plant_id: Optional[int] = Field(default=None, foreign_key="yp_plants.id")
    tool_id: Optional[int] = Field(default=None, foreign_key="yp_tools.id")
    consumable_id: Optional[int] = Field(default=None, foreign_key="yp_consumables.id")
    occurred_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc), index=True)
    notes: str = Field(default="", sa_column=Column(Text))
    source: YardProActionSource = Field(default=YardProActionSource.user)
    human_confirmed_at: Optional[datetime] = None
    idempotency_key: Optional[str] = Field(default=None, index=True)
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))


class YpDiagnosis(SQLModel, table=True):
    """CV diagnostic results from /diagnose (UC3)."""

    __tablename__ = "yp_diagnoses"

    id: Optional[int] = Field(default=None, primary_key=True)
    yard_id: int = Field(foreign_key="yp_yards.id", index=True)
    photo_uri: str = Field(default="")
    model_version: str = Field(default="")
    predictions: dict = Field(default_factory=dict, sa_column=Column(JSON))
    top_label: str = Field(default="")
    top_confidence: float = Field(default=0.0)
    accepted_label: Optional[str] = None
    status: YardProDiagnosisStatus = Field(default=YardProDiagnosisStatus.pending)
    idempotency_key: Optional[str] = Field(default=None, index=True)
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc), index=True)


class YpCalendarEntry(SQLModel, table=True):
    """Coach-generated personalized calendar entries (UC2)."""

    __tablename__ = "yp_calendar_entries"

    id: Optional[int] = Field(default=None, primary_key=True)
    yard_id: int = Field(foreign_key="yp_yards.id", index=True)
    title: str
    description: str = Field(default="", sa_column=Column(Text))
    scheduled_at: datetime
    target_plant_id: Optional[int] = Field(default=None, foreign_key="yp_plants.id")
    tool_id: Optional[int] = Field(default=None, foreign_key="yp_tools.id")
    status: YardProCalendarStatus = Field(default=YardProCalendarStatus.planned)
    generated_by_run_id: Optional[str] = Field(default=None, index=True)
    etag: str = Field(default="")
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))


class YpToolReadiness(SQLModel, table=True):
    """Latest readiness snapshot per tool — one row per ``yp_tools.id``.

    Upserted by the in-process telemetry synthesizer in P1; in P4 the same
    table is upserted by a Zerobus gRPC sink instead. Raw telemetry-at-
    volume lives in Delta Bronze, not here (lessons §3, §27).
    """

    __tablename__ = "yp_tool_readiness"

    tool_id: int = Field(primary_key=True, foreign_key="yp_tools.id")
    battery_pct: Optional[float] = None
    blade_hours_since_sharpening: Optional[float] = None
    last_session_at: Optional[datetime] = None
    last_event_type: Optional[YardProTelemetryEventType] = None
    last_event_at: Optional[datetime] = None
    payload: dict = Field(default_factory=dict, sa_column=Column(JSON))
    updated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))


class YpCoachFeedback(SQLModel, table=True):
    """One-tap feedback on coach responses (schema in P0; UI in P1).

    Closes the diagnostic-honesty advisory feedback loop (plan §8 AI security
    row): >5% thumbs_down per ``model_version`` over 100 turns auto-flags the
    version for manual review.
    """

    __tablename__ = "yp_coach_feedback"

    id: Optional[int] = Field(default=None, primary_key=True)
    yard_id: int = Field(foreign_key="yp_yards.id", index=True)
    response_id: str = Field(index=True)
    model_version: str = Field(default="")
    signal: YardProCoachFeedbackSignal
    notes: str = Field(default="", sa_column=Column(Text))
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))


class YpDealerRelationship(SQLModel, table=True):
    """Household ↔ dealer + consent state (P5 surface; schema lands in P0).

    Derisking the consent state machine: ship the table + the endpoint
    skeleton in P0 so the state transitions are exercised by tests from
    day one. The aggregation pipeline reads ``consent_state`` on every
    batch — see plan §7 risk callout.
    """

    __tablename__ = "yp_dealer_relationships"

    id: Optional[int] = Field(default=None, primary_key=True)
    yard_id: int = Field(foreign_key="yp_yards.id", index=True)
    dealer_id: str = Field(index=True)
    consent_state: YardProConsentState = Field(default=YardProConsentState.none_)
    consent_at: Optional[datetime] = None
    revoked_at: Optional[datetime] = None
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))


class YpCoachSession(SQLModel, table=True):
    """One coach chat session (UC2). Append-only history lives in
    ``YpCoachMessage`` for the SSE streaming protocol."""

    __tablename__ = "yp_coach_sessions"

    id: Optional[int] = Field(default=None, primary_key=True)
    yard_id: int = Field(foreign_key="yp_yards.id", index=True)
    title: str = Field(default="New chat")
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))


class YpCoachMessage(SQLModel, table=True):
    """A single turn in a coach session — assistant turns may carry
    citations + ``advisory=True`` metadata (Art. 50 EU AI Act chip).

    ``citations`` is a JSON list of ``KaChunkRef`` shapes (see
    ``services/coach_service.py``). On recommendation turns the response
    schema requires ``len(citations) >= 1`` — provenance enforcement per
    plan §8.
    """

    __tablename__ = "yp_coach_messages"

    id: Optional[int] = Field(default=None, primary_key=True)
    session_id: int = Field(foreign_key="yp_coach_sessions.id", index=True)
    role: YardProChatRole
    content: str = Field(default="", sa_column=Column(Text))
    citations: list = Field(default_factory=list, sa_column=Column(JSON))
    model_version: str = Field(default="")
    is_recommendation: bool = Field(default=False)
    advisory: bool = Field(default=True)
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))


# ============================================================================
# Pydantic I/O schemas — 3-model pattern (CLAUDE.md models & API)
# ============================================================================


class YpYardOut(BaseModel):
    id: int
    display_name: str
    region_code: str
    lat: float
    lng: float
    size_m2: float
    yard_metadata: dict


class YpPlantOut(BaseModel):
    id: int
    yard_id: int
    species: str
    variety: str
    planted_at: Optional[date]
    notes: str


class YpPlantCreate(BaseModel):
    species: str
    variety: str = ""
    planted_at: Optional[date] = None
    notes: str = ""


class YpToolOut(BaseModel):
    id: int
    yard_id: int
    kind: YardProToolKind
    display_name: str
    model_year: Optional[int]
    battery_family: YardProBatteryFamily
    last_serviced_at: Optional[date]


class YpToolCreate(BaseModel):
    kind: YardProToolKind
    display_name: str
    model_year: Optional[int] = None
    battery_family: YardProBatteryFamily = YardProBatteryFamily.none
    last_serviced_at: Optional[date] = None


class YpConsumableOut(BaseModel):
    id: int
    yard_id: int
    kind: YardProConsumableKind
    display_name: str
    quantity: float
    unit: str
    last_restock_at: Optional[date]


class YpConsumableCreate(BaseModel):
    kind: YardProConsumableKind
    display_name: str
    quantity: float = 0.0
    unit: str = ""
    last_restock_at: Optional[date] = None


class YpActionLogOut(BaseModel):
    id: int
    yard_id: int
    action_type: YardProActionType
    target_plant_id: Optional[int]
    tool_id: Optional[int]
    consumable_id: Optional[int]
    occurred_at: datetime
    notes: str
    source: YardProActionSource
    human_confirmed_at: Optional[datetime]


class YpActionLogCreate(BaseModel):
    """Input for ``POST /actions``. The Art. 22 invariant lives in the
    router: any payload with ``source != 'user'`` and no
    ``human_confirmed_at`` is rejected with 400."""

    action_type: YardProActionType
    target_plant_id: Optional[int] = None
    tool_id: Optional[int] = None
    consumable_id: Optional[int] = None
    occurred_at: Optional[datetime] = None
    notes: str = ""
    source: YardProActionSource = YardProActionSource.user
    human_confirmed_at: Optional[datetime] = None
    idempotency_key: Optional[str] = None


class YpCalendarEntryOut(BaseModel):
    id: int
    yard_id: int
    title: str
    description: str
    scheduled_at: datetime
    target_plant_id: Optional[int]
    tool_id: Optional[int]
    status: YardProCalendarStatus


class YpDiagnosisOut(BaseModel):
    id: int
    yard_id: int
    photo_uri: str
    model_version: str
    predictions: dict
    top_label: str
    top_confidence: float
    accepted_label: Optional[str]
    status: YardProDiagnosisStatus
    created_at: datetime
    # Advisory metadata — EU AI Act Art. 50, plan §2 non-negotiable. Always
    # True for now; reserved for future variants (e.g. a confirmed-by-pro
    # path) where it would drop to False.
    advisory: bool = True


class YpCockpitOut(BaseModel):
    """The UC1 anchor screen payload. One round-trip → first paint <1 s.

    Fields are intentionally flat — the cockpit's child cards (calendar /
    inventory / diagnose-result) each take a slice; the frontend does not
    fan out N fetches on cold load.
    """

    yard: YpYardOut
    plants: list[YpPlantOut]
    tools: list[YpToolOut]
    consumables: list[YpConsumableOut]
    upcoming_calendar: list[YpCalendarEntryOut]
    overdue_calendar: list[YpCalendarEntryOut]
    recent_actions: list[YpActionLogOut]
    recent_diagnoses: list[YpDiagnosisOut]
