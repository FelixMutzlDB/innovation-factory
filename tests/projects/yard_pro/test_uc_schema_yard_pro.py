"""Schema-shape tests for yard-pro Unity Catalog tables.

Lessons §23 declares ``scripts/uc_schema.py::TABLES`` the single source
of truth for UC DDL. yard-pro's bronze/silver/gold tables land in P0 in
the same dict; these tests assert presence and canonical-field shape
so that ``seed_uc_tables.py`` and ``deploy_ka.py`` can rely on the
table definitions without re-validating at runtime.
"""
from __future__ import annotations

import importlib.util
import pathlib
import sys


def _load_uc_schema():
    """Mirrors the loader pattern from ``tests/scripts/test_uc_schema.py``
    so this file is independent of import order."""
    repo_root = pathlib.Path(__file__).resolve().parents[3]
    path = repo_root / "scripts" / "uc_schema.py"
    spec = importlib.util.spec_from_file_location("uc_schema_yp", path)
    assert spec and spec.loader
    mod = importlib.util.module_from_spec(spec)
    sys.modules["uc_schema_yp"] = mod
    spec.loader.exec_module(mod)
    return mod


YARD_PRO_BRONZE_TABLES = {
    "yard_pro_bronze.telemetry_events",
    "yard_pro_bronze.diagnoses_raw",
    "yard_pro_bronze.coach_transcripts",
}

YARD_PRO_SILVER_TABLES = {
    "yard_pro_silver.tool_health",
    "yard_pro_silver.yard_state",
}

YARD_PRO_GOLD_TABLES = {
    "yard_pro_gold.dealer_customer_summary",
}

ALL_YARD_PRO_TABLES = (
    YARD_PRO_BRONZE_TABLES | YARD_PRO_SILVER_TABLES | YARD_PRO_GOLD_TABLES
)


class TestYardProSchemasPresent:
    def test_three_yard_pro_schemas(self):
        """Bronze / Silver / Gold all registered in TABLES."""
        mod = _load_uc_schema()
        schemas = set(mod.schemas())
        assert "yard_pro_bronze" in schemas
        assert "yard_pro_silver" in schemas
        assert "yard_pro_gold" in schemas

    def test_all_six_tables_present(self):
        """The exact six tables called out in plan §5 + §12 P0 list."""
        mod = _load_uc_schema()
        registered = set(mod.TABLES.keys())
        missing = ALL_YARD_PRO_TABLES - registered
        assert not missing, f"Missing yard-pro UC table entries: {sorted(missing)}"


class TestBronzeFields:
    """Canonical bronze-tier fields per plan §5."""

    def test_telemetry_events_canonical_fields(self):
        mod = _load_uc_schema()
        cols = {c[0] for c in mod.TABLES["yard_pro_bronze.telemetry_events"]["columns"]}
        # These are the columns seed_uc_tables.py and the silver rollup
        # depend on; missing any breaks the demo's analytical pipeline.
        for required in ("tool_id", "yard_id", "event_type", "occurred_at"):
            assert required in cols, (
                f"telemetry_events missing canonical field {required!r}"
            )

    def test_coach_transcripts_carries_consent_flag(self):
        """Plan §8 + §5: consent_flag=false rows hard-deleted at 30d."""
        mod = _load_uc_schema()
        cols = dict(mod.TABLES["yard_pro_bronze.coach_transcripts"]["columns"])
        assert "consent_flag" in cols, (
            "coach_transcripts must carry consent_flag (plan §8 retention rail)"
        )
        assert cols["consent_flag"] == "BOOLEAN", (
            f"consent_flag must be BOOLEAN; got {cols['consent_flag']}"
        )

    def test_diagnoses_raw_canonical_fields(self):
        mod = _load_uc_schema()
        cols = {c[0] for c in mod.TABLES["yard_pro_bronze.diagnoses_raw"]["columns"]}
        for required in ("yard_id", "photo_uri", "model_version",
                         "top_label", "top_confidence"):
            assert required in cols, (
                f"diagnoses_raw missing canonical field {required!r}"
            )


class TestSilverFields:
    def test_tool_health_canonical_fields(self):
        mod = _load_uc_schema()
        cols = {c[0] for c in mod.TABLES["yard_pro_silver.tool_health"]["columns"]}
        for required in ("tool_id", "rollup_date", "session_count",
                         "battery_low_events"):
            assert required in cols, (
                f"tool_health missing canonical field {required!r}"
            )

    def test_yard_state_canonical_fields(self):
        mod = _load_uc_schema()
        cols = {c[0] for c in mod.TABLES["yard_pro_silver.yard_state"]["columns"]}
        for required in ("yard_id", "snapshot_date", "plant_count", "tool_count"):
            assert required in cols, (
                f"yard_state missing canonical field {required!r}"
            )


class TestGoldFields:
    def test_dealer_summary_has_no_raw_pii_columns(self):
        """Plan §8 access-control row: gold table never carries raw lat/lng
        or display_name. The only join key is ``yard_id_hash``."""
        mod = _load_uc_schema()
        cols = {c[0] for c in mod.TABLES["yard_pro_gold.dealer_customer_summary"]["columns"]}
        forbidden = {"lat", "lng", "display_name", "yard_id", "user_key"}
        leaks = cols & forbidden
        assert not leaks, (
            f"dealer_customer_summary leaks raw PII columns: {sorted(leaks)}"
        )
        assert "yard_id_hash" in cols, (
            "dealer_customer_summary must use yard_id_hash as the (only) join key"
        )

    def test_dealer_summary_carries_consent_state(self):
        """Plan §8 consent-state row: gold aggregator reads consent_state
        on every batch."""
        mod = _load_uc_schema()
        cols = {c[0] for c in mod.TABLES["yard_pro_gold.dealer_customer_summary"]["columns"]}
        assert "consent_state" in cols, (
            "dealer_customer_summary must carry consent_state for the "
            "aggregation pipeline (plan §8)"
        )


class TestDdlGeneration:
    """``seed_uc_tables.py`` and ``deploy_ka.py`` both call
    ``uc_schema.create_table_sql()``; verify the generated DDL is
    well-formed for every yard-pro table."""

    def test_create_sql_well_formed_for_every_yard_pro_table(self):
        mod = _load_uc_schema()
        for schema_table in ALL_YARD_PRO_TABLES:
            sql = mod.create_table_sql("test_catalog", schema_table)
            assert sql.startswith("CREATE TABLE IF NOT EXISTS"), (
                f"DDL for {schema_table} missing CREATE TABLE preamble"
            )
            assert f"test_catalog.{schema_table}" in sql, (
                f"DDL for {schema_table} doesn't reference catalog correctly"
            )

    def test_tables_for_schema_yields_expected_subsets(self):
        mod = _load_uc_schema()
        assert set(mod.tables_for_schema("yard_pro_bronze").keys()) \
            == YARD_PRO_BRONZE_TABLES
        assert set(mod.tables_for_schema("yard_pro_silver").keys()) \
            == YARD_PRO_SILVER_TABLES
        assert set(mod.tables_for_schema("yard_pro_gold").keys()) \
            == YARD_PRO_GOLD_TABLES
