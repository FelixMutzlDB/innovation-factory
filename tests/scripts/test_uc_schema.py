"""Tests for scripts/uc_schema.py — the canonical UC DDL source.

D2 consolidated the scattered CREATE TABLE statements (6+ files, some
with subtle divergence) into one place. These tests lock down the
schema surface so an accidental divergence in a future seeder gets
caught at CI time instead of at deploy time.
"""
from __future__ import annotations

import importlib.util
import pathlib
import re
import sys


def _load_uc_schema():
    repo_root = pathlib.Path(__file__).resolve().parents[2]
    path = repo_root / "scripts" / "uc_schema.py"
    spec = importlib.util.spec_from_file_location("uc_schema", path)
    assert spec and spec.loader
    mod = importlib.util.module_from_spec(spec)
    sys.modules["uc_schema"] = mod
    spec.loader.exec_module(mod)
    return mod


class TestSchemaSurface:
    def test_tables_cover_three_schemas(self):
        mod = _load_uc_schema()
        assert set(mod.schemas()) == {
            "adtech_intelligence",
            "hb_product_center",
            "mac",
        }

    def test_every_table_has_columns_and_at_least_one_id_or_pk_like(self):
        mod = _load_uc_schema()
        for name, spec in mod.TABLES.items():
            assert spec["columns"], f"{name} has no columns"
            # Every table has either an `id`, a `station_id`, or some
            # composite key column. Sanity-check that we don't ship a
            # table with ONLY string columns — almost certainly a bug.
            col_names = {col[0] for col in spec["columns"]}
            assert col_names & {
                "id", "station_id", "product_id", "campaign_id",
                "inspection_id", "verification_id", "advertiser_id",
                "inventory_id",
            }, f"{name} has no identifier column"

    def test_column_names_are_safe_identifiers(self):
        """Regression for SQL-injection-adjacent concerns: no weird
        characters in column names (whitespace, quotes, semicolons)."""
        mod = _load_uc_schema()
        safe = re.compile(r"^[a-z_][a-z0-9_]*$")
        for name, spec in mod.TABLES.items():
            for col_name, _ in spec["columns"]:
                assert safe.match(col_name), (
                    f"{name} has unsafe column name: {col_name!r}"
                )

    def test_id_columns_are_numeric(self):
        """Every column ending in ``_id`` is an integer type, not STRING."""
        mod = _load_uc_schema()
        for name, spec in mod.TABLES.items():
            for col_name, col_type in spec["columns"]:
                if col_name == "id" or col_name.endswith("_id"):
                    assert any(
                        t in col_type.upper() for t in ("INT", "BIGINT")
                    ), f"{name}.{col_name} is {col_type!r}; expected INT/BIGINT"


class TestCreateTableSql:
    def test_includes_catalog_schema_table(self):
        mod = _load_uc_schema()
        sql = mod.create_table_sql("felix_demo_catalog", "hb_product_center.hb_products")
        assert "felix_demo_catalog.hb_product_center.hb_products" in sql
        assert "CREATE TABLE IF NOT EXISTS" in sql

    def test_includes_every_column(self):
        mod = _load_uc_schema()
        spec = mod.TABLES["hb_product_center.hb_products"]
        sql = mod.create_table_sql("c", "hb_product_center.hb_products")
        for col_name, col_type in spec["columns"]:
            assert f"{col_name} {col_type}" in sql, (
                f"{col_name} {col_type} missing from generated DDL"
            )

    def test_comment_is_emitted_when_set(self):
        mod = _load_uc_schema()
        sql = mod.create_table_sql("c", "hb_product_center.hb_products")
        # Every HB table has a comment; verify the COMMENT clause
        # is syntactically present.
        assert " COMMENT 'HB fashion product catalog.'" in sql

    def test_missing_table_raises(self):
        mod = _load_uc_schema()
        try:
            mod.create_table_sql("c", "nonexistent.table")
        except KeyError:
            pass
        else:
            raise AssertionError("expected KeyError for missing table")


class TestCreateAllSql:
    def test_yields_one_per_table(self):
        mod = _load_uc_schema()
        stmts = list(mod.create_all_sql("c"))
        assert len(stmts) == len(mod.TABLES)
        for stmt in stmts:
            assert stmt.startswith("CREATE TABLE IF NOT EXISTS ")


class TestTablesForSchema:
    def test_filters_by_prefix(self):
        mod = _load_uc_schema()
        adtech = mod.tables_for_schema("adtech_intelligence")
        assert set(adtech.keys()) == {
            "adtech_intelligence.advertisers",
            "adtech_intelligence.campaigns",
            "adtech_intelligence.ad_inventory",
            "adtech_intelligence.performance_metrics",
            "adtech_intelligence.anomalies",
            "adtech_intelligence.issues",
            "adtech_intelligence.customer_contracts",
        }

    def test_unknown_schema_returns_empty(self):
        mod = _load_uc_schema()
        assert mod.tables_for_schema("nonexistent") == {}
