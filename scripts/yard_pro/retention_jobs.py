"""yard-pro retention/partition jobs (Plan §5 + §12 P2).

Declarative retention rules for the four append-only data stores:

| Target                                  | Retention                          | Rule                                                                  |
|-----------------------------------------|------------------------------------|-----------------------------------------------------------------------|
| Lakebase ``yp_action_log``              | 24 months                          | Rows older than the cutoff are hard-deleted.                          |
| Delta ``yard_pro_bronze.coach_transcripts`` (unconsented) | 30 days       | Rows with ``consent_flag=false`` older than the cutoff are deleted.   |
| Delta ``yard_pro_bronze.telemetry_events`` (raw)         | 90 days       | Raw rows deleted; Silver/Gold rollups survive.                        |
| UC Volume ``yard_pro/photos/``                            | 180 days      | Files older than the cutoff are deleted.                              |

## Safety rails

- ``--dry-run`` defaults to **True**. ``--no-dry-run`` is required for
  any actual delete. Print-only otherwise.
- Every function returns the row count it (would have) purged so the
  CLI prints a structured summary.
- The Delta-side functions issue ``DELETE FROM …`` via UC Statement
  Execution (lessons-learned §9 SQL-safety pattern — the date filter
  is a literal ISO 8601 string produced by us, not user input).
- The Volume-side function uses the Workspace ``files`` API; failures
  on individual file deletes are logged but don't abort the run.

## Invocation

```bash
uv run python -m scripts.yard_pro.retention_jobs \
  --catalog felix_demo_catalog \
  --profile fevm-felix-demo \
  --before 2024-01-01 \
  --dry-run
```

To actually delete, pass ``--no-dry-run``. The script prints a
confirmation banner before each destructive step so an operator who
typo'd a date can ctrl-C out.
"""
from __future__ import annotations

import argparse
import logging
import sys
from dataclasses import dataclass, field
from datetime import date, datetime, timezone
from typing import Optional

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Retention rule constants (plan §5)
# ---------------------------------------------------------------------------

ACTION_LOG_RETENTION_MONTHS = 24
COACH_TRANSCRIPTS_UNCONSENTED_DAYS = 30
TELEMETRY_RAW_DAYS = 90
PHOTOS_VOLUME_DAYS = 180


# ---------------------------------------------------------------------------
# Result shape
# ---------------------------------------------------------------------------


@dataclass
class RetentionResult:
    """Returned by each ``purge_*`` function.

    - ``target``: human-readable name of the data store.
    - ``rows_purged``: how many rows / files were (or would be) deleted.
    - ``dry_run``: echoes the request flag.
    - ``errors``: per-row / per-file error messages (best-effort).
    """

    target: str
    rows_purged: int = 0
    dry_run: bool = True
    errors: list[str] = field(default_factory=list)


# ---------------------------------------------------------------------------
# Lakebase: yp_action_log
# ---------------------------------------------------------------------------


def purge_old_action_log(
    session,
    before: date,
    *,
    dry_run: bool = True,
) -> RetentionResult:
    """Hard-delete ``yp_action_log`` rows with ``occurred_at < before``.

    Plan §5: 24-month retention. Older rows are pruned to Delta cold
    storage during the partition prune; this Lakebase-side job is the
    secondary cleanup.

    ``session`` is a SQLModel/SQLAlchemy session. We use the metadata
    table to avoid an unconditional model import — the caller may be
    running this against a yard_pro-only DB.
    """
    from sqlalchemy import delete, func, select as sa_select
    from sqlmodel import SQLModel

    tbl = SQLModel.metadata.tables.get("yp_action_log")
    if tbl is None:
        # Allow callers to use the script without registering models —
        # graceful no-op + WARN. The test fixtures import models first
        # so they hit the real path.
        logger.warning(
            "purge_old_action_log: yp_action_log not in metadata — did "
            "you import the yard_pro models first?"
        )
        return RetentionResult(
            target="yp_action_log", rows_purged=0, dry_run=dry_run
        )

    before_dt = datetime(before.year, before.month, before.day, tzinfo=timezone.utc)
    count = session.execute(
        sa_select(func.count()).select_from(tbl).where(
            tbl.c.occurred_at < before_dt
        )
    ).scalar_one()

    if not dry_run and count > 0:
        session.execute(delete(tbl).where(tbl.c.occurred_at < before_dt))
        session.commit()
    elif dry_run:
        # Don't leave a transaction open.
        session.rollback()

    return RetentionResult(
        target="yp_action_log",
        rows_purged=int(count),
        dry_run=dry_run,
    )


# ---------------------------------------------------------------------------
# Delta: yard_pro_bronze.coach_transcripts (consent-gated)
# ---------------------------------------------------------------------------


def _execute_delta_delete(
    ws, catalog: str, sql: str, *, dry_run: bool
) -> tuple[int, list[str]]:
    """Run a DELETE statement against UC SQL warehouse; return (count, errors).

    The pre-count is a separate SELECT so the dry-run path reports a
    realistic number. Both statements run against the same warehouse
    (default warehouse on the WS client).
    """
    from os import environ

    warehouse_id = environ.get("DATABRICKS_WAREHOUSE_ID") or environ.get(
        "WAREHOUSE_ID"
    )
    if not warehouse_id:
        msg = (
            "retention: DATABRICKS_WAREHOUSE_ID / WAREHOUSE_ID env var "
            "not set; cannot execute Delta DELETE."
        )
        logger.warning(msg)
        return 0, [msg]

    # Extract the WHERE clause for the pre-count (mirror the DELETE).
    if "WHERE" not in sql.upper():
        return 0, ["retention: refusing to count without a WHERE clause"]
    where_clause = sql[sql.upper().index("WHERE"):]
    table_ref = sql.split()[2]  # DELETE FROM <table_ref> WHERE …
    count_sql = f"SELECT COUNT(*) FROM {table_ref} {where_clause}"

    errors: list[str] = []
    count = 0
    try:
        from databricks.sdk.service.sql import StatementState

        resp = ws.statement_execution.execute_statement(
            statement=count_sql,
            warehouse_id=warehouse_id,
            catalog=catalog,
            wait_timeout="30s",
        )
        if resp.status and resp.status.state == StatementState.SUCCEEDED:
            data = resp.result and resp.result.data_array
            if data and data[0]:
                count = int(data[0][0])
        else:
            errors.append(
                f"pre-count failed state={getattr(resp.status, 'state', None)}"
            )
    except Exception as exc:
        errors.append(f"pre-count error: {type(exc).__name__}: {exc}")
        return 0, errors

    if not dry_run and count > 0:
        try:
            ws.statement_execution.execute_statement(
                statement=sql,
                warehouse_id=warehouse_id,
                catalog=catalog,
                wait_timeout="50s",
            )
        except Exception as exc:
            errors.append(f"DELETE error: {type(exc).__name__}: {exc}")

    return count, errors


def purge_unconsented_coach_transcripts(
    ws,
    catalog: str,
    before: date,
    *,
    dry_run: bool = True,
) -> RetentionResult:
    """Hard-delete unconsented coach transcripts older than ``before``.

    Plan §5: ``consent_flag=false AND created_at < (now - 30d)`` is the
    GDPR-purpose-limitation rule. Consented transcripts survive longer
    (13 months) and are handled by a separate aggregation step.
    """
    sql = (
        "DELETE FROM yard_pro_bronze.coach_transcripts "
        f"WHERE consent_flag = false AND created_at < DATE('{before.isoformat()}')"
    )
    count, errors = _execute_delta_delete(ws, catalog, sql, dry_run=dry_run)
    return RetentionResult(
        target="yard_pro_bronze.coach_transcripts (unconsented)",
        rows_purged=count,
        dry_run=dry_run,
        errors=errors,
    )


# ---------------------------------------------------------------------------
# Delta: yard_pro_bronze.telemetry_events (raw)
# ---------------------------------------------------------------------------


def purge_old_telemetry(
    ws,
    catalog: str,
    before: date,
    *,
    dry_run: bool = True,
) -> RetentionResult:
    """Hard-delete raw telemetry rows older than ``before``.

    Plan §5: 90-day raw retention. Silver/Gold rollups survive
    indefinitely (they're not personal data once aggregated).
    """
    sql = (
        "DELETE FROM yard_pro_bronze.telemetry_events "
        f"WHERE occurred_at < DATE('{before.isoformat()}')"
    )
    count, errors = _execute_delta_delete(ws, catalog, sql, dry_run=dry_run)
    return RetentionResult(
        target="yard_pro_bronze.telemetry_events",
        rows_purged=count,
        dry_run=dry_run,
        errors=errors,
    )


# ---------------------------------------------------------------------------
# UC Volume: yard_pro/photos/
# ---------------------------------------------------------------------------


def purge_old_photos(
    ws,
    volume_path: str,
    before: date,
    *,
    dry_run: bool = True,
) -> RetentionResult:
    """Hard-delete photo files older than ``before`` from the UC Volume.

    Plan §5: 180-day rolling delete. Walks every per-yard subdirectory
    under ``volume_path`` and removes files whose ``modification_time``
    predates the cutoff.
    """
    target = f"UC Volume {volume_path}"
    if not volume_path:
        return RetentionResult(
            target=target,
            rows_purged=0,
            dry_run=dry_run,
            errors=["volume_path empty"],
        )

    files_api = getattr(ws, "files", None)
    if files_api is None:
        return RetentionResult(
            target=target,
            rows_purged=0,
            dry_run=dry_run,
            errors=["ws.files unavailable"],
        )

    cutoff_ms = int(
        datetime(before.year, before.month, before.day, tzinfo=timezone.utc).timestamp()
        * 1000
    )
    errors: list[str] = []
    purged = 0
    prefix = volume_path.rstrip("/") + "/"
    try:
        listing = list(files_api.list_directory_contents(prefix))
    except Exception as exc:
        return RetentionResult(
            target=target,
            rows_purged=0,
            dry_run=dry_run,
            errors=[f"list_directory_contents: {type(exc).__name__}: {exc}"],
        )

    # The listing's top level is per-yard subdirectories. Each entry has
    # ``is_directory`` and ``path``; recurse one level for files.
    def _walk_files(prefix_: str):
        try:
            entries = list(files_api.list_directory_contents(prefix_))
        except Exception as exc:
            errors.append(
                f"list({prefix_}): {type(exc).__name__}: {exc}"
            )
            return
        for entry in entries:
            path = getattr(entry, "path", None)
            if not path:
                continue
            is_dir = getattr(entry, "is_directory", False)
            if is_dir:
                _walk_files(path)
                continue
            mtime = getattr(entry, "modification_time", None) or getattr(
                entry, "last_modified", None
            )
            if mtime is None or int(mtime) >= cutoff_ms:
                continue
            yield path

    for path in _walk_files(prefix):
        if dry_run:
            purged += 1
            continue
        try:
            files_api.delete(path)
            purged += 1
        except Exception as exc:
            errors.append(f"delete({path}): {type(exc).__name__}: {exc}")

    return RetentionResult(
        target=target,
        rows_purged=purged,
        dry_run=dry_run,
        errors=errors,
    )


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------


def _build_workspace_client(profile: Optional[str]):
    """Lazy import so unit tests that don't hit Databricks don't pull SDK."""
    from databricks.sdk import WorkspaceClient

    if profile:
        return WorkspaceClient(profile=profile)
    return WorkspaceClient()


def _build_lakebase_session():
    """Open a session against the configured Lakebase / SQLite DB.

    Imports the backend's ``runtime`` lazily so the dev DATABASE_URL
    fallback applies in local runs.
    """
    # Make sure yard_pro models are registered before we touch metadata.
    import innovation_factory.backend.projects.yard_pro.models  # noqa: F401
    from innovation_factory.backend.config import AppConfig
    from innovation_factory.backend.runtime import Runtime
    from sqlmodel import Session

    runtime = Runtime(AppConfig())
    return Session(runtime.engine)


def main(argv: Optional[list[str]] = None) -> int:
    parser = argparse.ArgumentParser(
        prog="yard_pro.retention_jobs",
        description=(
            "yard-pro retention jobs. Defaults to --dry-run; pass "
            "--no-dry-run to actually delete."
        ),
    )
    parser.add_argument(
        "--catalog",
        required=True,
        help="UC catalog hosting yard_pro_bronze.* (e.g. felix_demo_catalog)",
    )
    parser.add_argument(
        "--profile",
        default=None,
        help="Databricks CLI profile (e.g. fevm-felix-demo)",
    )
    parser.add_argument(
        "--before",
        required=True,
        help="ISO date (YYYY-MM-DD). Rows older than this are purged.",
    )
    parser.add_argument(
        "--volume-path",
        default="/Volumes/main/yard_pro/photos",
        help="UC Volume root for yard photos (default: /Volumes/main/yard_pro/photos)",
    )

    # Default-true safety rail: --dry-run is the default; --no-dry-run
    # is required for an actual destructive run.
    group = parser.add_mutually_exclusive_group()
    group.add_argument(
        "--dry-run",
        dest="dry_run",
        action="store_true",
        default=True,
        help="(default) Print row counts without deleting.",
    )
    group.add_argument(
        "--no-dry-run",
        dest="dry_run",
        action="store_false",
        help="Actually delete. Required for destructive runs.",
    )

    parser.add_argument(
        "--targets",
        default="all",
        help=(
            "Comma-separated subset of targets: action_log, transcripts, "
            "telemetry, photos. Default 'all'."
        ),
    )

    args = parser.parse_args(argv)

    try:
        before_date = date.fromisoformat(args.before)
    except ValueError as exc:
        print(f"Invalid --before date: {exc}", file=sys.stderr)
        return 2

    targets = (
        {"action_log", "transcripts", "telemetry", "photos"}
        if args.targets == "all"
        else {t.strip() for t in args.targets.split(",") if t.strip()}
    )

    print("================================================================")
    print(" yard-pro retention jobs")
    print(f"   catalog:     {args.catalog}")
    print(f"   profile:     {args.profile or '(env)'}")
    print(f"   before:      {before_date}")
    print(f"   volume_path: {args.volume_path}")
    print(f"   dry_run:     {args.dry_run}")
    print(f"   targets:     {sorted(targets)}")
    print("================================================================")

    if not args.dry_run:
        print()
        print(" !! --no-dry-run set — destructive run. Sleeping 3s to allow")
        print(" !! a ctrl-C if this was a mistake.")
        print()
        import time

        time.sleep(3)

    results: list[RetentionResult] = []

    ws = None
    if targets & {"transcripts", "telemetry", "photos"}:
        try:
            ws = _build_workspace_client(args.profile)
        except Exception as exc:
            print(f"WorkspaceClient failed: {type(exc).__name__}: {exc}")
            return 1

    if "action_log" in targets:
        session = _build_lakebase_session()
        try:
            results.append(
                purge_old_action_log(
                    session, before_date, dry_run=args.dry_run
                )
            )
        finally:
            session.close()

    if "transcripts" in targets and ws is not None:
        results.append(
            purge_unconsented_coach_transcripts(
                ws, args.catalog, before_date, dry_run=args.dry_run
            )
        )

    if "telemetry" in targets and ws is not None:
        results.append(
            purge_old_telemetry(
                ws, args.catalog, before_date, dry_run=args.dry_run
            )
        )

    if "photos" in targets and ws is not None:
        results.append(
            purge_old_photos(
                ws, args.volume_path, before_date, dry_run=args.dry_run
            )
        )

    print()
    print(" Results")
    print(" -------")
    for r in results:
        verb = "would purge" if r.dry_run else "purged"
        print(f"   {r.target}: {verb} {r.rows_purged} rows")
        for err in r.errors:
            print(f"     ! {err}")

    return 0


if __name__ == "__main__":  # pragma: no cover
    logging.basicConfig(level=logging.INFO)
    sys.exit(main())
