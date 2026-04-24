"""Regression tests for HB Product Center dashboard summary.

The tile 500 traced back to `count_rows(ws, table, "status = 'active'")` —
passing a raw WHERE string as the 3rd positional argument after the
SQL-injection hardening changed that slot to `filters: dict | None`. The
string landed in `filters`, and `_build_where` exploded on
`filters.items()`.

These tests use a mock WorkspaceClient to record every SQL statement the
dashboard handler issues, then assert:
  1. No exception (the 500 reproducer).
  2. Every statement uses safe filter syntax, not raw WHERE interpolation
     of an unescaped string.
"""
from __future__ import annotations

import re

import pytest

from innovation_factory.backend.projects.hb_product_center.routers.dashboard import (
    get_dashboard_summary,
)


class _StmtStatus:
    def __init__(self, state):
        self.state = state
        self.error = None


class _StmtResult:
    def __init__(self, data_array):
        self.data_array = data_array


class _StmtResponse:
    def __init__(self, data_array):
        from databricks.sdk.service.sql import StatementState

        self.status = _StmtStatus(StatementState.SUCCEEDED)
        self.result = _StmtResult(data_array)
        self.manifest = None


class _MockStatementExecution:
    """Records every SQL statement and returns a canned single-value row.

    Distinguishes COUNT / AVG / SUM by SELECT clause so each metric resolves
    to a sensible numeric type.
    """

    def __init__(self) -> None:
        self.statements: list[str] = []

    def execute_statement(self, *, warehouse_id, statement, wait_timeout, **_kw):
        self.statements.append(statement)
        upper = statement.upper()
        if upper.startswith("SELECT COUNT"):
            value = 42
        elif "SELECT AVG" in upper:
            value = 7.5
        elif "SELECT SUM" in upper:
            value = 100.0
        else:
            value = None
        return _StmtResponse([[value]])


class _MockWs:
    def __init__(self) -> None:
        self.statement_execution = _MockStatementExecution()

    @property
    def api_client(self):  # some callers still reach for it; keep a stub
        return self.statement_execution


class TestDashboardSummary:
    def test_summary_does_not_pass_string_to_filters(self):
        """Regression: dashboard summary must not pass raw WHERE strings
        positionally. Pre-fix this raised:
          AttributeError: 'str' object has no attribute 'items'
        because `count_rows(ws, table, "status = 'active'")` landed in the
        `filters` kwarg after the SQL-injection hardening.
        """
        ws = _MockWs()
        result = get_dashboard_summary(ws)  # type: ignore[invalid-argument-type]  # mock ws

        # Sanity: every expected metric has a value.
        assert result.total_products == 42
        assert result.active_products == 42
        assert result.avg_quality_score == 7.5

        # Every statement that has a WHERE clause uses either:
        # - safe filters syntax (`{column} = {literal}`), or
        # - the deprecated where_raw path for inequalities (created_at >=,
        #   overall_score >). No statement should contain the broken
        #   `status = 'active'` as a *value* of a filter dict (which would
        #   have looked like `'status = 'active' = 'status = 'active''`).
        for sql in ws.statement_execution.statements:
            # The bug would produce doubled or malformed WHEREs; require
            # well-formed syntax.
            assert " WHERE " not in sql or re.search(
                r"WHERE\s+(\w+\s*(=|>|>=|<|<=)\s*('[^']*'|\d+))", sql
            ), f"malformed WHERE in: {sql}"

    def test_summary_uses_safe_filters_for_equality(self):
        """Equality filters are expressed through the safe `filters` dict,
        so the generated SQL escapes the value with single quotes."""
        ws = _MockWs()
        get_dashboard_summary(ws)  # type: ignore[invalid-argument-type]  # mock ws

        joined = "\n".join(ws.statement_execution.statements)
        # Each of these should appear exactly as a WHERE clause with a
        # single-quoted value.
        assert "status = 'active'" in joined
        assert "status = 'pending'" in joined
        assert "status = 'verified'" in joined
        assert "resolution = 'open'" in joined

    def test_summary_covers_all_kpi_tables(self):
        """Every UC table the dashboard needs is queried at least once."""
        ws = _MockWs()
        get_dashboard_summary(ws)  # type: ignore[invalid-argument-type]  # mock ws

        joined = "\n".join(ws.statement_execution.statements).lower()
        for table in (
            "hb_products",
            "hb_recognition_jobs",
            "hb_quality_inspections",
            "hb_auth_verifications",
            "hb_auth_alerts",
            "hb_supply_chain_events",
            "hb_sustainability_metrics",
        ):
            assert table in joined, f"dashboard summary didn't query {table}"
