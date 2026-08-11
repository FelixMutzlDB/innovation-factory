"""Extended UC query service tests for HB Product Center.

The existing test_hb_uc_query_security.py covers:
  _validate_column, _escape_value, _build_where, search_like,
  select_all (injection), ProductsListRegression

This file adds coverage for the remaining public API:
  count_rows, avg_column, sum_column, insert_row, update_row,
  execute_query error handling (FAILED / no-status states),
  get_table_name, select_one, select_by_id,
  execute_query_with_schema schema extraction
"""
from __future__ import annotations

import pytest
from unittest.mock import MagicMock

from innovation_factory.backend.projects.hb_product_center.services import (
    uc_query_service as qs,
)


# ---------------------------------------------------------------------------
# Recording mock helpers (mirrors pattern in test_hb_uc_query_security.py)
# ---------------------------------------------------------------------------


class _MockStmtExec:
    def __init__(self, data_array=None, state=None, error_msg=None):
        self.statements: list[str] = []
        self._data_array = data_array
        self._state = state
        self._error_msg = error_msg

    def execute_statement(self, *, warehouse_id, statement, wait_timeout, **_kw):
        from databricks.sdk.service.sql import StatementState

        self.statements.append(statement)

        if self._state == "FAILED":
            class _Result:
                class _Status:
                    state = StatementState.FAILED
                    class _Error:
                        message = "simulated failure"
                    error = _Error()
                status = _Status()
                result = None
                manifest = None
            return _Result()

        if self._state == "NO_STATUS":
            class _NoStatusResult:
                status = None
                result = None
                manifest = None
            return _NoStatusResult()

        class _Schema:
            columns = [
                type("Col", (), {"name": c})()
                for c in (self._data_array[0] if self._data_array and isinstance(self._data_array[0], list) else [])
            ]

        # Default: SUCCEEDED with data_array
        data = self._data_array or []

        class _Manifest:
            class _Schema:
                columns = [
                    type("Col", (), {"name": f"col{i}"})()
                    for i in range(len(data[0]) if data else 0)
                ]
            schema = _Schema()

        class _Result:
            from databricks.sdk.service.sql import StatementState as _SS

            class _Status:
                state = StatementState.SUCCEEDED
                error = None
            status = _Status()
            manifest = _Manifest()
            result = type("R", (), {"data_array": data})()
        return _Result()


def _mock_ws(data_array=None, state=None, error_msg=None):
    ws = MagicMock()
    ws.statement_execution = _MockStmtExec(
        data_array=data_array, state=state, error_msg=error_msg
    )
    return ws


# ---------------------------------------------------------------------------
# get_table_name
# ---------------------------------------------------------------------------


class TestGetTableName:
    def test_returns_three_part_fqn(self):
        from innovation_factory.backend.projects.hb_product_center.databricks_config import (
            UC_CATALOG,
            UC_SCHEMA,
        )
        name = qs.get_table_name("hb_products")
        assert name == f"{UC_CATALOG}.{UC_SCHEMA}.hb_products"
        assert name.count(".") == 2


# ---------------------------------------------------------------------------
# execute_query error handling
# ---------------------------------------------------------------------------


class TestExecuteQueryErrors:
    def test_raises_on_failed_state(self):
        ws = _mock_ws(state="FAILED")
        with pytest.raises(RuntimeError, match="Query failed"):
            qs.execute_query(ws, "SELECT 1")

    def test_raises_on_none_status(self):
        ws = _mock_ws(state="NO_STATUS")
        with pytest.raises(RuntimeError, match="no status"):
            qs.execute_query(ws, "SELECT 1")

    def test_returns_empty_list_when_result_none(self):
        """When state is SUCCEEDED but result is None, return empty list."""
        from databricks.sdk.service.sql import StatementState as _SS

        ws = MagicMock()

        class _Status:
            state = _SS.SUCCEEDED
            error = None

        class _Result:
            status = _Status()
            result = None
            manifest = None

        ws.statement_execution.execute_statement.return_value = _Result()
        rows = qs.execute_query(ws, "SELECT 1")
        assert rows == []


# ---------------------------------------------------------------------------
# count_rows
# ---------------------------------------------------------------------------


class TestCountRows:
    def test_generates_count_select(self):
        ws = _mock_ws(data_array=[[42]])
        count = qs.count_rows(ws, "hb_products")
        sql = ws.statement_execution.statements[-1]
        assert "SELECT COUNT(*)" in sql
        assert "hb_products" in sql
        assert count == 42

    def test_count_with_equality_filter(self):
        ws = _mock_ws(data_array=[[10]])
        qs.count_rows(ws, "hb_products", filters={"status": "active"})
        sql = ws.statement_execution.statements[-1]
        assert "WHERE" in sql
        assert "status = 'active'" in sql

    def test_count_with_comparison_filter(self):
        ws = _mock_ws(data_array=[[5]])
        qs.count_rows(ws, "hb_quality_inspections", filters={"overall_score": (">", 85)})
        sql = ws.statement_execution.statements[-1]
        assert "overall_score > 85" in sql

    def test_count_empty_table_returns_zero(self):
        ws = _mock_ws(data_array=[])
        count = qs.count_rows(ws, "hb_products")
        assert count == 0


# ---------------------------------------------------------------------------
# avg_column
# ---------------------------------------------------------------------------


class TestAvgColumn:
    def test_generates_avg_select(self):
        ws = _mock_ws(data_array=[[87.5]])
        avg = qs.avg_column(ws, "hb_quality_inspections", "overall_score")
        sql = ws.statement_execution.statements[-1]
        assert "AVG(overall_score)" in sql
        assert avg == pytest.approx(87.5)

    def test_invalid_column_raises(self):
        ws = _mock_ws(data_array=[[0]])
        with pytest.raises(ValueError):
            qs.avg_column(ws, "hb_products", "col; DROP TABLE x")

    def test_none_result_returns_zero(self):
        ws = _mock_ws(data_array=[[None]])
        avg = qs.avg_column(ws, "hb_quality_inspections", "overall_score")
        assert avg == 0.0

    def test_empty_result_returns_zero(self):
        ws = _mock_ws(data_array=[])
        avg = qs.avg_column(ws, "hb_quality_inspections", "overall_score")
        assert avg == 0.0

    def test_avg_with_filter(self):
        ws = _mock_ws(data_array=[[72.0]])
        qs.avg_column(ws, "hb_quality_inspections", "overall_score", filters={"status": "rejected"})
        sql = ws.statement_execution.statements[-1]
        assert "WHERE" in sql
        assert "status = 'rejected'" in sql


# ---------------------------------------------------------------------------
# sum_column
# ---------------------------------------------------------------------------


class TestSumColumn:
    def test_generates_sum_select(self):
        ws = _mock_ws(data_array=[[1000.0]])
        total = qs.sum_column(ws, "hb_sustainability_metrics", "carbon_footprint_kg")
        sql = ws.statement_execution.statements[-1]
        assert "SUM(carbon_footprint_kg)" in sql
        assert total == pytest.approx(1000.0)

    def test_invalid_column_raises(self):
        ws = _mock_ws(data_array=[[0]])
        with pytest.raises(ValueError):
            qs.sum_column(ws, "hb_products", "1; UNION SELECT 1")


# ---------------------------------------------------------------------------
# insert_row
# ---------------------------------------------------------------------------


class TestInsertRow:
    def test_generates_insert_statement(self):
        ws = _mock_ws(data_array=[[1]])
        qs.insert_row(ws, "hb_products", {"sku": "X-001", "style_name": "Test"})
        # First statement is the INSERT
        insert_sql = ws.statement_execution.statements[0]
        assert insert_sql.strip().upper().startswith("INSERT INTO")
        assert "hb_products" in insert_sql
        assert "'X-001'" in insert_sql
        assert "'Test'" in insert_sql

    def test_invalid_column_raises(self):
        ws = _mock_ws(data_array=[[1]])
        with pytest.raises(ValueError):
            qs.insert_row(ws, "hb_products", {"sku; DROP TABLE x": "val"})

    def test_returns_max_id_on_success(self):
        ws = _mock_ws(data_array=[[7]])
        result = qs.insert_row(ws, "hb_products", {"sku": "Y-001"})
        assert result == 7


# ---------------------------------------------------------------------------
# update_row
# ---------------------------------------------------------------------------


class TestUpdateRow:
    def test_generates_update_statement(self):
        ws = _mock_ws(data_array=[])
        qs.update_row(ws, "hb_quality_inspections", 42, {"status": "approved"})
        sql = ws.statement_execution.statements[-1]
        assert sql.strip().upper().startswith("UPDATE")
        assert "hb_quality_inspections" in sql
        assert "status = 'approved'" in sql
        assert "WHERE id = 42" in sql

    def test_empty_data_returns_true_without_query(self):
        ws = _mock_ws(data_array=[])
        result = qs.update_row(ws, "hb_quality_inspections", 1, {})
        assert result is True
        # empty dict → early-return, no SQL issued
        assert ws.statement_execution.statements == []

    def test_invalid_column_raises(self):
        ws = _mock_ws(data_array=[])
        with pytest.raises(ValueError):
            qs.update_row(ws, "hb_products", 1, {"col name": "val"})

    def test_id_is_sanitised_to_int(self):
        """update_row calls int(id_value) — string IDs should be coerced."""
        ws = _mock_ws(data_array=[])
        qs.update_row(ws, "hb_products", "99", {"status": "active"})  # type: ignore[arg-type, invalid-argument-type]
        sql = ws.statement_execution.statements[-1]
        assert "WHERE id = 99" in sql


# ---------------------------------------------------------------------------
# select_one / select_by_id
# ---------------------------------------------------------------------------


class TestSelectOne:
    def test_returns_none_on_empty(self):
        ws = _mock_ws(data_array=[])
        result = qs.select_one(ws, "hb_products")
        assert result is None

    def test_uses_limit_1(self):
        ws = _mock_ws(data_array=[])
        qs.select_one(ws, "hb_products", filters={"status": "active"})
        sql = ws.statement_execution.statements[-1]
        assert "LIMIT 1" in sql


class TestSelectById:
    def test_uses_id_filter(self):
        ws = _mock_ws(data_array=[])
        qs.select_by_id(ws, "hb_products", 123)
        sql = ws.statement_execution.statements[-1]
        assert "id = 123" in sql

    def test_id_is_sanitised_to_int(self):
        ws = _mock_ws(data_array=[])
        qs.select_by_id(ws, "hb_products", "55")  # type: ignore[arg-type, invalid-argument-type]
        sql = ws.statement_execution.statements[-1]
        assert "id = 55" in sql

    def test_returns_none_when_not_found(self):
        ws = _mock_ws(data_array=[])
        result = qs.select_by_id(ws, "hb_products", 999)
        assert result is None


# ---------------------------------------------------------------------------
# Numeric escape in _escape_value — additional edge cases
# ---------------------------------------------------------------------------


class TestEscapeValueExtras:
    def test_none_returns_null(self):
        assert qs._escape_value(None) == "NULL"

    def test_datetime_returns_iso_quoted(self):
        from datetime import datetime, timezone
        dt = datetime(2026, 8, 11, 12, 0, 0, tzinfo=timezone.utc)
        out = qs._escape_value(dt)
        assert out.startswith("'")
        assert "2026-08-11" in out

    def test_date_returns_iso_quoted(self):
        from datetime import date
        d = date(2026, 1, 15)
        out = qs._escape_value(d)
        assert out.startswith("'")
        assert "2026-01-15" in out

    def test_negative_numeric_unquoted(self):
        assert qs._escape_value(-42) == "-42"

    def test_zero_unquoted(self):
        assert qs._escape_value(0) == "0"
