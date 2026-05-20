"""Canonical Unity Catalog schema definitions — single source of truth.

Every seeder / deployer (``scripts/deploy_agents_fevm.py``,
``scripts/seed_uc_hb_data.py``, ``scripts/seed_all_uc_notebook.py``, the
archived ``scripts/archive/migrate_full.py``) should import from this
module rather than defining tables inline. Before this module, six
separate files carried overlapping and slightly divergent DDL for the
same tables (type mismatches on ``product_id``, ``last_audit_date``
DATE vs TIMESTAMP, ``id`` as auto-increment vs supplied by INSERT, etc.).

## Structure

``TABLES`` is a dict keyed by ``"<schema>.<table>"`` so callers can
prepend the target catalog at runtime and reuse the same definition
across workspaces with different catalog names. Each entry declares:

  * ``columns`` — list of ``(name, type)`` tuples in authoring order
  * ``comment`` — optional table comment

Helpers:

  * :func:`create_table_sql` — generate CREATE TABLE IF NOT EXISTS for
    one table at the given catalog
  * :func:`create_all_sql` — iterator over DDL for every table
  * :func:`tables_for_schema` — filter TABLES by schema prefix
"""
from __future__ import annotations

from typing import Iterator


# -----------------------------------------------------------------------------
# Column type conventions
# -----------------------------------------------------------------------------
# - ID columns: `BIGINT GENERATED ALWAYS AS IDENTITY` so INSERT statements
#   don't need to supply the id, and the value is a 64-bit integer.
# - Timestamps: always TIMESTAMP (includes time component). Use DATE only
#   for truly date-only semantics like `sale_date`, `metric_date`,
#   `last_audit_date`.
# - Money / metric values: DOUBLE.
# - Counts: INT (32-bit is plenty for row-level metric counters).
# - Impressions: BIGINT (can exceed 2.1B for a large advertiser).
# - Booleans: BOOLEAN.
# - String catch-all: STRING (no length constraint in UC; callers cap via
#   their Pydantic models — see backend/input_sanitize.py).
# -----------------------------------------------------------------------------

TABLES: dict[str, dict] = {
    # =========================================================================
    # HB Product Center (schema: hb_product_center)
    # =========================================================================
    "hb_product_center.hb_products": {
        "columns": [
            ("id", "BIGINT GENERATED ALWAYS AS IDENTITY"),
            ("sku", "STRING"),
            ("style_name", "STRING"),
            ("color", "STRING"),
            ("color_code", "STRING"),
            ("size", "STRING"),
            ("category", "STRING"),
            ("collection", "STRING"),
            ("season", "STRING"),
            ("material", "STRING"),
            ("price", "DOUBLE"),
            ("status", "STRING"),
            ("country_of_origin", "STRING"),
            ("supplier_name", "STRING"),
            ("created_at", "TIMESTAMP"),
        ],
        "comment": "HB fashion product catalog.",
    },
    "hb_product_center.hb_recognition_jobs": {
        "columns": [
            ("id", "BIGINT GENERATED ALWAYS AS IDENTITY"),
            ("job_type", "STRING"),
            ("status", "STRING"),
            ("user_role", "STRING"),
            ("submitted_by", "STRING"),
            ("image_count", "INT"),
            ("completed_count", "INT"),
            ("created_at", "TIMESTAMP"),
            ("completed_at", "TIMESTAMP"),
        ],
        "comment": "Visual recognition jobs submitted via HB's CLIP pipeline.",
    },
    "hb_product_center.hb_quality_inspections": {
        "columns": [
            ("id", "BIGINT GENERATED ALWAYS AS IDENTITY"),
            ("product_id", "BIGINT"),
            ("batch_number", "STRING"),
            ("inspector", "STRING"),
            ("manufacturing_partner", "STRING"),
            ("overall_score", "DOUBLE"),
            ("status", "STRING"),
            ("notes", "STRING"),
            ("created_at", "TIMESTAMP"),
            ("completed_at", "TIMESTAMP"),
        ],
        "comment": "Quality-control inspections for HB products.",
    },
    "hb_product_center.hb_quality_defects": {
        "columns": [
            ("id", "BIGINT GENERATED ALWAYS AS IDENTITY"),
            ("inspection_id", "BIGINT"),
            ("defect_type", "STRING"),
            ("severity", "STRING"),
            ("location_description", "STRING"),
            ("confidence_score", "DOUBLE"),
            ("image_url", "STRING"),
            ("created_at", "TIMESTAMP"),
        ],
        "comment": "Individual defects found within a quality inspection.",
    },
    "hb_product_center.hb_auth_verifications": {
        "columns": [
            ("id", "BIGINT GENERATED ALWAYS AS IDENTITY"),
            ("product_id", "BIGINT"),
            ("requester_type", "STRING"),
            ("requester_name", "STRING"),
            ("requester_email", "STRING"),
            ("status", "STRING"),
            ("confidence_score", "DOUBLE"),
            ("verification_method", "STRING"),
            ("image_url", "STRING"),
            ("region", "STRING"),
            ("notes", "STRING"),
            ("created_at", "TIMESTAMP"),
            ("completed_at", "TIMESTAMP"),
        ],
        "comment": "Authenticity verification requests for HB products.",
    },
    "hb_product_center.hb_auth_alerts": {
        "columns": [
            ("id", "BIGINT GENERATED ALWAYS AS IDENTITY"),
            ("verification_id", "BIGINT"),
            ("alert_type", "STRING"),
            ("severity", "STRING"),
            ("region", "STRING"),
            ("description", "STRING"),
            ("investigated_by", "STRING"),
            ("resolution", "STRING"),
            ("created_at", "TIMESTAMP"),
        ],
        "comment": "Counterfeit / authenticity alerts derived from verifications.",
    },
    "hb_product_center.hb_supply_chain_events": {
        "columns": [
            ("id", "BIGINT GENERATED ALWAYS AS IDENTITY"),
            ("product_id", "BIGINT"),
            ("event_type", "STRING"),
            ("location", "STRING"),
            ("partner_name", "STRING"),
            ("country", "STRING"),
            ("details", "STRING"),
            ("event_date", "TIMESTAMP"),
            ("created_at", "TIMESTAMP"),
        ],
        "comment": "Supply-chain events tracked along the HB product journey.",
    },
    "hb_product_center.hb_sustainability_metrics": {
        "columns": [
            ("id", "BIGINT GENERATED ALWAYS AS IDENTITY"),
            ("product_id", "BIGINT"),
            ("carbon_footprint_kg", "DOUBLE"),
            ("water_usage_liters", "DOUBLE"),
            ("recycled_content_pct", "DOUBLE"),
            ("organic_material_pct", "DOUBLE"),
            ("certifications", "STRING"),
            ("compliance_status", "STRING"),
            # DATE not TIMESTAMP — we only care about the audit day.
            ("last_audit_date", "DATE"),
            ("created_at", "TIMESTAMP"),
        ],
        "comment": "Sustainability audit metrics per product.",
    },

    # =========================================================================
    # AdTech Intelligence (schema: adtech_intelligence)
    # =========================================================================
    "adtech_intelligence.advertisers": {
        "columns": [
            ("id", "INT"),
            ("name", "STRING"),
            ("industry", "STRING"),
            ("contact_name", "STRING"),
            ("contact_email", "STRING"),
            ("budget_tier", "STRING"),
            ("created_at", "TIMESTAMP"),
        ],
        "comment": "Advertiser profiles.",
    },
    "adtech_intelligence.campaigns": {
        "columns": [
            ("id", "INT"),
            ("advertiser_id", "INT"),
            ("name", "STRING"),
            ("campaign_type", "STRING"),
            ("status", "STRING"),
            ("budget", "DOUBLE"),
            ("spent", "DOUBLE"),
            ("start_date", "DATE"),
            ("end_date", "DATE"),
            ("target_audience", "STRING"),
        ],
        "comment": "Advertising campaigns by advertiser.",
    },
    "adtech_intelligence.ad_inventory": {
        "columns": [
            ("id", "INT"),
            ("name", "STRING"),
            ("inventory_type", "STRING"),
            ("location_type", "STRING"),
            ("city", "STRING"),
            ("region", "STRING"),
            ("daily_impressions_est", "INT"),
            ("cpm_rate", "DOUBLE"),
            ("status", "STRING"),
            ("ad_format", "STRING"),
            ("media_owner", "STRING"),
        ],
        "comment": "Available ad slots / inventory units.",
    },
    "adtech_intelligence.performance_metrics": {
        "columns": [
            ("id", "INT"),
            ("campaign_id", "INT"),
            ("inventory_id", "INT"),
            ("metric_date", "DATE"),
            ("impressions", "BIGINT"),
            ("clicks", "INT"),
            ("ctr", "DOUBLE"),
            ("conversions", "INT"),
            ("spend", "DOUBLE"),
            ("viewability_rate", "DOUBLE"),
        ],
        "comment": "Per-day per-placement performance metrics.",
    },
    "adtech_intelligence.anomalies": {
        "columns": [
            ("id", "INT"),
            ("campaign_id", "INT"),
            ("anomaly_type", "STRING"),
            ("severity", "STRING"),
            ("title", "STRING"),
            ("description", "STRING"),
            ("status", "STRING"),
            ("metric_name", "STRING"),
            ("expected_value", "DOUBLE"),
            ("actual_value", "DOUBLE"),
            ("deviation_pct", "DOUBLE"),
            ("detected_at", "TIMESTAMP"),
        ],
        "comment": "Detected performance anomalies.",
    },
    "adtech_intelligence.issues": {
        "columns": [
            ("id", "INT"),
            ("campaign_id", "INT"),
            ("advertiser_id", "INT"),
            ("title", "STRING"),
            ("description", "STRING"),
            ("category", "STRING"),
            ("status", "STRING"),
            ("priority", "STRING"),
            ("assigned_to", "STRING"),
            ("created_at", "TIMESTAMP"),
            ("resolved_at", "TIMESTAMP"),
        ],
        "comment": "Support tickets for advertiser account management.",
    },
    "adtech_intelligence.customer_contracts": {
        "columns": [
            ("id", "INT"),
            ("advertiser_id", "INT"),
            ("contract_number", "STRING"),
            ("start_date", "DATE"),
            ("end_date", "DATE"),
            ("total_value", "DOUBLE"),
            ("status", "STRING"),
            ("payment_terms", "STRING"),
            ("signed_at", "TIMESTAMP"),
        ],
        "comment": "Signed contracts with advertisers.",
    },

    # =========================================================================
    # MOL ASM Cockpit (schema: mac)
    # =========================================================================
    "mac.stations": {
        "columns": [
            ("id", "INT"),
            ("station_code", "STRING"),
            ("name", "STRING"),
            ("city", "STRING"),
            ("region", "STRING"),
            ("country", "STRING"),
            ("latitude", "DOUBLE"),
            ("longitude", "DOUBLE"),
            ("station_type", "STRING"),
            ("has_fresh_corner", "BOOLEAN"),
            ("has_ev_charging", "BOOLEAN"),
            ("num_pumps", "INT"),
            ("shop_area_sqm", "DOUBLE"),
        ],
        "comment": "Retail fuel / service-station locations.",
    },
    "mac.fuel_sales": {
        "columns": [
            ("station_id", "INT"),
            ("sale_date", "DATE"),
            ("fuel_type", "STRING"),
            ("volume_liters", "DOUBLE"),
            ("revenue", "DOUBLE"),
            ("unit_price", "DOUBLE"),
            ("margin", "DOUBLE"),
        ],
        "comment": "Daily fuel sales per station per fuel type.",
    },
    "mac.nonfuel_sales": {
        "columns": [
            ("station_id", "INT"),
            ("sale_date", "DATE"),
            ("category", "STRING"),
            ("quantity", "INT"),
            ("revenue", "DOUBLE"),
            ("margin", "DOUBLE"),
        ],
        "comment": "Daily non-fuel product sales (shop + fresh corner).",
    },
    "mac.workforce_shifts": {
        "columns": [
            ("station_id", "INT"),
            ("shift_date", "DATE"),
            ("shift_type", "STRING"),
            ("planned_headcount", "INT"),
            ("actual_headcount", "INT"),
            ("overtime_hours", "DOUBLE"),
        ],
        "comment": "Workforce shifts per station per day.",
    },
    "mac.inventory": {
        "columns": [
            ("station_id", "INT"),
            ("record_date", "DATE"),
            ("product_category", "STRING"),
            ("stock_level", "INT"),
            ("reorder_point", "INT"),
            ("spoilage_count", "INT"),
            ("stock_out_events", "INT"),
            ("delivery_scheduled", "BOOLEAN"),
        ],
        "comment": "Daily inventory snapshot per station per category.",
    },
    "mac.competitor_prices": {
        "columns": [
            ("station_id", "INT"),
            ("price_date", "DATE"),
            ("competitor_name", "STRING"),
            ("fuel_type", "STRING"),
            ("price_per_liter", "DOUBLE"),
        ],
        "comment": "Observed competitor fuel prices near each station.",
    },
    "mac.price_history": {
        "columns": [
            ("station_id", "INT"),
            ("price_date", "DATE"),
            ("fuel_type", "STRING"),
            ("price_per_liter", "DOUBLE"),
            ("cost_per_liter", "DOUBLE"),
        ],
        "comment": "Our own fuel price history per station.",
    },
    "mac.loyalty_metrics": {
        "columns": [
            ("station_id", "INT"),
            ("month", "DATE"),
            ("active_members", "INT"),
            ("new_signups", "INT"),
            ("points_redeemed", "INT"),
            ("loyalty_revenue_share", "DOUBLE"),
        ],
        "comment": "Monthly loyalty program metrics per station.",
    },
    "mac.anomaly_alerts": {
        "columns": [
            ("id", "INT"),
            ("station_id", "INT"),
            ("metric_type", "STRING"),
            ("severity", "STRING"),
            ("title", "STRING"),
            ("description", "STRING"),
            ("suggested_action", "STRING"),
            ("status", "STRING"),
            ("detected_at", "TIMESTAMP"),
        ],
        "comment": "Anomaly alerts surfaced to the ASM cockpit.",
    },

    # =========================================================================
    # AECO Hub (schema: aeco_hub)
    # =========================================================================
    # UC mirror of the Lakebase ``dt_*`` tables for Genie + Lakeview dashboards.
    # Sensor *readings* are UC-only (too large for PGlite). Other tables are
    # subset projections of the Lakebase rows that show up in analytics.
    "aeco_hub.dt_projects": {
        "columns": [
            ("id", "BIGINT"),
            ("code", "STRING"),
            ("name", "STRING"),
            ("client_name", "STRING"),
            ("city", "STRING"),
            ("country", "STRING"),
            ("phase", "STRING"),
            ("status", "STRING"),
            ("progress_pct", "DOUBLE"),
            ("budget_eur", "DOUBLE"),
            ("actual_cost_eur", "DOUBLE"),
            ("start_date", "DATE"),
            ("target_completion_date", "DATE"),
        ],
        "comment": "AECO Hub construction projects (UC mirror of Lakebase dt_projects).",
    },
    "aeco_hub.dt_buildings": {
        "columns": [
            ("id", "BIGINT"),
            ("project_id", "BIGINT"),
            ("name", "STRING"),
            ("building_type", "STRING"),
            ("floor_count", "INT"),
            ("gross_floor_area_sqm", "DOUBLE"),
            ("year_built", "INT"),
            ("city", "STRING"),
        ],
        "comment": "Buildings within AECO Hub projects.",
    },
    "aeco_hub.dt_cost_items": {
        "columns": [
            ("id", "BIGINT"),
            ("project_id", "BIGINT"),
            ("code", "STRING"),
            ("description", "STRING"),
            ("category", "STRING"),
            ("estimated_eur", "DOUBLE"),
            ("actual_eur", "DOUBLE"),
            ("status", "STRING"),
        ],
        "comment": "Bill-of-quantities cost items per project.",
    },
    "aeco_hub.dt_schedule_activities": {
        "columns": [
            ("id", "BIGINT"),
            ("project_id", "BIGINT"),
            ("name", "STRING"),
            ("start_date", "DATE"),
            ("end_date", "DATE"),
            ("progress_pct", "DOUBLE"),
            ("status", "STRING"),
            ("responsible_party", "STRING"),
        ],
        "comment": "Construction schedule activities.",
    },
    "aeco_hub.dt_issues": {
        "columns": [
            ("id", "BIGINT"),
            ("project_id", "BIGINT"),
            ("title", "STRING"),
            ("category", "STRING"),
            ("severity", "STRING"),
            ("status", "STRING"),
            ("raised_by", "STRING"),
            ("created_at", "TIMESTAMP"),
            ("resolved_at", "TIMESTAMP"),
        ],
        "comment": "Cross-discipline issues (clashes, RFIs, defects, change requests).",
    },
    "aeco_hub.dt_sensor_readings": {
        "columns": [
            ("reading_id", "BIGINT GENERATED ALWAYS AS IDENTITY"),
            ("sensor_code", "STRING"),
            ("sensor_type", "STRING"),
            ("project_code", "STRING"),
            ("building_id", "BIGINT"),
            ("space_id", "BIGINT"),
            ("reading_ts", "TIMESTAMP"),
            ("value", "DOUBLE"),
            ("unit", "STRING"),
        ],
        "comment": "IoT sensor time-series — building automation feeds for operating projects.",
    },
    "aeco_hub.dt_energy_consumption": {
        "columns": [
            ("id", "BIGINT"),
            ("building_id", "BIGINT"),
            ("project_code", "STRING"),
            ("meter_code", "STRING"),
            ("period_start", "TIMESTAMP"),
            ("period_end", "TIMESTAMP"),
            ("kwh", "DOUBLE"),
            ("cost_eur", "DOUBLE"),
        ],
        "comment": "Aggregated daily energy per meter for operating buildings.",
    },
    "aeco_hub.dt_maintenance_orders": {
        "columns": [
            ("id", "BIGINT"),
            ("project_id", "BIGINT"),
            ("building_id", "BIGINT"),
            ("title", "STRING"),
            ("priority", "STRING"),
            ("status", "STRING"),
            ("assigned_technician", "STRING"),
            ("due_date", "DATE"),
            ("completed_at", "TIMESTAMP"),
            ("created_at", "TIMESTAMP"),
        ],
        "comment": "Facility-management maintenance orders.",
    },
    "aeco_hub.dt_space_utilization": {
        "columns": [
            ("id", "BIGINT"),
            ("space_id", "BIGINT"),
            ("project_code", "STRING"),
            ("period_start", "TIMESTAMP"),
            ("period_end", "TIMESTAMP"),
            ("occupancy_pct", "DOUBLE"),
            ("peak_count", "INT"),
        ],
        "comment": "Daily occupancy / utilization per space.",
    },

    # =========================================================================
    # yard-pro Bronze (schema: yard_pro_bronze)
    # =========================================================================
    # Raw analytical tier. Lakehouse Sync (Lakebase yp_* → Delta) lands here in
    # P4; in P0 we seed ~10k synthetic rows server-side via
    # ``INSERT … SELECT FROM range(N)`` (lessons §27) so the demo's
    # "analytical-pipeline tour" is visible. PII-bearing tables
    # (``coach_transcripts``) carry a ``consent_flag`` column; rows with
    # ``consent_flag=false`` are excluded from any analytical query (plan §8).
    "yard_pro_bronze.telemetry_events": {
        "columns": [
            ("event_id", "BIGINT GENERATED ALWAYS AS IDENTITY"),
            ("tool_id", "BIGINT"),
            ("yard_id", "BIGINT"),
            ("event_type", "STRING"),
            ("occurred_at", "TIMESTAMP"),
            ("payload_json", "STRING"),
            ("ingested_at", "TIMESTAMP"),
        ],
        "comment": "Raw connected-tool telemetry events (battery/blade/usage). Delta partitioned by date(occurred_at); 90-day raw retention per plan §5.",
    },
    "yard_pro_bronze.diagnoses_raw": {
        "columns": [
            ("diagnosis_id", "BIGINT GENERATED ALWAYS AS IDENTITY"),
            ("yard_id", "BIGINT"),
            ("photo_uri", "STRING"),
            ("model_version", "STRING"),
            ("top_label", "STRING"),
            ("top_confidence", "DOUBLE"),
            ("predictions_json", "STRING"),
            ("created_at", "TIMESTAMP"),
        ],
        "comment": "Snap-and-diagnose vision predictions (UC3) mirrored from Lakebase yp_diagnoses for analytics. Photos themselves live in UC Volume yard_pro/photos/<yard_id>/.",
    },
    "yard_pro_bronze.coach_transcripts": {
        "columns": [
            ("transcript_id", "BIGINT GENERATED ALWAYS AS IDENTITY"),
            ("session_id", "BIGINT"),
            ("yard_id", "BIGINT"),
            ("role", "STRING"),
            ("content", "STRING"),
            ("model_version", "STRING"),
            ("is_recommendation", "BOOLEAN"),
            ("consent_flag", "BOOLEAN"),
            ("created_at", "TIMESTAMP"),
        ],
        "comment": "Coach chat transcripts (UC2). PII-bearing; consent_flag=false rows hard-deleted at 30d, consent_flag=true rows aggregated and deleted at 13mo (GDPR purpose limitation).",
    },

    # =========================================================================
    # yard-pro Silver (schema: yard_pro_silver)
    # =========================================================================
    # Per-tool / per-yard rollups derived from Bronze. Seeded from Bronze via a
    # single INSERT … SELECT aggregate in P0; Lakeflow declarative pipelines
    # take over in P4.
    "yard_pro_silver.tool_health": {
        "columns": [
            ("tool_id", "BIGINT"),
            ("rollup_date", "DATE"),
            ("session_count", "INT"),
            ("battery_low_events", "INT"),
            ("maintenance_due_events", "INT"),
            ("stuck_events", "INT"),
            ("last_event_at", "TIMESTAMP"),
            ("updated_at", "TIMESTAMP"),
        ],
        "comment": "Per-tool daily telemetry KPIs rolled up from yard_pro_bronze.telemetry_events.",
    },
    "yard_pro_silver.yard_state": {
        "columns": [
            ("yard_id", "BIGINT"),
            ("snapshot_date", "DATE"),
            ("plant_count", "INT"),
            ("tool_count", "INT"),
            ("action_count_30d", "INT"),
            ("diagnosis_count_30d", "INT"),
            ("updated_at", "TIMESTAMP"),
        ],
        "comment": "Per-yard daily state snapshot (plant / tool / activity counts) for cockpit summaries.",
    },

    # =========================================================================
    # yard-pro Gold (schema: yard_pro_gold)
    # =========================================================================
    # Dealer-facing, anonymized aggregate view. UC grants exclude all yp_* and
    # yard_pro_bronze.* / yard_pro_silver.* tables from the dealer SP. Genie
    # space in P5 reads from here only. No raw lat/lng or names — see plan §8
    # access-control row "Klaus only sees yard_pro_gold.*".
    "yard_pro_gold.dealer_customer_summary": {
        "columns": [
            ("summary_id", "BIGINT GENERATED ALWAYS AS IDENTITY"),
            ("yard_id_hash", "STRING"),
            ("dealer_code", "STRING"),
            ("region_bucket", "STRING"),
            ("yard_size_bucket", "STRING"),
            ("tool_inventory_hash", "STRING"),
            ("robotic_mower_age_years", "INT"),
            ("last_service_event_age_days", "INT"),
            ("consent_state", "STRING"),
            ("updated_at", "TIMESTAMP"),
        ],
        "comment": "Anonymized per-household summary for the dealer Genie space (UC6, P5). Never carries raw PII; yard_id_hash is the only join key.",
    },
}


def create_table_sql(catalog: str, schema_table: str) -> str:
    """Return the full ``CREATE TABLE IF NOT EXISTS`` statement for
    *schema_table* in the given catalog.

    Raises KeyError if the table isn't in :data:`TABLES`.
    """
    spec = TABLES[schema_table]
    cols = ",\n    ".join(f"{name} {typ}" for name, typ in spec["columns"])
    comment = spec.get("comment")
    comment_clause = f" COMMENT '{comment}'" if comment else ""
    schema, table = schema_table.split(".", 1)
    return (
        f"CREATE TABLE IF NOT EXISTS {catalog}.{schema}.{table} (\n"
        f"    {cols}\n"
        f"){comment_clause}"
    )


def create_all_sql(catalog: str) -> Iterator[str]:
    """Yield ``CREATE TABLE IF NOT EXISTS`` DDL for every canonical table."""
    for schema_table in TABLES:
        yield create_table_sql(catalog, schema_table)


def tables_for_schema(schema: str) -> dict[str, dict]:
    """Return the subset of TABLES whose name starts with ``{schema}.``."""
    prefix = f"{schema}."
    return {k: v for k, v in TABLES.items() if k.startswith(prefix)}


def schemas() -> list[str]:
    """Return a sorted list of distinct schemas referenced by TABLES."""
    return sorted({key.split(".", 1)[0] for key in TABLES})
