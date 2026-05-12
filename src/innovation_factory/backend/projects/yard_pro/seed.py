"""Seed script for yard-pro — Martin's Stuttgart yard.

PGlite-safe (lessons §3): total row count is intentionally < 200. The
high-volume telemetry stream that would push past PGlite's memory ceiling
lives in Delta Bronze; ``seed_uc_tables.py`` writes ~10k rows there via
``INSERT … SELECT FROM range(N)`` (lessons §27).

Idempotent: ``seed_yp_data`` early-returns when ``YpYard`` already has a
row. Deterministic via a seeded ``random.Random`` so demo data is stable.

The 2026-05-08 row in ``yp_action_log`` is the **demo's load-bearing
string** — "Apple tree fungus check overdue 4 days" appears in §12 step 1
of the plan. Touching this date risks breaking that demo gate.
"""
from __future__ import annotations

import random
from datetime import date, datetime, timedelta, timezone

from sqlmodel import Session, select

from .models import (
    YardProActionSource,
    YardProActionType,
    YardProBatteryFamily,
    YardProCalendarStatus,
    YardProConsumableKind,
    YardProDiagnosisStatus,
    YardProTelemetryEventType,
    YardProToolKind,
    YpActionLog,
    YpCalendarEntry,
    YpConsumable,
    YpDiagnosis,
    YpPlant,
    YpTool,
    YpToolReadiness,
    YpYard,
)

_rng = random.Random(2026_05_12)
TODAY = date(2026, 5, 12)
NOW = datetime(2026, 5, 12, 9, 0, tzinfo=timezone.utc)
MARTIN_USER_KEY = "martin@yard-pro.local"


def _ts(d: date, hour: int = 9, minute: int = 0) -> datetime:
    return datetime(d.year, d.month, d.day, hour, minute, tzinfo=timezone.utc)


# ---------------------------------------------------------------------------
# Plant inventory — 12 plants total (4 fruit trees, 1 hedge, 7 perennials)
# ---------------------------------------------------------------------------

PLANTS: list[dict] = [
    # 4 fruit trees — fundamental to the demo (apple-tree fungus check)
    {"species": "Apple", "variety": "Boskoop", "planted_at": date(2019, 4, 12),
     "notes": "South-facing wall; espalier on east side."},
    {"species": "Apple", "variety": "Elstar", "planted_at": date(2019, 4, 12),
     "notes": "Showed minor scab in 2025 — kept untreated."},
    {"species": "Cherry", "variety": "Schneiders späte Knorpelkirsche",
     "planted_at": date(2018, 3, 20), "notes": "Self-fertile pair with the next-door garden's Hedelfinger."},
    {"species": "Plum", "variety": "Hauszwetschge", "planted_at": date(2020, 4, 5),
     "notes": "Late variety, harvest mid-September."},
    # 1 beech hedge — recorded as a single plant row
    {"species": "Beech", "variety": "Fagus sylvatica",
     "planted_at": date(2015, 11, 8),
     "notes": "30 m run along the north property line; trim June + August."},
    # 7 perennials / shrubs
    {"species": "Lavender", "variety": "Hidcote", "planted_at": date(2021, 5, 1),
     "notes": "Front border."},
    {"species": "Rose", "variety": "Schneewittchen", "planted_at": date(2022, 4, 15),
     "notes": "Trellised against the shed."},
    {"species": "Rhododendron", "variety": "Cunningham's White",
     "planted_at": date(2020, 10, 3), "notes": "Acidic-soil patch under the cherry."},
    {"species": "Hydrangea", "variety": "Endless Summer",
     "planted_at": date(2023, 5, 20), "notes": "Pruned hard in March."},
    {"species": "Boxwood", "variety": "Suffruticosa",
     "planted_at": date(2017, 3, 30), "notes": "Watch for boxwood moth."},
    {"species": "Rosemary", "variety": "Tuscan Blue",
     "planted_at": date(2024, 5, 5), "notes": "Mediterranean herb spiral."},
    {"species": "Thyme", "variety": "English",
     "planted_at": date(2024, 5, 5), "notes": "Herb spiral, top tier."},
]


# ---------------------------------------------------------------------------
# Tools — 5 owned (Stihl-shaped real world)
# ---------------------------------------------------------------------------

TOOLS: list[dict] = [
    {
        "kind": YardProToolKind.trimmer,
        "display_name": "Cordless trimmer",
        "model_year": 2022,
        "battery_family": YardProBatteryFamily.ap,
        "last_serviced_at": date(2025, 9, 14),
    },
    {
        "kind": YardProToolKind.hedge_cutter,
        "display_name": "Cordless hedge cutter",
        "model_year": 2023,
        "battery_family": YardProBatteryFamily.ap,
        "last_serviced_at": date(2025, 7, 2),
    },
    {
        "kind": YardProToolKind.robotic_mower,
        "display_name": "Robotic mower",
        "model_year": 2021,
        "battery_family": YardProBatteryFamily.asa,
        "last_serviced_at": date(2025, 4, 18),
    },
    {
        "kind": YardProToolKind.chainsaw,
        "display_name": "Petrol chainsaw",
        "model_year": 2018,
        "battery_family": YardProBatteryFamily.none,
        "last_serviced_at": date(2024, 11, 10),
    },
    {
        "kind": YardProToolKind.blower,
        "display_name": "Cordless leaf blower",
        "model_year": 2023,
        "battery_family": YardProBatteryFamily.ap,
        "last_serviced_at": None,
    },
]


# ---------------------------------------------------------------------------
# Consumables — 8 items
# ---------------------------------------------------------------------------

CONSUMABLES: list[dict] = [
    {"kind": YardProConsumableKind.fertilizer, "display_name": "Lawn fertilizer NPK 20-5-8",
     "quantity": 2.5, "unit": "kg", "last_restock_at": date(2026, 3, 21)},
    {"kind": YardProConsumableKind.fertilizer, "display_name": "Slow-release tree fertilizer",
     "quantity": 1.2, "unit": "kg", "last_restock_at": date(2025, 10, 5)},
    {"kind": YardProConsumableKind.oil, "display_name": "2-stroke chainsaw mix oil",
     "quantity": 0.8, "unit": "L", "last_restock_at": date(2025, 8, 1)},
    {"kind": YardProConsumableKind.oil, "display_name": "Bar-and-chain oil",
     "quantity": 1.5, "unit": "L", "last_restock_at": date(2025, 8, 1)},
    {"kind": YardProConsumableKind.lubricant, "display_name": "Trimmer-head grease",
     "quantity": 0.1, "unit": "kg", "last_restock_at": date(2025, 6, 12)},
    {"kind": YardProConsumableKind.blade, "display_name": "Robotic mower blade set",
     "quantity": 9, "unit": "pcs", "last_restock_at": date(2025, 4, 18)},
    {"kind": YardProConsumableKind.spray, "display_name": "Copper-based fungicide",
     "quantity": 0.5, "unit": "L", "last_restock_at": date(2026, 4, 2)},
    {"kind": YardProConsumableKind.fuel, "display_name": "Alkylate petrol",
     "quantity": 5.0, "unit": "L", "last_restock_at": date(2025, 9, 1)},
]


# ---------------------------------------------------------------------------
# 30-day action log — most recent 30 days
# ---------------------------------------------------------------------------
# The 2026-05-08 fungus-check row is the demo's load-bearing string.

_ACTION_LOG_TEMPLATES: list[tuple[int, YardProActionType, str, int | None, int | None]] = [
    # (days_ago, action_type, notes, plant_idx, tool_idx)
    (4, YardProActionType.diagnose, "Apple tree fungus check overdue — last looked 4 days ago.", 0, None),
    (5, YardProActionType.mow, "Robotic mower zone 1+2 full run; blade looked dull.", None, 2),
    (6, YardProActionType.water, "Front border deep watering after dry week.", 5, None),
    (8, YardProActionType.prune, "Light shaping cut on hydrangea after first flush.", 8, None),
    (10, YardProActionType.fertilize, "Lawn NPK at 30 g/m² across 400 m².", None, None),
    (12, YardProActionType.mow, "Robotic mower zone 3 run.", None, 2),
    (14, YardProActionType.spray, "Copper fungicide on apple after wet spell.", 0, None),
    (15, YardProActionType.mow, "Robotic mower full lawn run.", None, 2),
    (17, YardProActionType.water, "Pots + hanging baskets.", None, None),
    (18, YardProActionType.prune, "Beech hedge first trim of the season — west run only.", 4, 1),
    (19, YardProActionType.plant, "Replanted thyme spot after winter loss.", 11, None),
    (21, YardProActionType.mow, "Cordless trimmer edges only.", None, 0),
    (22, YardProActionType.fertilize, "Slow-release fertilizer ring at each fruit tree.", 0, None),
    (23, YardProActionType.water, "Vegetable seedlings.", None, None),
    (24, YardProActionType.mow, "Robotic mower zone 1+2.", None, 2),
    (25, YardProActionType.other, "Sharpened robotic mower blades.", None, 2),
    (27, YardProActionType.prune, "Removed dead wood from cherry.", 2, None),
    (28, YardProActionType.water, "Hedge base watering.", 4, None),
    (29, YardProActionType.spray, "Boxwood moth pheromone refresh.", 9, None),
    (30, YardProActionType.mow, "Robotic mower full run.", None, 2),
    # Older sprinkling to bring the total to 30
    (33, YardProActionType.fertilize, "Rose feeding.", 6, None),
    (35, YardProActionType.water, "Rhododendron deep water.", 7, None),
    (37, YardProActionType.prune, "Removed cherry blossom deadheads.", 2, None),
    (40, YardProActionType.other, "Robotic mower battery service check.", None, 2),
    (43, YardProActionType.water, "Beech hedge base water.", 4, None),
    (46, YardProActionType.mow, "Robotic mower zone 3 only.", None, 2),
    (49, YardProActionType.fertilize, "Lavender annual feed.", 5, None),
    (52, YardProActionType.spray, "Late-spring boxwood spray.", 9, None),
    (55, YardProActionType.water, "Spot watering during dry warm week.", None, None),
    (58, YardProActionType.other, "Tightened trimmer head.", None, 0),
]


# ---------------------------------------------------------------------------
# 5 calendar entries — upcoming + overdue
# ---------------------------------------------------------------------------

_CALENDAR_TEMPLATES: list[tuple[int, str, str, YardProCalendarStatus, int | None, int | None]] = [
    # (days_offset, title, description, status, plant_idx, tool_idx)
    (-4, "Apple tree fungus check (overdue)",
     "Walk apple trees; inspect leaves for scab/fungus. Treat if active.",
     YardProCalendarStatus.planned, 0, None),
    (2, "Mow lawn — full run",
     "Forecast dry through Saturday; robotic mower full run recommended.",
     YardProCalendarStatus.planned, None, 2),
    (5, "Hedge first trim — east run",
     "Beech hedge second pass — east-facing run only.",
     YardProCalendarStatus.planned, 4, 1),
    (9, "Fertilize tree ring (slow-release)",
     "Slow-release NPK ring at each fruit tree; ~80 g/tree.",
     YardProCalendarStatus.planned, None, None),
    (14, "Lavender prune",
     "Light shaping cut after first bloom; avoid old wood.",
     YardProCalendarStatus.planned, 5, None),
]


# ---------------------------------------------------------------------------
# 3 telemetry-readiness rows + 2 diagnoses (seed history)
# ---------------------------------------------------------------------------


def seed_yp_data(session: Session) -> None:
    """Idempotent seed entry point — registered in ``backend/seed.py``."""

    existing = session.exec(select(YpYard)).first()
    if existing:
        return

    # --- Yard ---------------------------------------------------------------
    yard = YpYard(
        user_key=MARTIN_USER_KEY,
        display_name="Martin's Yard",
        region_code="DE-BW",
        lat=48.7758,
        lng=9.1829,
        size_m2=900.0,
        yard_metadata={
            "lawn_m2": 400,
            "hedge_m": 30,
            "fruit_trees": 4,
            "microclimate": "Stuttgart kettle — late frost risk to mid-April",
        },
    )
    session.add(yard)
    session.flush()
    assert yard.id is not None

    # --- Plants -------------------------------------------------------------
    plants: list[YpPlant] = []
    for spec in PLANTS:
        p = YpPlant(yard_id=yard.id, **spec)
        session.add(p)
        plants.append(p)
    session.flush()

    # --- Tools --------------------------------------------------------------
    tools: list[YpTool] = []
    for spec in TOOLS:
        t = YpTool(yard_id=yard.id, **spec)
        session.add(t)
        tools.append(t)
    session.flush()

    # --- Consumables --------------------------------------------------------
    for spec in CONSUMABLES:
        c = YpConsumable(yard_id=yard.id, **spec)
        session.add(c)
    session.flush()

    # --- Action log ---------------------------------------------------------
    for days_ago, action_type, notes, plant_idx, tool_idx in _ACTION_LOG_TEMPLATES:
        occurred = NOW - timedelta(days=days_ago)
        entry = YpActionLog(
            yard_id=yard.id,
            action_type=action_type,
            target_plant_id=plants[plant_idx].id if plant_idx is not None else None,
            tool_id=tools[tool_idx].id if tool_idx is not None else None,
            occurred_at=occurred,
            notes=notes,
            source=YardProActionSource.user,
            human_confirmed_at=occurred,  # All seeded user-actions are pre-confirmed.
        )
        session.add(entry)
    session.flush()

    # --- Calendar entries ---------------------------------------------------
    for days_offset, title, description, status, plant_idx, tool_idx in _CALENDAR_TEMPLATES:
        scheduled = NOW + timedelta(days=days_offset)
        entry = YpCalendarEntry(
            yard_id=yard.id,
            title=title,
            description=description,
            scheduled_at=scheduled,
            target_plant_id=plants[plant_idx].id if plant_idx is not None else None,
            tool_id=tools[tool_idx].id if tool_idx is not None else None,
            status=status,
            generated_by_run_id="seed-2026-05-12",
            etag="seed-v1",
        )
        session.add(entry)
    session.flush()

    # --- Tool readiness snapshots (3 rows, sparse) --------------------------
    # Robotic mower
    session.add(
        YpToolReadiness(
            tool_id=tools[2].id,
            battery_pct=92.0,
            blade_hours_since_sharpening=18.5,
            last_session_at=NOW - timedelta(days=2),
            last_event_type=YardProTelemetryEventType.session_ended,
            last_event_at=NOW - timedelta(days=2),
            payload={"zone_3_runtime_min": 35, "rain_skips_7d": 2},
        )
    )
    # Hedge cutter
    session.add(
        YpToolReadiness(
            tool_id=tools[1].id,
            battery_pct=78.0,
            blade_hours_since_sharpening=12.0,
            last_session_at=NOW - timedelta(days=18),
            last_event_type=YardProTelemetryEventType.session_ended,
            last_event_at=NOW - timedelta(days=18),
            payload={},
        )
    )
    # Trimmer
    session.add(
        YpToolReadiness(
            tool_id=tools[0].id,
            battery_pct=46.0,
            blade_hours_since_sharpening=7.5,
            last_session_at=NOW - timedelta(days=21),
            last_event_type=YardProTelemetryEventType.battery_low,
            last_event_at=NOW - timedelta(days=21),
            payload={"reminder": "charge before weekend"},
        )
    )

    # --- Diagnoses (2 seeded for history) ----------------------------------
    session.add(
        YpDiagnosis(
            yard_id=yard.id,
            photo_uri="seed://yard_pro/diagnoses/2026-04-14-yellow-lawn-patch.jpg",
            model_version="yard-pro-vision-v0",
            predictions={
                "labels": [
                    {"name": "fusarium_blight", "confidence": 0.82},
                    {"name": "drought_stress", "confidence": 0.11},
                    {"name": "healthy", "confidence": 0.07},
                ]
            },
            top_label="fusarium_blight",
            top_confidence=0.82,
            accepted_label="fusarium_blight",
            status=YardProDiagnosisStatus.acted_upon,
            created_at=NOW - timedelta(days=28),
        )
    )
    session.add(
        YpDiagnosis(
            yard_id=yard.id,
            photo_uri="seed://yard_pro/diagnoses/2026-04-30-apple-leaf-spot.jpg",
            model_version="yard-pro-vision-v0",
            predictions={
                "labels": [
                    {"name": "apple_scab", "confidence": 0.71},
                    {"name": "healthy", "confidence": 0.18},
                    {"name": "powdery_mildew", "confidence": 0.11},
                ]
            },
            top_label="apple_scab",
            top_confidence=0.71,
            accepted_label=None,
            status=YardProDiagnosisStatus.reviewed,
            created_at=NOW - timedelta(days=12),
        )
    )

    print("  Seeded yard-pro data (Martin's Stuttgart yard).")
