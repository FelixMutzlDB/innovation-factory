"""Unity Catalog query service for HB Product Center.

Uses Databricks SQL Statement Execution API to query UC tables instead of Lakebase.
This ensures consistent access via the app's Service Principal identity.
"""

from datetime import datetime
from typing import Any

from databricks.sdk import WorkspaceClient
from databricks.sdk.service.sql import StatementState

from ..databricks_config import UC_CATALOG, UC_SCHEMA, WAREHOUSE_ID


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


def count_rows(ws: WorkspaceClient, table: str, where: str = "") -> int:
    """Count rows in a UC table with optional WHERE clause."""
    fqn = get_table_name(table)
    sql = f"SELECT COUNT(*) FROM {fqn}"
    if where:
        sql += f" WHERE {where}"
    rows = execute_query(ws, sql)
    return int(rows[0][0]) if rows else 0


def avg_column(ws: WorkspaceClient, table: str, column: str, where: str = "") -> float:
    """Calculate average of a column with optional WHERE clause."""
    fqn = get_table_name(table)
    sql = f"SELECT AVG({column}) FROM {fqn}"
    if where:
        sql += f" WHERE {where}"
    rows = execute_query(ws, sql)
    return float(rows[0][0]) if rows and rows[0][0] is not None else 0.0


def sum_column(ws: WorkspaceClient, table: str, column: str, where: str = "") -> float:
    """Calculate sum of a column with optional WHERE clause."""
    fqn = get_table_name(table)
    sql = f"SELECT SUM({column}) FROM {fqn}"
    if where:
        sql += f" WHERE {where}"
    rows = execute_query(ws, sql)
    return float(rows[0][0]) if rows and rows[0][0] is not None else 0.0


def select_all(
    ws: WorkspaceClient,
    table: str,
    where: str = "",
    order_by: str = "",
    limit: int = 50,
    offset: int = 0,
) -> list[dict[str, Any]]:
    """Select all columns from a table and return as list of dicts."""
    fqn = get_table_name(table)
    sql = f"SELECT * FROM {fqn}"
    if where:
        sql += f" WHERE {where}"
    if order_by:
        sql += f" ORDER BY {order_by}"
    sql += f" LIMIT {limit} OFFSET {offset}"

    columns, rows = execute_query_with_schema(ws, sql)
    return [dict(zip(columns, row)) for row in rows]


def select_one(ws: WorkspaceClient, table: str, where: str) -> dict[str, Any] | None:
    """Select a single row from a table."""
    results = select_all(ws, table, where=where, limit=1)
    return results[0] if results else None


def select_by_id(ws: WorkspaceClient, table: str, id_value: int) -> dict[str, Any] | None:
    """Select a single row by ID."""
    return select_one(ws, table, f"id = {id_value}")


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
        # Escape single quotes
        escaped = str(value).replace("'", "''")
        return f"'{escaped}'"


def insert_row(ws: WorkspaceClient, table: str, data: dict[str, Any]) -> int | None:
    """Insert a row into a UC table and return the generated ID if available."""
    fqn = get_table_name(table)
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

    fqn = get_table_name(table)
    set_clause = ", ".join(f"{k} = {_escape_value(v)}" for k, v in data.items())
    sql = f"UPDATE {fqn} SET {set_clause} WHERE id = {id_value}"
    execute_query(ws, sql)
    return True
