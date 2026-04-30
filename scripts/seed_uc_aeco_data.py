"""Seed AECO Hub data into Unity Catalog tables.

Mirrors :mod:`seed_uc_hb_data` — produces a list of SQL statements that the
Phase 3 deployer (:mod:`deploy_agents_fevm`) executes against the warehouse.

Design notes:
- Project / building / cost / schedule / issue mirrors are small enough for
  ``INSERT VALUES`` (a few hundred rows total).
- Sensor readings is large (~500K rows over 1 year for operating projects).
  We generate them server-side via ``INSERT ... SELECT FROM range(N)`` so the
  warehouse does the work — far faster than streaming 500K parameter rows
  over the SQL API.
- Idempotency: callers should ``DROP TABLE IF EXISTS`` then re-create from
  ``uc_schema`` before running these inserts (the AdTech phase does the same).

Run via: python scripts/seed_uc_aeco_data.py  (prints statement summaries)
"""
from __future__ import annotations

import random
from datetime import date, datetime, timedelta, timezone

import os

# Default catalog for standalone runs; the deploy_agents_fevm.py orchestrator
# overrides via the build_sql(catalog=...) parameter so the same generator
# works against multiple workspaces (felix_demo_catalog, innovation_factory_catalog, …).
DEFAULT_CATALOG = os.getenv("AECO_UC_CATALOG", "innovation_factory_catalog")
SCHEMA = "aeco_hub"
_rng = random.Random(2026)
TODAY = date.today()


def _ts(dt) -> str:
    if dt is None:
        return "NULL"
    if isinstance(dt, date) and not isinstance(dt, datetime):
        return f"DATE '{dt.isoformat()}'"
    return f"TIMESTAMP '{dt.strftime('%Y-%m-%d %H:%M:%S')}'"


def _s(val) -> str:
    if val is None:
        return "NULL"
    return "'" + str(val).replace("'", "''") + "'"


# Mirror the same Schuster Bau AG portfolio used in the Lakebase seed so
# Genie / dashboards line up with what the app shows. Keep these in sync if
# the Lakebase seed (``backend/projects/aeco_hub/seed.py``) changes.
PROJECTS = [
    # (id, code, name, client, city, phase, progress, budget, actual)
    (1, "QSP-2024", "Quartier am Stadtpark",     "Stadtpark Immobilien GmbH", "Munich",     "operate",  100.0, 78_500_000.0, 81_300_000.0),
    (2, "THC-2025", "TechHub Campus Garching",   "Bayern Tech Estates AG",    "Garching",   "build",     65.0, 142_000_000.0, 91_400_000.0),
    (3, "KES-2026", "Klinikum Erweiterung Süd",  "Klinikum Stuttgart gGmbH",  "Stuttgart",  "design",    22.0, 64_000_000.0, 4_100_000.0),
    (4, "LOG-A9",   "Logistikzentrum A9",        "Süddeutsche Logistik AG",   "Ingolstadt", "operate",  100.0, 38_000_000.0, 37_200_000.0),
    (5, "AMS-RENO", "Altbau Maximilianstraße",   "Maximilian Real Estate KG", "Munich",     "demolish",  38.0, 12_500_000.0, 5_800_000.0),
]


# (project_id, building_id, name, type, floors, gfa, year)
BUILDINGS = [
    (1, 1, "QSP-A Residential North", "residential", 6, 12_400.0, 2024),
    (1, 2, "QSP-B Residential South", "residential", 5, 10_800.0, 2024),
    (1, 3, "QSP-C Retail Plinth",     "retail",      2,  4_900.0, 2024),
    (2, 4, "THC-1 East Wing",         "office",      6, 18_200.0, None),
    (2, 5, "THC-2 West Wing",         "office",      4, 12_900.0, None),
    (3, 6, "KES Hauptbau",            "healthcare",  5,  9_600.0, None),
    (4, 7, "LOG-A9 Hall",             "industrial",  4, 22_400.0, 2022),
    (5, 8, "Maximilianstraße 14",     "mixed_use",   4,  3_900.0, 1894),
]


SENSOR_TYPES = [
    ("zone_temp",          "C",   18.0,   28.0),
    ("supply_air_temp",    "C",   12.0,   22.0),
    ("relative_humidity",  "%RH", 30.0,   70.0),
    ("co2_concentration",  "ppm", 400.0,  1500.0),
    ("active_power",       "kW",  0.0,    500.0),
    ("dimming_level",      "%",   0.0,    100.0),
]


def _project_inserts(catalog: str) -> list[str]:
    rows = []
    for pid, code, name, client, city, phase, progress, budget, actual in PROJECTS:
        start = date(2023, 1, 1) + timedelta(days=_rng.randint(0, 600))
        target = start + timedelta(days=_rng.randint(540, 1080))
        rows.append(
            f"({pid}, {_s(code)}, {_s(name)}, {_s(client)}, {_s(city)}, 'DE', "
            f"{_s(phase)}, 'active', {progress}, {budget}, {actual}, "
            f"DATE '{start}', DATE '{target}')"
        )
    return [
        f"INSERT INTO {catalog}.{SCHEMA}.dt_projects "
        f"(id, code, name, client_name, city, country, phase, status, progress_pct, "
        f"budget_eur, actual_cost_eur, start_date, target_completion_date) VALUES\n"
        + ",\n".join(rows)
    ]


def _building_inserts(catalog: str) -> list[str]:
    rows = []
    for project_id, bid, name, btype, floors, gfa, year in BUILDINGS:
        city = next(p[4] for p in PROJECTS if p[0] == project_id)
        year_val = "NULL" if year is None else str(year)
        rows.append(
            f"({bid}, {project_id}, {_s(name)}, {_s(btype)}, {floors}, {gfa}, {year_val}, {_s(city)})"
        )
    return [
        f"INSERT INTO {catalog}.{SCHEMA}.dt_buildings "
        f"(id, project_id, name, building_type, floor_count, gross_floor_area_sqm, year_built, city) VALUES\n"
        + ",\n".join(rows)
    ]


def _cost_inserts(catalog: str) -> list[str]:
    cost_templates = [
        ("01.10", "Earthworks and excavation",    "Earthworks"),
        ("02.20", "Concrete foundations",         "Structure"),
        ("02.30", "Reinforced concrete walls",    "Structure"),
        ("03.10", "Steel structure",              "Structure"),
        ("04.10", "Roofing membrane",             "Envelope"),
        ("04.20", "Curtain wall facade",          "Envelope"),
        ("05.10", "Interior partitions",          "Interiors"),
        ("06.10", "HVAC ductwork",                "MEP"),
        ("06.30", "Chillers",                     "MEP"),
        ("07.10", "Electrical panels",            "MEP"),
        ("09.10", "Elevators",                    "Vertical"),
        ("10.10", "Site landscaping",             "Site"),
    ]
    statuses = ["estimated", "committed", "actual", "paid"]
    rows = []
    next_id = 1
    for project in PROJECTS:
        pid = project[0]
        for _ in range(_rng.randint(20, 35)):
            code, desc, category = _rng.choice(cost_templates)
            estimated = round(_rng.uniform(50_000, 2_000_000), 2)
            actual = round(estimated * _rng.uniform(0.85, 1.25), 2)
            status = _rng.choice(statuses)
            actual_val = actual if status in ("actual", "paid") else 0.0
            rows.append(
                f"({next_id}, {pid}, {_s(code)}, {_s(desc)}, {_s(category)}, "
                f"{estimated}, {actual_val}, {_s(status)})"
            )
            next_id += 1
    return [
        f"INSERT INTO {catalog}.{SCHEMA}.dt_cost_items "
        f"(id, project_id, code, description, category, estimated_eur, actual_eur, status) VALUES\n"
        + ",\n".join(rows)
    ]


def _schedule_inserts(catalog: str) -> list[str]:
    activity_templates = [
        "Site mobilization", "Demolition of existing structures", "Earthworks",
        "Foundation works", "Substructure", "Superstructure",
        "Envelope and roofing", "MEP rough-in", "Internal partitions",
        "Finishes — flooring", "Finishes — painting", "MEP commissioning",
        "Final inspections", "Handover", "Operations stabilization",
    ]
    statuses = ["not_started", "in_progress", "completed", "delayed"]
    parties = ["Schuster Bau AG", "Vogel Architekten", "MEP-Planung Klein GmbH",
               "Wiegand Bau-Subunternehmen", "FM-Service Süd"]
    rows = []
    next_id = 1
    for project in PROJECTS:
        pid = project[0]
        base = date(2023, 6, 1) + timedelta(days=_rng.randint(0, 400))
        for i in range(_rng.randint(15, 30)):
            name = _rng.choice(activity_templates) + f" #{i + 1}"
            start_offset = _rng.randint(0, 540)
            duration = _rng.randint(7, 90)
            start = base + timedelta(days=start_offset)
            end = start + timedelta(days=duration)
            status = _rng.choice(statuses)
            progress = {
                "not_started": 0.0,
                "in_progress": round(_rng.uniform(10, 90), 1),
                "completed": 100.0,
                "delayed": round(_rng.uniform(20, 80), 1),
            }[status]
            party = _rng.choice(parties)
            rows.append(
                f"({next_id}, {pid}, {_s(name)}, DATE '{start}', DATE '{end}', "
                f"{progress}, {_s(status)}, {_s(party)})"
            )
            next_id += 1
    return [
        f"INSERT INTO {catalog}.{SCHEMA}.dt_schedule_activities "
        f"(id, project_id, name, start_date, end_date, progress_pct, status, responsible_party) VALUES\n"
        + ",\n".join(rows)
    ]


def _issue_inserts(catalog: str) -> list[str]:
    issue_templates = [
        ("Pipe-duct clash on level 3", "clash", "major"),
        ("Missing fire-rated penetration seal", "safety", "critical"),
        ("RFI: ceiling height in lobby", "rfi", "minor"),
        ("Concrete spalling in stair core", "defect", "moderate"),
        ("Owner-requested layout change", "change_request", "moderate"),
        ("Door swing conflicts with column", "design_issue", "minor"),
        ("HVAC duct routing requires re-coordination", "clash", "moderate"),
        ("Damaged window frame on facade", "defect", "minor"),
    ]
    statuses = ["open", "in_review", "in_progress", "resolved", "closed"]
    raisers = ["Anna Becker", "Tobias Lang", "Dr. Petra Vogel", "Markus Klein", "Marie Schulze"]
    rows = []
    next_id = 1
    for project in PROJECTS:
        pid = project[0]
        for _ in range(_rng.randint(8, 15)):
            title, category, severity = _rng.choice(issue_templates)
            status = _rng.choice(statuses)
            created_dt = datetime.now(timezone.utc) - timedelta(days=_rng.randint(1, 365))
            resolved_dt = (
                created_dt + timedelta(days=_rng.randint(2, 60))
                if status in ("resolved", "closed")
                else None
            )
            rows.append(
                f"({next_id}, {pid}, {_s(title)}, {_s(category)}, {_s(severity)}, "
                f"{_s(status)}, {_s(_rng.choice(raisers))}, {_ts(created_dt)}, {_ts(resolved_dt)})"
            )
            next_id += 1
    return [
        f"INSERT INTO {catalog}.{SCHEMA}.dt_issues "
        f"(id, project_id, title, category, severity, status, raised_by, created_at, resolved_at) VALUES\n"
        + ",\n".join(rows)
    ]


def _energy_inserts(catalog: str) -> list[str]:
    """30 days of daily aggregates per operating-project building."""
    rows = []
    next_id = 1
    operating = [(p[0], p[1]) for p in PROJECTS if p[5] == "operate"]
    operating_pids = {pid for pid, _ in operating}
    for pid, building_id, *_ in BUILDINGS:
        if pid not in operating_pids:
            continue
        code = next(p[1] for p in PROJECTS if p[0] == pid)
        for day_offset in range(30):
            period_start = datetime.now(timezone.utc) - timedelta(days=day_offset + 1)
            period_end = period_start + timedelta(days=1)
            kwh = round(_rng.uniform(800, 4500), 1)
            cost = round(kwh * _rng.uniform(0.18, 0.32), 2)
            rows.append(
                f"({next_id}, {building_id}, {_s(code)}, "
                f"{_s(f'M-{building_id:03d}-MAIN')}, {_ts(period_start)}, {_ts(period_end)}, "
                f"{kwh}, {cost})"
            )
            next_id += 1
    if not rows:
        return []
    return [
        f"INSERT INTO {catalog}.{SCHEMA}.dt_energy_consumption "
        f"(id, building_id, project_code, meter_code, period_start, period_end, kwh, cost_eur) VALUES\n"
        + ",\n".join(rows)
    ]


def _maintenance_inserts(catalog: str) -> list[str]:
    titles = [
        ("Quarterly HVAC filter replacement", "medium"),
        ("Elevator annual inspection", "high"),
        ("Lighting fixture replacement", "low"),
        ("Boiler pressure check", "high"),
        ("Chiller refrigerant top-up", "medium"),
        ("Fire alarm testing", "high"),
        ("Leak in 3rd floor washroom", "urgent"),
        ("Window seal replacement", "low"),
    ]
    statuses = ["open", "scheduled", "in_progress", "completed", "cancelled"]
    technicians = ["Klaus Berger", "Mehmet Yıldız", "Sara Müller", "Lukas Hoffmann"]
    rows = []
    next_id = 1
    operating_pids = {p[0] for p in PROJECTS if p[5] == "operate"}
    for project_id, building_id, *_ in BUILDINGS:
        if project_id not in operating_pids:
            continue
        for _ in range(_rng.randint(8, 18)):
            title, priority = _rng.choice(titles)
            status = _rng.choice(statuses)
            completed_offset = _rng.randint(1, 60) if status == "completed" else 0
            creation_offset = (
                completed_offset + _rng.randint(2, 30) if status == "completed"
                else _rng.randint(1, 90)
            )
            created_dt = datetime.now(timezone.utc) - timedelta(days=creation_offset)
            completed_dt = (
                datetime.now(timezone.utc) - timedelta(days=completed_offset)
                if status == "completed"
                else None
            )
            due = (
                date.today() + timedelta(days=_rng.randint(1, 60))
                if status != "completed"
                else date.today() - timedelta(days=_rng.randint(1, 90))
            )
            rows.append(
                f"({next_id}, {project_id}, {building_id}, {_s(title)}, {_s(priority)}, "
                f"{_s(status)}, {_s(_rng.choice(technicians))}, "
                f"DATE '{due}', {_ts(completed_dt)}, {_ts(created_dt)})"
            )
            next_id += 1
    if not rows:
        return []
    return [
        f"INSERT INTO {catalog}.{SCHEMA}.dt_maintenance_orders "
        f"(id, project_id, building_id, title, priority, status, assigned_technician, "
        f"due_date, completed_at, created_at) VALUES\n"
        + ",\n".join(rows)
    ]


def _utilization_inserts(catalog: str) -> list[str]:
    """7 days × ~30 spaces per operating project."""
    rows = []
    next_id = 1
    operating_pids = {p[0] for p in PROJECTS if p[5] == "operate"}
    # Synthesize space ids from a deterministic range — these match the
    # Lakebase seed where each operating building gets ~spaces_per_floor *
    # floors spaces. We don't import the Lakebase model; for UC analytics the
    # space id is just an opaque key.
    space_id = 1
    for project_id, building_id, _, _, floors, *_ in BUILDINGS:
        if project_id not in operating_pids:
            continue
        # ~10 spaces per floor as a reasonable proxy
        bldg_space_count = floors * 10
        bldg_space_ids = list(range(space_id, space_id + bldg_space_count))
        space_id += bldg_space_count
        sample = _rng.sample(bldg_space_ids, min(20, len(bldg_space_ids)))
        code = next(p[1] for p in PROJECTS if p[0] == project_id)
        for sid in sample:
            for day_offset in range(7):
                period_start = datetime.now(timezone.utc) - timedelta(days=day_offset + 1)
                period_end = period_start + timedelta(days=1)
                rows.append(
                    f"({next_id}, {sid}, {_s(code)}, {_ts(period_start)}, {_ts(period_end)}, "
                    f"{round(_rng.uniform(0.0, 95.0), 1)}, {_rng.randint(0, 40)})"
                )
                next_id += 1
    if not rows:
        return []
    return [
        f"INSERT INTO {catalog}.{SCHEMA}.dt_space_utilization "
        f"(id, space_id, project_code, period_start, period_end, occupancy_pct, peak_count) VALUES\n"
        + ",\n".join(rows)
    ]


def _sensor_readings_insert(catalog: str, target_rows: int = 500_000) -> list[str]:
    """Generate ``target_rows`` synthetic sensor readings server-side.

    Uses ``INSERT … SELECT FROM range(N)`` so the warehouse generates rows
    in-place rather than streaming hundreds of thousands of literals over
    the SQL API. Per-row variation comes from ``hash(id)`` and ``(id %
    N)`` style expressions — pseudo-random but cheap.
    """
    operating_buildings = [
        (b[1], b[0]) for b in BUILDINGS if b[0] in {p[0] for p in PROJECTS if p[5] == "operate"}
    ]
    if not operating_buildings:
        return []

    statements: list[str] = []
    sensors_per_building = 50  # operating-project sensors carry the bulk of readings
    rows_per_building = max(1, target_rows // (len(operating_buildings) * len(SENSOR_TYPES)))

    for building_id, project_id in operating_buildings:
        project_code = next(p[1] for p in PROJECTS if p[0] == project_id)
        for st_idx, (sensor_type, unit, lo, hi) in enumerate(SENSOR_TYPES):
            mid = (lo + hi) / 2.0
            amplitude = (hi - lo) / 2.0
            sql = f"""
INSERT INTO {catalog}.{SCHEMA}.dt_sensor_readings
    (sensor_code, sensor_type, project_code, building_id, space_id, reading_ts, value, unit)
SELECT
    CONCAT('S-', LPAD(CAST({building_id} AS STRING), 3, '0'), '-',
           LPAD(CAST(CAST(id % {sensors_per_building} + 1 AS BIGINT) AS STRING), 4, '0')) AS sensor_code,
    '{sensor_type}' AS sensor_type,
    '{project_code}' AS project_code,
    {building_id} AS building_id,
    CAST(((id % {sensors_per_building}) + ({building_id} - 1) * 100) AS BIGINT) AS space_id,
    CAST(date_sub(current_timestamp(), CAST(id / 96 AS INT)) AS TIMESTAMP) -
        INTERVAL '15' MINUTE * (id % 96) AS reading_ts,
    {mid} + {amplitude} * sin(id / 24.0) +
        ({amplitude * 0.2}) * (rand({(building_id * 31 + st_idx) % 1000}) - 0.5) AS value,
    '{unit}' AS unit
FROM range({rows_per_building})
""".strip()
            statements.append(sql)

    return statements


def build_sql(catalog: str = DEFAULT_CATALOG, target_sensor_rows: int = 500_000) -> list[str]:
    """Return all SQL statements (in order) to seed AECO Hub UC tables.

    Callers (the deploy script) drop+recreate the tables first using
    :mod:`uc_schema`, then run these inserts.
    """
    out: list[str] = []
    out.extend(_project_inserts(catalog))
    out.extend(_building_inserts(catalog))
    out.extend(_cost_inserts(catalog))
    out.extend(_schedule_inserts(catalog))
    out.extend(_issue_inserts(catalog))
    out.extend(_energy_inserts(catalog))
    out.extend(_maintenance_inserts(catalog))
    out.extend(_utilization_inserts(catalog))
    out.extend(_sensor_readings_insert(catalog, target_sensor_rows))
    return out


if __name__ == "__main__":
    stmts = build_sql()
    print(f"Generated {len(stmts)} SQL statements.")
    for i, stmt in enumerate(stmts, 1):
        print(f"--- Statement {i} ({len(stmt)} chars) ---")
        print(stmt[:200] + ("..." if len(stmt) > 200 else ""))
