"""Unity Catalog query service for HB Product Center.

Uses Databricks SQL Statement Execution API to query UC tables instead of Lakebase.
This ensures consistent access via the app's Service Principal identity.
"""

import logging
import re
import warnings
from datetime import datetime
from typing import Any

from databricks.sdk import WorkspaceClient
from databricks.sdk.service.sql import StatementState

from ..databricks_config import UC_CATALOG, UC_SCHEMA, WAREHOUSE_ID

logger = logging.getLogger(__name__)

_COLUMN_RE = re.compile(r"^[a-zA-Z_][a-zA-Z0-9_]*$")


def _validate_column(name: str) -> str:
    """Validate that a column name contains only safe characters.

    Args:
        name: Column name to validate

    Returns:
        The validated column name

    Raises:
        ValueError: If column name contains unsafe characters
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


def execute_query(ws: WorkspaceClient, sql: str) -> list[list]:
    """Execute a SQL query against Unity Catalog and return results.

    Args:
        ws: WorkspaceClient instance (uses app SP identity)
        sql: SQL query to execute

    Returns:
        List of rows, where each row is a list of column values

    Raises:
        RuntimeError: If query execution fails
    """
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
    elif result.status.state == StatementState.FAILED:
        error_msg = "Unknown error"
        if result.status.error and result.status.error.message:
            error_msg = result.status.error.message
        raise RuntimeError(f"Query failed: {error_msg}")
    else:
        raise RuntimeError(f"Query in unexpected state: {result.status.state}")


def execute_query_with_schema(ws: WorkspaceClient, sql: str) -> tuple[list[str], list[list]]:
    """Execute a SQL query and return column names along with results."""
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
    elif result.status.state == StatementState.FAILED:
        error_msg = "Unknown error"
        if result.status.error and result.status.error.message:
            error_msg = result.status.error.message
        raise RuntimeError(f"Query failed: {error_msg}")
    else:
        raise RuntimeError(f"Query in unexpected state: {result.status.state}")


def get_table_name(table: str) -> str:
    """Get fully qualified table name."""
    return f"{UC_CATALOG}.{UC_SCHEMA}.{table}"


def count_rows(
    ws: WorkspaceClient,
    table: str,
    filters: dict[str, str] | None = None,
    *,
    where_raw: str = "",
    where: str = "",
) -> int:
    """Count rows in a UC table with optional filters.

    Args:
        ws: WorkspaceClient instance
        table: Table name
        filters: Safe column=value equality filters
        where_raw: **Deprecated.** Raw WHERE clause — avoid if possible.
        where: **Deprecated.** Alias for where_raw.
    """
    if where and not where_raw:
        where_raw = where
    fqn = get_table_name(table)
    sql = f"SELECT COUNT(*) FROM {fqn}"
    where_clause = _build_where(filters, where_raw)
    if where_clause:
        sql += f" WHERE {where_clause}"
    rows = execute_query(ws, sql)
    return int(rows[0][0]) if rows else 0


def avg_column(
    ws: WorkspaceClient,
    table: str,
    column: str,
    filters: dict[str, str] | None = None,
    *,
    where_raw: str = "",
    where: str = "",
) -> float:
    """Calculate average of a column with optional filters."""
    if where and not where_raw:
        where_raw = where
    _validate_column(column)
    fqn = get_table_name(table)
    sql = f"SELECT AVG({column}) FROM {fqn}"
    where_clause = _build_where(filters, where_raw)
    if where_clause:
        sql += f" WHERE {where_clause}"
    rows = execute_query(ws, sql)
    return float(rows[0][0]) if rows and rows[0][0] is not None else 0.0


def sum_column(
    ws: WorkspaceClient,
    table: str,
    column: str,
    filters: dict[str, str] | None = None,
    *,
    where_raw: str = "",
    where: str = "",
) -> float:
    """Calculate sum of a column with optional filters."""
    if where and not where_raw:
        where_raw = where
    _validate_column(column)
    fqn = get_table_name(table)
    sql = f"SELECT SUM({column}) FROM {fqn}"
    where_clause = _build_where(filters, where_raw)
    if where_clause:
        sql += f" WHERE {where_clause}"
    rows = execute_query(ws, sql)
    return float(rows[0][0]) if rows and rows[0][0] is not None else 0.0


def _build_where(filters: dict[str, str] | None, where_raw: str) -> str:
    """Build a WHERE clause from safe filters, falling back to deprecated raw clause."""
    if filters:
        parts = []
        for col, val in filters.items():
            _validate_column(col)
            parts.append(f"{col} = {_escape_value(val)}")
        return " AND ".join(parts)
    if where_raw:
        logger.warning(
            "where_raw is deprecated and unsafe — migrate to filters dict. "
            "Caller: %s",
            where_raw[:120],
        )
        warnings.warn(
            "where_raw is deprecated; use filters dict instead",
            DeprecationWarning,
            stacklevel=3,
        )
        return where_raw
    return ""


def select_all(
    ws: WorkspaceClient,
    table: str,
    filters: dict[str, str] | None = None,
    order_by_column: str = "",
    order_desc: bool = False,
    limit: int = 50,
    offset: int = 0,
    *,
    where_raw: str = "",
    order_by_raw: str = "",
    # Deprecated aliases for backward compatibility
    where: str = "",
    order_by: str = "",
) -> list[dict[str, Any]]:
    """Select all columns from a table and return as list of dicts.

    Args:
        ws: WorkspaceClient instance
        table: Table name
        filters: Safe column=value equality filters
        order_by_column: Column to order by (validated)
        order_desc: If True, order descending
        limit: Maximum number of rows
        offset: Row offset
        where_raw: **Deprecated.** Raw WHERE clause.
        order_by_raw: **Deprecated.** Raw ORDER BY clause.
        where: **Deprecated.** Alias for where_raw.
        order_by: **Deprecated.** Alias for order_by_raw.
    """
    # Map deprecated aliases
    if where and not where_raw:
        where_raw = where
    if order_by and not order_by_raw:
        order_by_raw = order_by

    limit = int(limit)
    offset = int(offset)

    fqn = get_table_name(table)
    sql = f"SELECT * FROM {fqn}"

    where_clause = _build_where(filters, where_raw)
    if where_clause:
        sql += f" WHERE {where_clause}"

    if order_by_column:
        _validate_column(order_by_column)
        sql += f" ORDER BY {order_by_column}"
        if order_desc:
            sql += " DESC"
    elif order_by_raw:
        logger.warning(
            "order_by_raw is deprecated and unsafe — migrate to order_by_column. "
            "Caller: %s",
            order_by_raw[:120],
        )
        warnings.warn(
            "order_by_raw is deprecated; use order_by_column instead",
            DeprecationWarning,
            stacklevel=2,
        )
        sql += f" ORDER BY {order_by_raw}"

    sql += f" LIMIT {limit} OFFSET {offset}"

    columns, rows = execute_query_with_schema(ws, sql)
    return [dict(zip(columns, row)) for row in rows]


def select_one(
    ws: WorkspaceClient,
    table: str,
    filters: dict[str, str] | None = None,
    *,
    where_raw: str = "",
    where: str = "",
) -> dict[str, Any] | None:
    """Select a single row from a table."""
    if where and not where_raw:
        where_raw = where
    results = select_all(ws, table, filters=filters, where_raw=where_raw, limit=1)
    return results[0] if results else None


def select_by_id(ws: WorkspaceClient, table: str, id_value: int) -> dict[str, Any] | None:
    """Select a single row by ID."""
    id_value = int(id_value)
    return select_one(ws, table, filters={"id": id_value})


def search_like(
    ws: WorkspaceClient,
    table: str,
    columns: list[str],
    term: str,
    limit: int = 50,
    offset: int = 0,
) -> list[dict[str, Any]]:
    """Search for rows where any of the given columns contain *term* (case-insensitive).

    Uses parameterised LIKE with proper escaping to prevent SQL injection.

    Args:
        ws: WorkspaceClient instance
        table: Table name
        columns: List of column names to search (each validated)
        term: Search term (will be escaped for LIKE)
        limit: Maximum rows
        offset: Row offset

    Returns:
        List of matching rows as dicts
    """
    limit = int(limit)
    offset = int(offset)

    if not columns:
        return []

    for col in columns:
        _validate_column(col)

    escaped_term = _escape_like(term.lower())
    conditions = [f"LOWER({col}) LIKE '%{escaped_term}%' ESCAPE '\\\\'" for col in columns]
    where_clause = " OR ".join(conditions)

    fqn = get_table_name(table)
    sql = f"SELECT * FROM {fqn} WHERE {where_clause} LIMIT {limit} OFFSET {offset}"
    result_columns, rows = execute_query_with_schema(ws, sql)
    return [dict(zip(result_columns, row)) for row in rows]


def _escape_value(value: Any) -> str:
    """Escape a value for SQL insertion."""
    if value is None:
        return "NULL"
    elif isinstance(value, bool):
        return "TRUE" if value else "FALSE"
    elif isinstance(value, (int, float)):
        return str(value)
    elif isinstance(value, datetime):
        return f"'{value.isoformat()}'"
    else:
        s = str(value)
        # Remove null bytes
        s = s.replace("\x00", "")
        # Escape backslashes, then single quotes, percent, and underscore
        s = s.replace("\\", "\\\\")
        s = s.replace("'", "''")
        s = s.replace("%", "\\%")
        s = s.replace("_", "\\_")
        return f"'{s}'"


def insert_row(ws: WorkspaceClient, table: str, data: dict[str, Any]) -> int | None:
    """Insert a row into a UC table and return the generated ID if available."""
    fqn = get_table_name(table)
    for col in data.keys():
        _validate_column(col)
    columns = ", ".join(data.keys())
    values = ", ".join(_escape_value(v) for v in data.values())

    sql = f"INSERT INTO {fqn} ({columns}) VALUES ({values})"
    execute_query(ws, sql)

    # Try to get the last inserted ID (works if table has auto-increment)
    try:
        result = execute_query(ws, f"SELECT MAX(id) FROM {fqn}")
        return int(result[0][0]) if result and result[0][0] else None
    except Exception:
        return None


def update_row(ws: WorkspaceClient, table: str, id_value: int, data: dict[str, Any]) -> bool:
    """Update a row in a UC table by ID."""
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
