"""SQL-injection regression tests for the HB Product Center UC query layer.

UC Statement Execution does not support bind parameters, so every
injection vector must be closed inside
``services/uc_query_service.py``. The module now enforces:

  * ``_validate_column`` — regex allowlist for identifiers
  * ``_escape_value`` — escapes ``'``, ``%``, ``_``, ``\\``, drops null bytes
  * ``_escape_like`` — same as above for LIKE patterns
  * No ``where_raw`` / ``order_by_raw`` / ``where`` / ``order_by`` kwargs
    — only ``filters={}`` (equality / comparison tuples) and
    ``search_like(columns=[...], term=...)``

These tests use a recording mock so we can inspect the SQL that *would*
be executed without needing a live Databricks warehouse.
"""
from __future__ import annotations

import re

import pytest

from innovation_factory.backend.projects.hb_product_center.services import (
    uc_query_service as qs,
)


# ---------------------------------------------------------------------------
# Recording mock
# ---------------------------------------------------------------------------


class _MockStmtExec:
    def __init__(self) -> None:
        self.statements: list[str] = []

    def execute_statement(self, *, warehouse_id, statement, wait_timeout, **_kw):
        from databricks.sdk.service.sql import StatementState

        self.statements.append(statement)

        class _Result:
            class _Status:
                state = StatementState.SUCCEEDED
                error = None

            status = _Status()
            result = type("R", (), {"data_array": [[0]]})()
            manifest = None

        return _Result()


class _MockWs:
    def __init__(self) -> None:
        self.statement_execution = _MockStmtExec()


# ---------------------------------------------------------------------------
# Column allowlist
# ---------------------------------------------------------------------------


class TestValidateColumn:
    @pytest.mark.parametrize(
        "bad",
        [
            "col; DROP TABLE users",
            "col' OR '1'='1",
            "1col",
            "col-name",
            "",
            "col name",
            "col/**/",
            "col\n",
            "`col`",
            "col;",
        ],
    )
    def test_rejects_unsafe(self, bad):
        with pytest.raises(ValueError):
            qs._validate_column(bad)

    @pytest.mark.parametrize("ok", ["col", "_col", "col_1", "COL", "a1_b2"])
    def test_accepts_safe(self, ok):
        assert qs._validate_column(ok) == ok


# ---------------------------------------------------------------------------
# Escape value
# ---------------------------------------------------------------------------


class TestEscapeValue:
    @pytest.mark.parametrize(
        "payload",
        [
            "normal string",
            "with 'single' quotes",
            "wild%card_%_",
            "back\\slash",
            "tab\there",
        ],
    )
    def test_returns_quoted_and_escaped(self, payload):
        out = qs._escape_value(payload)
        # Always wrapped in single quotes
        assert out.startswith("'") and out.endswith("'")
        # No unescaped single quote inside the value (doubled is fine)
        inner = out[1:-1]
        # Every single quote must be part of '' pair
        i = 0
        while i < len(inner):
            c = inner[i]
            if c == "'":
                assert i + 1 < len(inner) and inner[i + 1] == "'", (
                    f"unescaped single quote in {out!r}"
                )
                i += 2
            else:
                i += 1

    def test_drops_null_bytes(self):
        out = qs._escape_value("before\x00after")
        assert "\x00" not in out

    @pytest.mark.parametrize("numeric", [42, 3.14, -1, 0])
    def test_numeric_unquoted(self, numeric):
        assert qs._escape_value(numeric) == str(numeric)

    def test_bool_unquoted(self):
        assert qs._escape_value(True) == "TRUE"
        assert qs._escape_value(False) == "FALSE"


# ---------------------------------------------------------------------------
# Build-where contract
# ---------------------------------------------------------------------------


class TestBuildWhere:
    def test_empty(self):
        assert qs._build_where(None) == ""
        assert qs._build_where({}) == ""

    def test_equality_shorthand(self):
        out = qs._build_where({"status": "active"})
        assert out == "status = 'active'"

    def test_comparison_tuple(self):
        out = qs._build_where({"created_at": (">=", "2026-04-01")})
        assert out == "created_at >= '2026-04-01'"

    def test_rejects_bad_operator(self):
        # an op not in the allowed set is treated as a scalar and escaped —
        # ensuring we never inject an operator we didn't vet.
        out = qs._build_where({"col": ("SELECT *", "x")})
        # the tuple falls through to the equality path and stringifies
        assert "SELECT" not in out.split("=")[0]

    def test_rejects_bad_column(self):
        with pytest.raises(ValueError):
            qs._build_where({"col; DROP": "x"})


# ---------------------------------------------------------------------------
# Payload-driven injection attempts
# ---------------------------------------------------------------------------


PAYLOADS = [
    "'; DROP TABLE hb_products; --",
    "' OR '1'='1",
    "a%' OR '1'='1",             # the LIKE-wildcard-bypass regression
    "a_' UNION SELECT * FROM users",
    "\\' OR 1=1 --",
    "\x00' OR 1",                # null byte
    "/* comment */ OR 1=1",
    "'; INSERT INTO hb_products VALUES(1); --",
]


def _is_inside_quoted_literal(sql: str, idx: int) -> bool:
    """Is character *idx* inside a single-quoted string literal?

    Counts unescaped single quotes before *idx*; odd count → inside.
    Treats '' as one doubled quote (stays on whichever side we started).
    """
    i = 0
    inside = False
    while i < idx:
        ch = sql[i]
        if ch == "'":
            # peek for doubled quote → that's an escaped quote within a literal
            if i + 1 < len(sql) and sql[i + 1] == "'":
                i += 2
                continue
            inside = not inside
        i += 1
    return inside


def _all_dangerous_keywords_are_literal(sql: str) -> bool:
    """Every occurrence of dangerous SQL keywords must sit inside a
    single-quoted literal (i.e. an escaped payload, not a SQL keyword)."""
    upper = sql.upper()
    for kw in ("DROP TABLE", "UNION SELECT", "INSERT INTO", "UPDATE ",
               "DELETE FROM", "--", "/*"):
        start = 0
        while True:
            idx = upper.find(kw, start)
            if idx < 0:
                break
            if not _is_inside_quoted_literal(sql, idx):
                return False
            start = idx + len(kw)
    return True


class TestInjectionPayloads:
    @pytest.mark.parametrize("payload", PAYLOADS)
    def test_search_like_escapes(self, payload):
        ws = _MockWs()
        qs.search_like(ws, "hb_products", ["style_name", "sku"], term=payload, limit=5)  # type: ignore[invalid-argument-type]  # mock ws
        sql = ws.statement_execution.statements[-1]

        # Our LIKE ESCAPE clause is present so the backslash-escape
        # strategy actually works.
        assert " ESCAPE '\\\\'" in sql, f"missing ESCAPE clause in: {sql}"

        # Any dangerous keyword that appears must be inside a
        # single-quoted literal (i.e. the payload was neutered).
        assert _all_dangerous_keywords_are_literal(sql), (
            f"dangerous keyword escaped the quoted literal in: {sql}"
        )

        # The WHERE clause still wraps the LIKE conditions in
        # parentheses — the payload can't close the group early.
        where_match = re.search(r"WHERE (.+?) (?:ORDER|LIMIT)", sql)
        assert where_match is not None, f"no WHERE…LIMIT in {sql}"
        assert where_match.group(1).strip().startswith("("), (
            f"LIKE conditions not parenthesised: {sql}"
        )

    @pytest.mark.parametrize("payload", PAYLOADS)
    def test_select_all_equality_escapes(self, payload):
        ws = _MockWs()
        qs.select_all(ws, "hb_products", filters={"status": payload}, limit=5)  # type: ignore[invalid-argument-type]  # mock ws
        sql = ws.statement_execution.statements[-1]

        # Every dangerous keyword (if present at all) must sit inside a
        # single-quoted literal.
        assert _all_dangerous_keywords_are_literal(sql), (
            f"dangerous keyword escaped the quoted literal in: {sql}"
        )

        # The WHERE must remain one equality on `status`; any top-level
        # boolean operator would mean the payload broke out of the literal.
        where_match = re.search(r"WHERE (.+?) LIMIT", sql)
        assert where_match is not None, f"no WHERE…LIMIT in {sql}"
        where = where_match.group(1).strip()

        # Find the first `=` at the top level (outside quotes). Everything
        # after the `=` should be one balanced single-quoted literal.
        eq_idx = -1
        inside = False
        for i, ch in enumerate(where):
            if ch == "'":
                if i + 1 < len(where) and where[i + 1] == "'":
                    continue
                inside = not inside
            elif ch == "=" and not inside:
                eq_idx = i
                break
        assert eq_idx >= 0, f"no top-level `=` in {where!r}"
        rhs = where[eq_idx + 1:].strip()
        assert rhs.startswith("'") and rhs.endswith("'"), (
            f"RHS of equality must be one quoted literal; got: {rhs!r}"
        )


# ---------------------------------------------------------------------------
# The regression that started Batch B
# ---------------------------------------------------------------------------


class TestProductsListRegression:
    """The list_products endpoint was the original vector: it built
    LIKE search + equality filters by raw f-string concatenation. After
    refactor it must go through search_like + filters.
    """

    def test_search_with_wildcard_bypass_is_neutered(self):
        ws = _MockWs()
        payload = "a%' OR '1'='1"
        qs.search_like(
            ws,  # type: ignore[invalid-argument-type]  # mock ws
            "hb_products", ["style_name", "sku"],
            term=payload, filters={"category": "suits"}, limit=5,
        )
        sql = ws.statement_execution.statements[-1]
        # The payload's wildcard (%) is escaped.
        assert "\\%" in sql
        # The payload's single quote is doubled.
        assert "''" in sql
        # The filter is ANDed with the search — it can't be clobbered by
        # an unclosed-quote injection.
        assert "category = 'suits'" in sql
        assert " AND " in sql
