"""gdpr_service — GDPR Art. 17 ("right to be forgotten") cascade for yard-pro.

Plan §8 row: ``DELETE /api/projects/yard-pro/yards/{id}`` cascades:

- Lakebase ``yp_*`` rows by ``yard_id``
- UC Volume ``yard_pro/photos/<yard_id>/`` prefix
- Delta Bronze/Silver/Gold rows by ``yard_id_hash`` (anonymized rows are
  matchable by the hash but contain no PII)
- revokes ``yp_dealer_relationships.consent_state`` → ``revoked``

This module ships the **Lakebase-side cascade only**. The Delta-side
propagation runs through Lakehouse Sync within the sync interval; this
function returns when Lakebase is clean and the volume prefix is purged.

RT-025 mitigation — enumeration via metadata
---------------------------------------------
The risk register's RT-025 entry ("GDPR delete endpoint misses a table —
orphan rows survive") is mitigated by deriving the cascade target list
from ``SQLModel.metadata.tables``, filtered to the ``yp_*`` prefix. A
future contributor who adds another ``yp_*`` table gets automatic
coverage; the matching regression test in
``tests/projects/yard_pro/test_gdpr_art17_delete.py`` walks the same
metadata enumeration and fails CI if a new table isn't reachable from
the cascade (direct ``yard_id`` rows would still be there after the
delete).

Tables fall into three classes that the cascade handles in order:

1. **Indirect via parent** (purged BEFORE the parent table):
   - ``yp_coach_messages`` references ``yp_coach_sessions.id`` — gather
     the parent session IDs for the yard, then delete child messages by
     ``session_id``.
   - ``yp_tool_readiness`` references ``yp_tools.id`` — gather the
     parent tool IDs for the yard, then delete readiness rows by
     ``tool_id``.

2. **Direct yard_id rows** — every remaining ``yp_*`` table with a
   ``yard_id`` column, including the parents from (1) and the
   ``yp_dealer_relationships`` rows that we tombstone-then-delete.

3. **Root**: the ``yp_yards`` row itself.

Consent revocation tombstone
----------------------------
Per plan §8 we revoke ``yp_dealer_relationships.consent_state`` to
``revoked`` with ``revoked_at`` set **before** deleting the row, all in
one Session. The UPDATE is flushed to the DB before the DELETE so the
WAL emits both events; Lakehouse Sync downstream sees the revocation
transition even though the source row is then gone in the same flush.
"""
from __future__ import annotations

import logging
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any

from sqlalchemy import delete, select as sa_select, update
from sqlmodel import Session, SQLModel

from ..databricks_config import PHOTOS_VOLUME_PATH
from ..models import YpYard

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Enumerated cascade target lists — derived from SQLModel.metadata at
# **call time**. The conftest imports yard_pro.models before any test
# runs, so metadata is fully populated by the time this module's
# functions execute in the test environment; the FastAPI app imports
# models the same way.
# ---------------------------------------------------------------------------


def _yp_tables() -> dict[str, Any]:
    """All SQLAlchemy ``Table`` objects whose name starts with ``yp_``.

    Returns a name → Table mapping. Computed at call time (not cached at
    module load) so test fixtures that register new tables after import
    are still picked up. The cost is negligible (one dict comprehension
    over the registered mapper entries).
    """
    return {
        name: tbl
        for name, tbl in SQLModel.metadata.tables.items()
        if name.startswith("yp_")
    }


#: Tables that don't carry a ``yard_id`` column directly — they reference
#: the yard transitively. Each entry maps the child table name to
#: ``(child_fk_column, parent_table_name, parent_pk_column)`` so the
#: cascade can resolve the parent IDs first and then purge children.
_INDIRECT_REFS: dict[str, tuple[str, str, str]] = {
    "yp_coach_messages": ("session_id", "yp_coach_sessions", "id"),
    "yp_tool_readiness": ("tool_id", "yp_tools", "id"),
}

#: The root table the cascade ends with.
_ROOT_TABLE = "yp_yards"


def _classify_tables(
    all_tables: dict[str, Any],
) -> tuple[list[str], list[str]]:
    """Split yp_* tables into (indirect_first, direct_by_yard_id).

    Order matters: indirect children must be purged before their parents
    because the parent rows are themselves in the direct list and will
    be deleted by ``yard_id``. ``yp_yards`` is intentionally excluded
    from both lists — it is deleted last as the root.

    If a yp_* table appears that has no ``yard_id`` column AND no
    ``_INDIRECT_REFS`` entry, we WARN-log here and the matching test
    will fail (post-delete row count != 0). This is RT-025 by design —
    the contributor must explicitly wire the new table into the cascade.
    """
    indirect = [name for name in _INDIRECT_REFS if name in all_tables]

    direct: list[str] = []
    for name, tbl in all_tables.items():
        if name == _ROOT_TABLE:
            continue
        if name in _INDIRECT_REFS:
            continue
        if "yard_id" in tbl.columns:
            direct.append(name)
        else:
            logger.warning(
                "yard-pro GDPR cascade: table %s has no yard_id and no "
                "_INDIRECT_REFS entry — orphan rows would survive a "
                "delete. RT-025: add a mapping in gdpr_service.py.",
                name,
            )
    # Sort for deterministic order — same enumeration, same delete plan.
    return indirect, sorted(direct)


# ---------------------------------------------------------------------------
# Result shape
# ---------------------------------------------------------------------------


@dataclass
class CascadeResult:
    """Returned by :func:`delete_yard_cascade`.

    - ``tables_purged``: name → row count actually deleted (or counted
      in dry-run mode).
    - ``photos_purged``: number of UC Volume entries removed (best-
      effort count from the SDK list). Zero when ``PHOTOS_VOLUME_PATH``
      is not configured or when the prefix didn't exist.
    - ``consent_revocations``: count of ``yp_dealer_relationships`` rows
      whose ``consent_state`` was tombstoned to ``revoked`` before the
      row was deleted.
    - ``dry_run``: echoes the request flag.
    """

    yard_id: int
    tables_purged: dict[str, int] = field(default_factory=dict)
    photos_purged: int = 0
    consent_revocations: int = 0
    dry_run: bool = False


# ---------------------------------------------------------------------------
# Volume cascade
# ---------------------------------------------------------------------------


def _purge_photo_prefix(ws: Any, yard_id: int, *, dry_run: bool) -> int:
    """Delete ``<PHOTOS_VOLUME_PATH>/<yard_id>/`` recursively from UC Volume.

    Returns the number of files removed (or that would be removed in
    dry-run mode). When ``PHOTOS_VOLUME_PATH`` is empty (local dev) or
    the WS client doesn't expose a ``files`` API surface, logs WARN and
    returns 0 — the function never raises.
    """
    if not PHOTOS_VOLUME_PATH:
        logger.warning(
            "yard-pro GDPR cascade: PHOTOS_VOLUME_PATH unset; skipping "
            "volume purge for yard_id=%s",
            yard_id,
        )
        return 0

    prefix = f"{PHOTOS_VOLUME_PATH.rstrip('/')}/{yard_id}/"
    files_api = getattr(ws, "files", None)
    if files_api is None:
        logger.warning(
            "yard-pro GDPR cascade: ws.files unavailable (local dev "
            "mock?); skipping volume purge for prefix=%s",
            prefix,
        )
        return 0

    try:
        listing = list(files_api.list_directory_contents(prefix))
    except Exception as exc:
        # 404-shaped: prefix doesn't exist yet. Treat as "0 to delete".
        logger.info(
            "yard-pro GDPR cascade: list_directory_contents(%s) -> %s "
            "(treated as empty)",
            prefix,
            exc,
        )
        return 0

    count = 0
    for entry in listing:
        if dry_run:
            count += 1
            continue
        path = getattr(entry, "path", None)
        if not path:
            continue
        try:
            files_api.delete(path)
            count += 1
        except Exception as exc:  # pragma: no cover — best-effort
            logger.error(
                "yard-pro GDPR cascade: delete(%s) failed: %s; "
                "continuing — RT-025 demands the DB cascade still "
                "completes even on partial volume failure.",
                path,
                exc,
            )
    return count


# ---------------------------------------------------------------------------
# Main entry
# ---------------------------------------------------------------------------


def delete_yard_cascade(
    session: Session,
    ws: Any,
    yard_id: int,
    *,
    dry_run: bool = False,
) -> CascadeResult:
    """Delete a yard and every Lakebase row referencing it.

    Hard rails (RT-025):

    - Enumerates **every** ``yp_*`` table from
      ``SQLModel.metadata.tables`` at call time. Never hardcodes a
      shorter list. A future ``yp_*`` table is covered automatically as
      long as it has a ``yard_id`` column or a mapping in
      ``_INDIRECT_REFS``.
    - Photo prefix delete via Workspace UC Volume API when
      ``PHOTOS_VOLUME_PATH`` is configured; no-op + WARN log when empty.
    - Sets ``yp_dealer_relationships.consent_state`` to ``revoked`` and
      ``revoked_at`` to ``now`` BEFORE deleting the row, so the
      transition is observable to any downstream sync.
    - ``dry_run=True`` returns row counts but rolls back instead of
      committing — useful for ops verification before a real delete.

    **Out of scope** (Delta cascade): documented at the module top —
    Delta propagation runs via Lakehouse Sync within the sync interval;
    this function returns when Lakebase is clean and the volume prefix
    is purged.
    """
    result = CascadeResult(yard_id=yard_id, dry_run=dry_run)
    all_tables = _yp_tables()
    indirect_names, direct_names = _classify_tables(all_tables)

    # ---- 1. Resolve indirect-parent ID sets --------------------------------

    indirect_parent_ids: dict[str, list[Any]] = {}
    for child_name in indirect_names:
        _fk_col, parent_name, parent_pk = _INDIRECT_REFS[child_name]
        parent_tbl = all_tables.get(parent_name)
        if parent_tbl is None:
            logger.warning(
                "yard-pro GDPR cascade: parent table %s missing for "
                "child %s; skipping (RT-025 gap)",
                parent_name,
                child_name,
            )
            indirect_parent_ids[child_name] = []
            continue
        if "yard_id" not in parent_tbl.columns:
            logger.warning(
                "yard-pro GDPR cascade: parent %s has no yard_id column "
                "— cannot resolve children of %s (RT-025 gap)",
                parent_name,
                child_name,
            )
            indirect_parent_ids[child_name] = []
            continue
        rows = session.execute(
            sa_select(parent_tbl.c[parent_pk]).where(
                parent_tbl.c.yard_id == yard_id
            )
        ).all()
        indirect_parent_ids[child_name] = [r[0] for r in rows]

    # ---- 2. Tombstone consent state on yp_dealer_relationships ----------

    consent_count = 0
    rels_tbl = all_tables.get("yp_dealer_relationships")
    if rels_tbl is not None:
        consent_count = len(
            session.execute(
                sa_select(rels_tbl.c.id).where(
                    rels_tbl.c.yard_id == yard_id
                )
            ).all()
        )
        if not dry_run and consent_count > 0:
            session.execute(
                update(rels_tbl)
                .where(rels_tbl.c.yard_id == yard_id)
                .values(
                    consent_state="revoked",
                    revoked_at=datetime.now(timezone.utc),
                )
            )
            # Flush the UPDATE so the WAL emits the revocation event
            # before the DELETE that follows.
            session.flush()
    result.consent_revocations = consent_count

    # ---- 3. Delete indirect children ------------------------------------

    for child_name in indirect_names:
        child_tbl = all_tables[child_name]
        fk_col, _parent, _pk = _INDIRECT_REFS[child_name]
        parent_ids = indirect_parent_ids[child_name]
        if not parent_ids:
            result.tables_purged[child_name] = 0
            continue
        count = len(
            session.execute(
                sa_select(child_tbl.c[fk_col]).where(
                    child_tbl.c[fk_col].in_(parent_ids)
                )
            ).all()
        )
        if not dry_run and count > 0:
            session.execute(
                delete(child_tbl).where(
                    child_tbl.c[fk_col].in_(parent_ids)
                )
            )
        result.tables_purged[child_name] = count

    # ---- 4. Delete direct yard_id rows ----------------------------------

    for name in direct_names:
        tbl = all_tables[name]
        count = len(
            session.execute(
                sa_select(tbl.c.yard_id).where(tbl.c.yard_id == yard_id)
            ).all()
        )
        if not dry_run and count > 0:
            session.execute(delete(tbl).where(tbl.c.yard_id == yard_id))
        result.tables_purged[name] = count

    # ---- 5. Delete the root yard row ------------------------------------

    root_tbl = all_tables.get(_ROOT_TABLE)
    if root_tbl is not None:
        count = len(
            session.execute(
                sa_select(root_tbl.c.id).where(root_tbl.c.id == yard_id)
            ).all()
        )
        if not dry_run and count > 0:
            session.execute(
                delete(root_tbl).where(root_tbl.c.id == yard_id)
            )
        result.tables_purged[_ROOT_TABLE] = count

    # ---- 6. Photo prefix purge ------------------------------------------

    result.photos_purged = _purge_photo_prefix(
        ws, yard_id, dry_run=dry_run
    )

    # ---- 7. Commit or rollback ------------------------------------------

    if dry_run:
        session.rollback()
    else:
        session.commit()

    return result


__all__ = [
    "CascadeResult",
    "DATA_EXPORT_SCHEMA_VERSION",
    "delete_yard_cascade",
    "export_yard_access",
    "export_yard_portability",
]


# ---------------------------------------------------------------------------
# Art. 15 (access) + Art. 20 (portability) exports
# ---------------------------------------------------------------------------
#
# Read-side counterparts to the Art. 17 cascade. Both functions reuse the
# same ``_yp_tables()`` + ``_INDIRECT_REFS`` enumeration so a future yp_*
# table is auto-covered. Photos are referenced by URI; bytes never inline
# (RT-024). Coach transcripts that live in Delta (yard_pro_bronze) are
# referenced via a pointer block so the consumer SAR ZIP can fetch them
# out-of-band via the consent-gated path.


#: Stable schema version for the Art. 20 portability export.
#: Bump on any breaking change to the shape; document the change in
#: ``docs/projects/yard-pro-data-export-schema.md`` first.
DATA_EXPORT_SCHEMA_VERSION = "1.0.0"


def _row_to_dict(row: Any) -> dict[str, Any]:
    """Serialize a SQLAlchemy row mapping to a plain JSON-friendly dict.

    Datetimes → ISO 8601 strings, dates → ISO 8601 strings, enums →
    string value, dicts/lists pass through, everything else stringified
    only if not already JSON-safe.
    """
    from datetime import date, datetime
    from enum import Enum

    out: dict[str, Any] = {}
    for key, value in dict(row._mapping).items():
        if isinstance(value, (datetime, date)):
            out[key] = value.isoformat()
        elif isinstance(value, Enum):
            out[key] = value.value
        elif isinstance(value, (str, int, float, bool, type(None), list, dict)):
            out[key] = value
        else:
            out[key] = str(value)
    return out


def _rows_for_table(session: Session, name: str, yard_id: int) -> list[dict]:
    """Return JSON-serializable rows for one yp_* table scoped to a yard.

    Handles both direct yard_id columns and the ``_INDIRECT_REFS`` map.
    """
    from sqlalchemy import select as sa_select

    tbl = SQLModel.metadata.tables.get(name)
    if tbl is None:
        return []

    # SQLModel's session.exec is typed for ORM `Select` only; Core selects
    # against raw Table objects need session.execute() — same underlying
    # call, different overload.
    if "yard_id" in tbl.columns:
        stmt = sa_select(tbl).where(tbl.c.yard_id == yard_id)
        return [_row_to_dict(r) for r in session.execute(stmt).all()]

    if name in _INDIRECT_REFS:
        fk_col, parent_name, parent_pk = _INDIRECT_REFS[name]
        parent = SQLModel.metadata.tables.get(parent_name)
        if parent is None or "yard_id" not in parent.columns:
            return []
        parent_pk_col = parent.c[parent_pk]
        parent_ids = [
            row[0]
            for row in session.execute(
                sa_select(parent_pk_col).where(parent.c.yard_id == yard_id)
            ).all()
        ]
        if not parent_ids:
            return []
        stmt = sa_select(tbl).where(tbl.c[fk_col].in_(parent_ids))
        return [_row_to_dict(r) for r in session.execute(stmt).all()]

    return []


def _build_yard_snapshot(session: Session, yard_id: int) -> dict[str, Any]:
    """Walk SQLModel.metadata and return ``{table_name: [rows…]}`` for
    every yp_* table that references the yard (directly or indirectly)."""
    from sqlmodel import select as smselect

    yard_row = session.exec(smselect(YpYard).where(YpYard.id == yard_id)).first()
    yards = [_row_to_dict_orm(yard_row)] if yard_row is not None else []

    tables: dict[str, list[dict]] = {}
    for name in _yp_tables():
        if name == _ROOT_TABLE:
            continue
        tbl = SQLModel.metadata.tables[name]
        if "yard_id" in tbl.columns or name in _INDIRECT_REFS:
            tables[name] = _rows_for_table(session, name, yard_id)
    return {"yards": yards, "tables": tables}


def _row_to_dict_orm(row: Any) -> dict[str, Any]:
    """Same as :func:`_row_to_dict` but for SQLModel ORM rows."""
    from datetime import date, datetime
    from enum import Enum

    out: dict[str, Any] = {}
    for key, value in row.model_dump().items() if hasattr(row, "model_dump") else vars(row).items():
        if isinstance(value, (datetime, date)):
            out[key] = value.isoformat()
        elif isinstance(value, Enum):
            out[key] = value.value
        else:
            out[key] = value
    return out


def _list_photo_uris(ws: Any, yard_id: int) -> list[str]:
    """Best-effort enumeration of UC Volume photo URIs for the yard.

    Returns ``[]`` when ``PHOTOS_VOLUME_PATH`` is empty (local dev) or
    when the SDK doesn't expose ``files`` (older SDK builds). The
    function never raises — photo bytes are NEVER inlined into the
    export (RT-024 invariant).
    """
    if not PHOTOS_VOLUME_PATH or ws is None:
        return []
    prefix = f"{PHOTOS_VOLUME_PATH.rstrip('/')}/{yard_id}/"
    try:
        files = ws.files
    except AttributeError:
        return []
    try:
        entries = list(files.list_directory_contents(prefix))
    except Exception:
        return []
    uris: list[str] = []
    for entry in entries:
        path = getattr(entry, "path", None)
        if isinstance(path, str):
            uris.append(path)
    return uris


def export_yard_access(
    session: Session, ws: Any, yard_id: int
) -> dict[str, Any]:
    """GDPR Art. 15 (right of access) export.

    Returns a structured dict with EVERY yp_* row referencing this yard,
    plus a list of UC Volume photo URIs (URIs only — bytes never
    inlined, RT-024), plus a pointer to the consent-gated Delta coach
    transcript mirror. Stable top-level keys; see
    ``docs/projects/yard-pro-data-export-schema.md``.
    """
    snapshot = _build_yard_snapshot(session, yard_id)
    return {
        "article": "GDPR Art. 15",
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "yard_id": yard_id,
        "yards": snapshot["yards"],
        "tables": snapshot["tables"],
        "photos": {
            "volume_path": PHOTOS_VOLUME_PATH or "",
            "uris": _list_photo_uris(ws, yard_id),
        },
        "coach_transcripts_external": {
            "source": "yard_pro_bronze.coach_transcripts",
            "consent_gated": True,
            "retention_unconsented_days": 30,
            "retention_consented_months": 13,
            "note": (
                "Coach transcripts mirrored to Delta carry a consent_flag. "
                "Rows with consent_flag=false are hard-deleted at 30 days; "
                "consent_flag=true rows are aggregated and deleted at 13 "
                "months (GDPR purpose limitation, plan §5)."
            ),
        },
    }


def export_yard_portability(
    session: Session, ws: Any, yard_id: int
) -> dict[str, Any]:
    """GDPR Art. 20 (right to data portability) export.

    Same underlying data as Art. 15 but framed under a versioned JSON
    Schema. The top-level envelope is intentionally narrow
    (``schema_version`` / ``article`` / ``generated_at`` / ``yard``) so
    a downstream provider can identify the schema and dive into the
    yard payload. See ``docs/projects/yard-pro-data-export-schema.md``
    v1.0.0.
    """
    snapshot = _build_yard_snapshot(session, yard_id)
    return {
        "schema_version": DATA_EXPORT_SCHEMA_VERSION,
        "article": "GDPR Art. 20",
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "yard": {
            "yard_id": yard_id,
            "yards": snapshot["yards"],
            "tables": snapshot["tables"],
            "photos": {
                "volume_path": PHOTOS_VOLUME_PATH or "",
                "uris": _list_photo_uris(ws, yard_id),
            },
            "coach_transcripts_external": {
                "source": "yard_pro_bronze.coach_transcripts",
                "consent_gated": True,
                "retention_unconsented_days": 30,
                "retention_consented_months": 13,
                "note": (
                    "Coach transcripts mirrored to Delta carry a "
                    "consent_flag. Rows with consent_flag=false are "
                    "hard-deleted at 30 days; consent_flag=true rows are "
                    "aggregated and deleted at 13 months (GDPR purpose "
                    "limitation, plan §5)."
                ),
            },
        },
    }
