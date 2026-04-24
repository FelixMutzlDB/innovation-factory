"""Unity Catalog query service for HB Product Center.

Uses Databricks SQL Statement Execution API to query UC tables instead of
Lakebase. This ensures consistent access via the app's Service Principal
identity.

## Safety contract

UC Statement Execution does not support bind parameters. Every public
function in this module builds SQL by interpolation, so the **only** way
to interpolate anything is via:

  * ``filters={"col": value}``      — equality predicate
  * ``filters={"col": (op, value)}`` — comparison predicate (``op`` ∈
    ``{"=", "!=", ">", ">=", "<", "<="}``)
  * ``order_by_column="col"``       — validated identifier
  * ``search_like(columns=[...])``  — escaped ``LIKE`` on named columns

Column names run through ``_validate_column`` (regex allowlist
``^[A-Za-z_][A-Za-z0-9_]*$``) and values run through ``_escape_value``
(escapes ``\\``, ``'``, ``%``, ``_``; drops null bytes; numerics/bools/
datetimes handled natively). Unknown operators raise ``ValueError``.

Callers MUST NOT build SQL by f-string concatenation — this module is the
only SQL construction point in the HB Product Center. Batch B (WS 2)
removed the deprecated ``where``/``where_raw``/``order_by``/``order_by_raw``
kwargs; any new injection vector would be a new bug, not a regression of
an old API.
"""

import logging
import re
from datetime import date, datetime
from typing import Any

from databricks.sdk import WorkspaceClient
from databricks.sdk.service.sql import StatementState

from ..databricks_config import UC_CATALOG, UC_SCHEMA, WAREHOUSE_ID

logger = logging.getLogger(__name__)

# \A / \Z anchors reject trailing newlines — `$` in default mode lets
# `"col\n"` through.
_COLUMN_RE = re.compile(r"\A[a-zA-Z_][a-zA-Z0-9_]*\Z")
_ALLOWED_OPS = {"=", "!=", ">", ">=", "<", "<="}

# Type alias for the public filter shape: col → scalar (shorthand for
# equality) OR col → (op, value) for comparisons.
FilterValue = Any  # scalar | tuple[str, Any]
Filters = dict[str, FilterValue]


def _validate_column(name: str) -> str:
    """Validate a column name against an allowlist regex.

    Raises ValueError on any character that isn't ASCII letter, digit, or
    underscore — and rejects names starting with a digit.
    """
    if not _COLUMN_RE.match(name):
        raise ValueError(f"Invalid column name: {name!r}")
    return name


def _escape_like(value: str) -> str:
    """Escape special characters for use inside a SQL LIKE pattern.

    Escapes ``\\``, ``%``, ``_``, and ``'`` so the value can be safely
    interpolated into a ``LIKE '...' ESCAPE '\\\\'`` clause.
    """
    value = value.replace("\\", "\\\\")
    value = value.replace("%", "\\%")
    value = value.replace("_", "\\_")
    value = value.replace("'", "''")
    return value


def _escape_value(value: Any) -> str:
    """Escape a scalar for SQL insertion."""
    if value is None:
        return "NULL"
    if isinstance(value, bool):
        return "TRUE" if value else "FALSE"
    if isinstance(value, (int, float)):
        return str(value)
    if isinstance(value, (datetime, date)):
        return f"'{value.isoformat()}'"
    s = str(value)
    # Drop null bytes before any escape work — they can terminate SQL
    # strings on some drivers.
    s = s.replace("\x00", "")
    # Order matters: escape backslashes first, then single quotes, then
    # LIKE wildcards (to keep = comparisons with literal %/_ working).
    s = s.replace("\\", "\\\\")
    s = s.replace("'", "''")
    s = s.replace("%", "\\%")
    s = s.replace("_", "\\_")
    return f"'{s}'"


def execute_query(ws: WorkspaceClient, sql: str) -> list[list]:
    """Execute a SQL query against Unity Catalog and return rows."""
    result = ws.statement_execution.execute_statement(
        warehouse_id=WAREHOUSE_ID,
        statement=sql,
        wait_timeout="30s",
    )

    if result.status is None:
        raise RuntimeError("Query returned no status")

    if result.status.state == StatementState.SUCCEEDED:
        if result.result is None:
            return []
        return result.result.data_array or []
    if result.status.state == StatementState.FAILED:
        error_msg = "Unknown error"
        if result.status.error and result.status.error.message:
            error_msg = result.status.error.message
        raise RuntimeError(f"Query failed: {error_msg}")
    raise RuntimeError(f"Query in unexpected state: {result.status.state}")


def execute_query_with_schema(
    ws: WorkspaceClient, sql: str
) -> tuple[list[str], list[list]]:
    """Execute a SQL query and return (column_names, rows)."""
    result = ws.statement_execution.execute_statement(
        warehouse_id=WAREHOUSE_ID,
        statement=sql,
        wait_timeout="30s",
    )

    if result.status is None:
        raise RuntimeError("Query returned no status")

    if result.status.state == StatementState.SUCCEEDED:
        columns: list[str] = []
        if result.manifest and result.manifest.schema and result.manifest.schema.columns:
            columns = [col.name or "" for col in result.manifest.schema.columns]
        data = result.result.data_array if result.result else []
        return columns, data or []
    if result.status.state == StatementState.FAILED:
        error_msg = "Unknown error"
        if result.status.error and result.status.error.message:
            error_msg = result.status.error.message
        raise RuntimeError(f"Query failed: {error_msg}")
    raise RuntimeError(f"Query in unexpected state: {result.status.state}")


def get_table_name(table: str) -> str:
    """Return fully qualified table name — ``<catalog>.<schema>.<table>``."""
    return f"{UC_CATALOG}.{UC_SCHEMA}.{table}"


def _build_where(filters: Filters | None) -> str:
    """Build a WHERE clause from a safe filters dict.

    Each entry is one of:
      * ``col: scalar``         — rendered as ``col = <escaped>``
      * ``col: (op, value)``    — rendered as ``col <op> <escaped>``
    """
    if not filters:
        return ""
    parts: list[str] = []
    for col, raw in filters.items():
        _validate_column(col)
        if (
            isinstance(raw, tuple)
            and len(raw) == 2
            and isinstance(raw[0], str)
            and raw[0] in _ALLOWED_OPS
        ):
            op, value = raw
            parts.append(f"{col} {op} {_escape_value(value)}")
        else:
            parts.append(f"{col} = {_escape_value(raw)}")
    return " AND ".join(parts)


def count_rows(
    ws: WorkspaceClient,
    table: str,
    filters: Filters | None = None,
) -> int:
    """Count rows in a UC table, optionally filtered.

    Example:
        count_rows(ws, "hb_products", filters={"status": "active"})
        count_rows(ws, "hb_recognition_jobs",
                   filters={"created_at": (">=", "2026-04-01")})
    """
    fqn = get_table_name(table)
    sql = f"SELECT COUNT(*) FROM {fqn}"
    where_clause = _build_where(filters)
    if where_clause:
        sql += f" WHERE {where_clause}"
    rows = execute_query(ws, sql)
    return int(rows[0][0]) if rows else 0


def avg_column(
    ws: WorkspaceClient,
    table: str,
    column: str,
    filters: Filters | None = None,
) -> float:
    """Average of *column*, optionally filtered."""
    _validate_column(column)
    fqn = get_table_name(table)
    sql = f"SELECT AVG({column}) FROM {fqn}"
    where_clause = _build_where(filters)
    if where_clause:
        sql += f" WHERE {where_clause}"
    rows = execute_query(ws, sql)
    return float(rows[0][0]) if rows and rows[0][0] is not None else 0.0


def sum_column(
    ws: WorkspaceClient,
    table: str,
    column: str,
    filters: Filters | None = None,
) -> float:
    """Sum of *column*, optionally filtered."""
    _validate_column(column)
    fqn = get_table_name(table)
    sql = f"SELECT SUM({column}) FROM {fqn}"
    where_clause = _build_where(filters)
    if where_clause:
        sql += f" WHERE {where_clause}"
    rows = execute_query(ws, sql)
    return float(rows[0][0]) if rows and rows[0][0] is not None else 0.0


def select_all(
    ws: WorkspaceClient,
    table: str,
    filters: Filters | None = None,
    order_by_column: str = "",
    order_desc: bool = False,
    limit: int = 50,
    offset: int = 0,
) -> list[dict[str, Any]]:
    """Select all columns from *table* and return as a list of dicts.

    Only equality and comparison filters are supported. For free-text
    search, use :func:`search_like`.
    """
    limit = int(limit)
    offset = int(offset)

    fqn = get_table_name(table)
    sql = f"SELECT * FROM {fqn}"

    where_clause = _build_where(filters)
    if where_clause:
        sql += f" WHERE {where_clause}"

    if order_by_column:
        _validate_column(order_by_column)
        sql += f" ORDER BY {order_by_column}"
        if order_desc:
            sql += " DESC"

    sql += f" LIMIT {limit} OFFSET {offset}"

    columns, rows = execute_query_with_schema(ws, sql)
    return [dict(zip(columns, row)) for row in rows]


def select_one(
    ws: WorkspaceClient,
    table: str,
    filters: Filters | None = None,
) -> dict[str, Any] | None:
    """Select a single row, optionally filtered."""
    results = select_all(ws, table, filters=filters, limit=1)
    return results[0] if results else None


def select_by_id(
    ws: WorkspaceClient, table: str, id_value: int
) -> dict[str, Any] | None:
    """Select a single row by ID."""
    id_value = int(id_value)
    return select_one(ws, table, filters={"id": id_value})


def search_like(
    ws: WorkspaceClient,
    table: str,
    columns: list[str],
    term: str,
    filters: Filters | None = None,
    order_by_column: str = "",
    order_desc: bool = False,
    limit: int = 50,
    offset: int = 0,
) -> list[dict[str, Any]]:
    """LIKE-search *term* across *columns*, optionally combined with filters.

    All column names are validated, ``term`` is escaped for LIKE wildcards,
    and an explicit ``ESCAPE '\\\\'`` clause is appended so the escape
    character can't be used to bypass the protection.

    Example:
        search_like(ws, "hb_products",
                    columns=["style_name", "sku"],
                    term=user_input,
                    filters={"category": "suits"})
    """
    limit = int(limit)
    offset = int(offset)

    if not columns:
        return []

    for col in columns:
        _validate_column(col)

    escaped_term = _escape_like(term.lower())
    conditions = [
        f"LOWER({col}) LIKE '%{escaped_term}%' ESCAPE '\\\\'" for col in columns
    ]
    search_clause = "(" + " OR ".join(conditions) + ")"

    fqn = get_table_name(table)
    parts = [f"SELECT * FROM {fqn}"]

    where_clause = _build_where(filters)
    if where_clause and search_clause:
        parts.append(f"WHERE {where_clause} AND {search_clause}")
    elif where_clause:
        parts.append(f"WHERE {where_clause}")
    elif search_clause:
        parts.append(f"WHERE {search_clause}")

    if order_by_column:
        _validate_column(order_by_column)
        direction = " DESC" if order_desc else ""
        parts.append(f"ORDER BY {order_by_column}{direction}")

    parts.append(f"LIMIT {limit} OFFSET {offset}")

    sql = " ".join(parts)
    result_columns, rows = execute_query_with_schema(ws, sql)
    return [dict(zip(result_columns, row)) for row in rows]


def insert_row(ws: WorkspaceClient, table: str, data: dict[str, Any]) -> int | None:
    """Insert a row into a UC table; return the max id if available."""
    fqn = get_table_name(table)
    for col in data.keys():
        _validate_column(col)
    columns = ", ".join(data.keys())
    values = ", ".join(_escape_value(v) for v in data.values())

    sql = f"INSERT INTO {fqn} ({columns}) VALUES ({values})"
    execute_query(ws, sql)

    try:
        result = execute_query(ws, f"SELECT MAX(id) FROM {fqn}")
        return int(result[0][0]) if result and result[0][0] else None
    except Exception:
        return None


def update_row(
    ws: WorkspaceClient, table: str, id_value: int, data: dict[str, Any]
) -> bool:
    """Update a row in a UC table by integer ID."""
    if not data:
        return True

    id_value = int(id_value)
    fqn = get_table_name(table)
    for col in data.keys():
        _validate_column(col)
    set_clause = ", ".join(f"{k} = {_escape_value(v)}" for k, v in data.items())
    sql = f"UPDATE {fqn} SET {set_clause} WHERE id = {id_value}"
    execute_query(ws, sql)
    return True
