"""Seed Unity Catalog tables for yard-pro with synthetic telemetry / Bronze
data so the Phase C demo's "analytical-pipeline" tour is visible.

Mirrors :mod:`backend.projects.mol_asm_cockpit.seed_uc_tables` (canonical
per-project UC seed pattern, plan §7 explicit reference) but uses the
server-side ``INSERT … SELECT FROM range(N)`` pattern from lessons §27
rather than PySpark ``createDataFrame`` — this script runs from anywhere
the Databricks SDK is installed, including a developer laptop, and does
not require a Spark session.

Tables seeded (canonical DDL in :mod:`scripts.uc_schema`):

  * ``yard_pro_bronze.telemetry_events`` — ~10k synthetic rows (event_type
    cycling through :class:`YardProTelemetryEventType`; occurred_at over
    the last 90 days; per-tool / per-yard scatter).
  * ``yard_pro_bronze.coach_transcripts`` — 30-50 representative rows
    (PII-flagged so the demo doesn't need volume).
  * ``yard_pro_bronze.diagnoses_raw`` — handful of representative rows
    mirroring the seeded Lakebase diagnoses.
  * ``yard_pro_silver.tool_health`` — single ``INSERT … SELECT`` rollup
    aggregating bronze telemetry per tool per day.
  * ``yard_pro_silver.yard_state`` — handful of yard-level snapshots.
  * ``yard_pro_gold.dealer_customer_summary`` — 5-10 anonymized aggregate
    rows so the Klaus / dealer-Genie tour has data on the Gold side.

Idempotency strategy: ``CREATE SCHEMA IF NOT EXISTS`` + ``DELETE FROM``
the target tables before re-seeding (mirrors the
``mol_asm_cockpit/seed_uc_tables.py`` "overwrite" semantics). The
``BIGINT GENERATED ALWAYS AS IDENTITY`` columns in the canonical DDL
recycle naturally on Delta IDENTITY columns; we don't drop the table,
so existing UC grants are preserved.

Catalog-parameterized via ``--catalog`` (lessons §28). The same script
runs against ``fevm-felix-demo`` (``felix_demo_catalog``) and any other
workspace.

CLI:

  python -m src.innovation_factory.backend.projects.yard_pro.seed_uc_tables \\
      --catalog felix_demo_catalog \\
      --workspace-url https://fevm-felix-demo.cloud.databricks.com
"""
from __future__ import annotations

import argparse
import os
import sys
from typing import Iterable

# Add repo root so `import scripts.uc_schema` works when run as a module
_REPO_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "..", "..", ".."))
if _REPO_ROOT not in sys.path:
    sys.path.insert(0, _REPO_ROOT)

from scripts import uc_schema  # noqa: E402

# Default catalog matches the AECO seed convention (lessons §28).
DEFAULT_CATALOG = os.getenv("YARD_PRO_UC_CATALOG", "innovation_factory_catalog")

SCHEMA_BRONZE = "yard_pro_bronze"
SCHEMA_SILVER = "yard_pro_silver"
SCHEMA_GOLD = "yard_pro_gold"

# Number of synthetic telemetry rows to seed. 10k is enough for the demo's
# analytical tour (per plan §12); the cost is a couple of seconds of warehouse
# time via the server-side range() pattern.
DEFAULT_TELEMETRY_ROWS = 10_000

# Telemetry event types — must match
# :class:`backend.projects.yard_pro.models.YardProTelemetryEventType`.
# Duplicating the values rather than importing the SQLModel module keeps
# this script importable in environments without sqlmodel (e.g. a Spark
# job runner).
TELEMETRY_EVENT_TYPES = [
    "battery_low",
    "maintenance_due",
    "stuck",
    "session_started",
    "session_ended",
]


# ---------------------------------------------------------------------------
# Schema creation helpers
# ---------------------------------------------------------------------------


def _create_schemas(ws, catalog: str, schemas: Iterable[str]) -> None:
    """Idempotently create the yard_pro schemas. Catches the
    ``SCHEMA_ALREADY_EXISTS`` exception so re-runs are safe.
    """
    for schema in schemas:
        try:
            ws.schemas.create(catalog_name=catalog, name=schema,
                              comment=f"yard-pro {schema.rsplit('_', 1)[-1]} tier")
            print(f"  Created schema {catalog}.{schema}")
        except Exception as exc:  # noqa: BLE001 — SDK raises a typed error here
            msg = str(exc).lower()
            if "already exists" in msg or "schema_already_exists" in msg:
                print(f"  Schema {catalog}.{schema} already exists")
            else:
                raise


def _run_sql(ws, statement: str, *, warehouse_id: str, label: str) -> None:
    """Execute a single SQL statement on the given warehouse and surface
    failures as exceptions (so a half-seeded UC catalog doesn't silently
    happen)."""
    from databricks.sdk.service.sql import StatementState

    result = ws.statement_execution.execute_statement(
        warehouse_id=warehouse_id,
        statement=statement,
        wait_timeout="50s",
    )
    state = result.status.state if result.status else None
    # Poll until finished if the warehouse didn't return synchronously.
    statement_id = result.statement_id
    while state in (StatementState.PENDING, StatementState.RUNNING) and statement_id:
        result = ws.statement_execution.get_statement(statement_id=statement_id)
        state = result.status.state if result.status else None
    if state == StatementState.FAILED:
        err = result.status.error.message if result.status and result.status.error else "?"
        raise RuntimeError(f"SQL FAILED ({label}): {err}")
    print(f"    [{label}] OK")


# ---------------------------------------------------------------------------
# Table creation (canonical DDL via uc_schema)
# ---------------------------------------------------------------------------


def _create_tables(ws, catalog: str, *, warehouse_id: str) -> None:
    """Create every ``yard_pro_*`` table via the canonical DDL.

    We use ``CREATE TABLE IF NOT EXISTS`` from :mod:`scripts.uc_schema`,
    which is the project-wide convention (lessons §23). The DELETE in
    ``_clear_tables`` handles idempotency; the table itself persists so
    UC grants survive re-seeds.
    """
    for schema_table in uc_schema.TABLES:
        if not schema_table.startswith(("yard_pro_bronze.", "yard_pro_silver.", "yard_pro_gold.")):
            continue
        ddl = uc_schema.create_table_sql(catalog, schema_table)
        _run_sql(ws, ddl, warehouse_id=warehouse_id, label=f"CREATE {schema_table}")


def _clear_tables(ws, catalog: str, *, warehouse_id: str) -> None:
    """DELETE rows so re-runs are idempotent without dropping the tables
    (preserves UC grants and any external references)."""
    for schema_table in uc_schema.TABLES:
        if not schema_table.startswith(("yard_pro_bronze.", "yard_pro_silver.", "yard_pro_gold.")):
            continue
        _run_sql(
            ws,
            f"DELETE FROM {catalog}.{schema_table}",
            warehouse_id=warehouse_id,
            label=f"DELETE {schema_table}",
        )


# ---------------------------------------------------------------------------
# Bronze: synthetic telemetry via INSERT … SELECT FROM range(N)
# ---------------------------------------------------------------------------


def _telemetry_insert_sql(catalog: str, num_rows: int) -> str:
    """Generate ~``num_rows`` synthetic telemetry events server-side.

    Lessons §27: ``INSERT … SELECT FROM range(N)`` keeps row-generation on
    the warehouse rather than streaming millions of SQL literals over the
    HTTP API. For 10k rows this is sub-second on a 2X-Small warehouse;
    for 1M+ rows it scales near-linearly.

    Each row scatters across:
      * 5 demo tools (tool_id 1..5 — matching the seeded Lakebase
        ``yp_tools`` rows so the analytical view lines up with what the
        cockpit shows)
      * 1 demo yard (yard_id = 1 — Martin's Stuttgart yard)
      * occurred_at over the last 90 days, evenly distributed
      * event_type cycled deterministically through
        :data:`TELEMETRY_EVENT_TYPES`
      * payload_json includes battery_pct and blade_hours so the silver
        rollup can derive something useful
    """
    n_events = len(TELEMETRY_EVENT_TYPES)
    # CASE expression mapping id % n_events to a specific event_type. Built
    # at SQL-codegen time so the warehouse executes a constant lookup, not
    # a multi-row UDF.
    event_case = "CASE " + " ".join(
        f"WHEN (id % {n_events}) = {i} THEN '{ev}'" for i, ev in enumerate(TELEMETRY_EVENT_TYPES)
    ) + " END"
    return f"""
INSERT INTO {catalog}.{SCHEMA_BRONZE}.telemetry_events
    (tool_id, yard_id, event_type, occurred_at, payload_json, ingested_at)
SELECT
    CAST((id % 5) + 1 AS BIGINT) AS tool_id,
    CAST(1 AS BIGINT) AS yard_id,
    {event_case} AS event_type,
    current_timestamp() - INTERVAL '90' DAY * (rand({42}) ) AS occurred_at,
    CONCAT(
        '{{"battery_pct": ', CAST(round(20 + 80 * rand({43}), 1) AS STRING),
        ', "blade_hours_since_sharpening": ',
        CAST(round(rand({44}) * 30.0, 1) AS STRING),
        ', "session_minutes": ',
        CAST(round(rand({45}) * 90.0, 1) AS STRING),
        '}}'
    ) AS payload_json,
    current_timestamp() AS ingested_at
FROM range({num_rows})
""".strip()


def _coach_transcripts_insert_sql(catalog: str) -> str:
    """Seed 40 representative coach transcript rows.

    These are small because they are PII-flagged (plan §5 retention rule):
    consent_flag=false rows hard-deleted at 30 days, consent_flag=true rows
    aggregated and deleted at 13 months. The demo doesn't need volume here
    — it needs *presence* in the analytical tier.
    """
    rows = []
    # Generate small natural-looking turn pairs.
    turn_templates = [
        ("user", "What should I do this weekend?", False),
        ("assistant", "It is mid-May in Stuttgart — apple-tree summer prune window is approaching. Light fruit-thinning and a base watering pass on the rose bed are the highest-leverage tasks. *Advisory only.*", True),
        ("user", "How do I tell apple scab apart from powdery mildew?", False),
        ("assistant", "Apple scab is dark, embedded, olive-brown lesions; powdery mildew is a white, powdery surface coating that wipes off. *Advisory only — second opinion suggested for low-confidence calls.*", True),
        ("user", "Is it time to prune my cherry tree?", False),
        ("assistant", "Never prune cherries in winter (silver-leaf risk). The correct window is late July through early September, in a dry week. *Advisory only.*", True),
        ("user", "When should I sharpen my hedge-trimmer blades?", False),
        ("assistant", "Hedge-trimmer blades typically need sharpening every 25-30 operating hours; sooner if you see torn leaf edges after a trim. *Advisory only.*", True),
    ]
    transcript_id = 0
    for session_idx in range(5):  # 5 sessions × 8 turns = 40 rows
        for role, content, is_rec in turn_templates:
            transcript_id += 1
            content_sql = "'" + content.replace("'", "''") + "'"
            rows.append(
                f"({session_idx + 1}, 1, '{role}', {content_sql}, "
                f"'databricks-meta-llama-3-3-70b', {'TRUE' if is_rec else 'FALSE'}, "
                f"TRUE, current_timestamp() - INTERVAL '{session_idx * 3}' DAY)"
            )
    return (
        f"INSERT INTO {catalog}.{SCHEMA_BRONZE}.coach_transcripts "
        f"(session_id, yard_id, role, content, model_version, is_recommendation, "
        f"consent_flag, created_at) VALUES\n"
        + ",\n".join(rows)
    )


def _diagnoses_raw_insert_sql(catalog: str) -> str:
    """Seed a handful of representative vision-diagnosis rows mirroring the
    Lakebase ``yp_diagnoses`` seed."""
    rows = [
        # (yard_id, photo_uri, model_version, top_label, top_confidence, predictions_json, days_ago)
        (1, "/Volumes/yard_pro/photos/1/lawn_yellow_patch.jpg", "yard-pro-vision-v1",
         "fusarium_blight_lawn", 0.82,
         '{"fusarium_blight_lawn": 0.82, "drought_stress": 0.11, "healthy": 0.07}', 1),
        (1, "/Volumes/yard_pro/photos/1/apple_leaf_spotted.jpg", "yard-pro-vision-v1",
         "apple_scab", 0.74,
         '{"apple_scab": 0.74, "powdery_mildew": 0.18, "healthy": 0.08}', 3),
        (1, "/Volumes/yard_pro/photos/1/rose_leaf_white.jpg", "yard-pro-vision-v1",
         "powdery_mildew", 0.69,
         '{"powdery_mildew": 0.69, "downy_mildew": 0.21, "healthy": 0.10}', 7),
        (1, "/Volumes/yard_pro/photos/1/box_webbing.jpg", "yard-pro-vision-v1",
         "boxwood_moth", 0.88,
         '{"boxwood_moth": 0.88, "boxwood_blight": 0.07, "healthy": 0.05}', 10),
        (1, "/Volumes/yard_pro/photos/1/healthy_lawn.jpg", "yard-pro-vision-v1",
         "healthy", 0.91,
         '{"healthy": 0.91, "drought_stress": 0.06, "fusarium_blight_lawn": 0.03}', 14),
    ]
    sql_rows = []
    for yard_id, photo_uri, model_version, top_label, top_conf, preds, days_ago in rows:
        preds_sql = "'" + preds.replace("'", "''") + "'"
        sql_rows.append(
            f"({yard_id}, '{photo_uri}', '{model_version}', '{top_label}', "
            f"{top_conf}, {preds_sql}, current_timestamp() - INTERVAL '{days_ago}' DAY)"
        )
    return (
        f"INSERT INTO {catalog}.{SCHEMA_BRONZE}.diagnoses_raw "
        f"(yard_id, photo_uri, model_version, top_label, top_confidence, "
        f"predictions_json, created_at) VALUES\n"
        + ",\n".join(sql_rows)
    )


# ---------------------------------------------------------------------------
# Silver: rollups derived from bronze
# ---------------------------------------------------------------------------


def _tool_health_insert_sql(catalog: str) -> str:
    """Aggregate the bronze telemetry into per-tool / per-day rollups.

    Single ``INSERT … SELECT`` — same pattern that Lakeflow Declarative
    Pipelines will take over in P4. Lessons §27 again: the warehouse does
    the work.
    """
    return f"""
INSERT INTO {catalog}.{SCHEMA_SILVER}.tool_health
    (tool_id, rollup_date, session_count, battery_low_events,
     maintenance_due_events, stuck_events, last_event_at, updated_at)
SELECT
    tool_id,
    CAST(occurred_at AS DATE) AS rollup_date,
    SUM(CASE WHEN event_type = 'session_started' THEN 1 ELSE 0 END) AS session_count,
    SUM(CASE WHEN event_type = 'battery_low' THEN 1 ELSE 0 END) AS battery_low_events,
    SUM(CASE WHEN event_type = 'maintenance_due' THEN 1 ELSE 0 END) AS maintenance_due_events,
    SUM(CASE WHEN event_type = 'stuck' THEN 1 ELSE 0 END) AS stuck_events,
    MAX(occurred_at) AS last_event_at,
    current_timestamp() AS updated_at
FROM {catalog}.{SCHEMA_BRONZE}.telemetry_events
GROUP BY tool_id, CAST(occurred_at AS DATE)
""".strip()


def _yard_state_insert_sql(catalog: str) -> str:
    """Per-yard daily snapshot — small, hand-built rows for the demo."""
    return f"""
INSERT INTO {catalog}.{SCHEMA_SILVER}.yard_state
    (yard_id, snapshot_date, plant_count, tool_count, action_count_30d,
     diagnosis_count_30d, updated_at)
SELECT
    1 AS yard_id,
    CAST(current_timestamp() - INTERVAL '{i}' DAY AS DATE) AS snapshot_date,
    12 AS plant_count,
    5 AS tool_count,
    {15 + i // 3} AS action_count_30d,
    {2 + (i % 3)} AS diagnosis_count_30d,
    current_timestamp() AS updated_at
FROM range(1)
""".strip().replace("{i}", "0")  # We'll do 1 row only — multi-row UNION below.


def _yard_state_insert_rows_sql(catalog: str) -> str:
    """7-day snapshot history for yard 1."""
    rows = []
    for day_offset in range(7):
        rows.append(
            f"(1, CAST(current_timestamp() - INTERVAL '{day_offset}' DAY AS DATE), "
            f"12, 5, {15 + day_offset // 3}, {2 + (day_offset % 3)}, current_timestamp())"
        )
    return (
        f"INSERT INTO {catalog}.{SCHEMA_SILVER}.yard_state "
        f"(yard_id, snapshot_date, plant_count, tool_count, action_count_30d, "
        f"diagnosis_count_30d, updated_at) VALUES\n"
        + ",\n".join(rows)
    )


# ---------------------------------------------------------------------------
# Gold: anonymized dealer-facing aggregates
# ---------------------------------------------------------------------------


def _dealer_customer_summary_insert_sql(catalog: str) -> str:
    """5-10 anonymized rows for the dealer panel's Genie space.

    No raw lat/lng, no names. ``yard_id_hash`` is the only join key; in
    P5 the real anonymization pipeline replaces this with a HMAC over
    yard_id keyed on a dealer-specific salt.
    """
    rows = [
        ("yh_a1b2c3", "dealer_stuttgart_nord", "DE-BW-stuttgart-basin", "small_200_500_m2", "th_typ_A", 3, 180, "granted"),
        ("yh_d4e5f6", "dealer_stuttgart_nord", "DE-BW-stuttgart-basin", "medium_500_1000_m2", "th_typ_B", 5, 90, "granted"),
        ("yh_g7h8i9", "dealer_stuttgart_nord", "DE-BW-stuttgart-basin", "small_200_500_m2", "th_typ_A", 2, 45, "granted"),
        ("yh_j0k1l2", "dealer_stuttgart_sued", "DE-BW-stuttgart-filder", "medium_500_1000_m2", "th_typ_C", 4, 300, "granted"),
        ("yh_m3n4o5", "dealer_stuttgart_sued", "DE-BW-stuttgart-filder", "large_1000_plus_m2", "th_typ_D", 6, 720, "granted"),
        ("yh_p6q7r8", "dealer_stuttgart_nord", "DE-BW-stuttgart-basin", "small_200_500_m2", "th_typ_A", 1, 30, "granted"),
        ("yh_s9t0u1", "dealer_stuttgart_west", "DE-BW-stuttgart-vaihingen", "medium_500_1000_m2", "th_typ_B", 4, 150, "granted"),
        ("yh_v2w3x4", "dealer_stuttgart_west", "DE-BW-stuttgart-vaihingen", "small_200_500_m2", "th_typ_A", 3, 60, "pending"),
    ]
    sql_rows = []
    for yard_id_hash, dealer_code, region, size_bucket, inv_hash, rm_age, last_svc, consent in rows:
        sql_rows.append(
            f"('{yard_id_hash}', '{dealer_code}', '{region}', '{size_bucket}', "
            f"'{inv_hash}', {rm_age}, {last_svc}, '{consent}', current_timestamp())"
        )
    return (
        f"INSERT INTO {catalog}.{SCHEMA_GOLD}.dealer_customer_summary "
        f"(yard_id_hash, dealer_code, region_bucket, yard_size_bucket, "
        f"tool_inventory_hash, robotic_mower_age_years, last_service_event_age_days, "
        f"consent_state, updated_at) VALUES\n"
        + ",\n".join(sql_rows)
    )


# ---------------------------------------------------------------------------
# Orchestrator
# ---------------------------------------------------------------------------


def seed_yard_pro_uc_tables(
    ws,
    catalog: str,
    *,
    schema_bronze: str = SCHEMA_BRONZE,
    schema_silver: str = SCHEMA_SILVER,
    schema_gold: str = SCHEMA_GOLD,
    warehouse_id: str | None = None,
    telemetry_rows: int = DEFAULT_TELEMETRY_ROWS,
) -> None:
    """Idempotently seed the yard-pro UC tables.

    Args:
        ws: An authenticated ``databricks.sdk.WorkspaceClient``.
        catalog: Target Unity Catalog name (e.g. ``felix_demo_catalog``).
            Lessons §28: every seed function takes catalog as the first
            argument so the same script runs across workspaces.
        schema_bronze / schema_silver / schema_gold: Override the schema
            names if you want to seed into an isolated test catalog. The
            canonical DDL still uses the fixed names, so overriding these
            without forking the DDL only works for selective deletes.
        warehouse_id: SQL warehouse to execute statements on. Falls back
            to ``YARD_PRO_WAREHOUSE_ID`` then ``WAREHOUSE_ID`` env vars.
        telemetry_rows: Row count for the synthetic bronze telemetry
            seed. Default 10_000 per plan §12.
    """
    warehouse_id = warehouse_id or os.getenv("YARD_PRO_WAREHOUSE_ID") or os.getenv("WAREHOUSE_ID")
    if not warehouse_id:
        raise RuntimeError(
            "warehouse_id is required (or set YARD_PRO_WAREHOUSE_ID / WAREHOUSE_ID env)"
        )

    print(f"== Seeding yard-pro UC tables into {catalog} (warehouse={warehouse_id}) ==")

    print("\n-- Step 1: create schemas --")
    _create_schemas(ws, catalog, [schema_bronze, schema_silver, schema_gold])

    print("\n-- Step 2: create tables (canonical DDL via scripts.uc_schema) --")
    _create_tables(ws, catalog, warehouse_id=warehouse_id)

    print("\n-- Step 3: clear existing rows (idempotent re-seed) --")
    _clear_tables(ws, catalog, warehouse_id=warehouse_id)

    print(f"\n-- Step 4: bronze telemetry ({telemetry_rows} rows via range(N)) --")
    _run_sql(
        ws,
        _telemetry_insert_sql(catalog, telemetry_rows),
        warehouse_id=warehouse_id,
        label=f"INSERT telemetry_events ({telemetry_rows} rows)",
    )

    print("\n-- Step 5: bronze coach transcripts (40 rows, consent_flag-marked) --")
    _run_sql(
        ws,
        _coach_transcripts_insert_sql(catalog),
        warehouse_id=warehouse_id,
        label="INSERT coach_transcripts",
    )

    print("\n-- Step 6: bronze diagnoses_raw (representative rows) --")
    _run_sql(
        ws,
        _diagnoses_raw_insert_sql(catalog),
        warehouse_id=warehouse_id,
        label="INSERT diagnoses_raw",
    )

    print("\n-- Step 7: silver tool_health rollup (INSERT … SELECT from bronze) --")
    _run_sql(
        ws,
        _tool_health_insert_sql(catalog),
        warehouse_id=warehouse_id,
        label="INSERT tool_health rollup",
    )

    print("\n-- Step 8: silver yard_state snapshot (7-day history) --")
    _run_sql(
        ws,
        _yard_state_insert_rows_sql(catalog),
        warehouse_id=warehouse_id,
        label="INSERT yard_state",
    )

    print("\n-- Step 9: gold dealer_customer_summary (anonymized aggregates) --")
    _run_sql(
        ws,
        _dealer_customer_summary_insert_sql(catalog),
        warehouse_id=warehouse_id,
        label="INSERT dealer_customer_summary",
    )

    print(f"\n== yard-pro UC seed complete for {catalog} ==")


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------


def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Seed yard-pro Unity Catalog tables (lessons §27 + §28)",
    )
    parser.add_argument(
        "--catalog",
        default=DEFAULT_CATALOG,
        help=f"Target UC catalog (default: {DEFAULT_CATALOG})",
    )
    parser.add_argument(
        "--workspace-url",
        default=None,
        help="Databricks workspace URL (e.g. https://fevm-felix-demo.cloud.databricks.com). "
             "If omitted, the SDK falls back to the default profile.",
    )
    parser.add_argument(
        "--profile",
        default=None,
        help="Databricks CLI profile name (alternative to --workspace-url).",
    )
    parser.add_argument(
        "--warehouse-id",
        default=None,
        help="SQL warehouse ID (default: env YARD_PRO_WAREHOUSE_ID or WAREHOUSE_ID)",
    )
    parser.add_argument(
        "--telemetry-rows",
        type=int,
        default=DEFAULT_TELEMETRY_ROWS,
        help=f"Bronze telemetry row count (default: {DEFAULT_TELEMETRY_ROWS})",
    )
    return parser.parse_args()


def main() -> None:
    args = _parse_args()
    from databricks.sdk import WorkspaceClient  # local import — heavy dep

    if args.profile:
        ws = WorkspaceClient(profile=args.profile)
    elif args.workspace_url:
        ws = WorkspaceClient(host=args.workspace_url)
    else:
        ws = WorkspaceClient()

    seed_yard_pro_uc_tables(
        ws,
        catalog=args.catalog,
        warehouse_id=args.warehouse_id,
        telemetry_rows=args.telemetry_rows,
    )


if __name__ == "__main__":
    main()
