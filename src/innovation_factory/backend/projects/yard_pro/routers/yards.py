"""Yard endpoints — single source of truth for the calling user's yard
plus the UC1 cockpit anchor payload.

Tenancy rail (plan §8, RT-016): every read filters by the caller's
``user_key`` (resolved from the ``X-Forwarded-User`` header — the
Databricks Apps proxy is the only writer; never user-set, lessons §21).
Other yard-pro routers import :func:`_resolve_user_key` and
:func:`get_caller_yard` from this module so the resolution rule is
defined in exactly one place.
"""
from __future__ import annotations

from datetime import datetime, timezone
from typing import Optional

from databricks.sdk import WorkspaceClient
from fastapi import APIRouter, Depends, HTTPException, Request
from pydantic import BaseModel
from sqlmodel import select

from ....dependencies import SessionDep, get_obo_ws
from ..services.gdpr_service import (
    delete_yard_cascade,
    export_yard_access,
    export_yard_portability,
)
from ..services.telemetry_service import (
    list_nudges_for_yard,
    list_readiness_for_yard,
)
from ..models import (
    YardProActionType,
    YardProCalendarStatus,
    YardProDiagnosisStatus,
    YpActionLog,
    YpActionLogOut,
    YpCalendarEntry,
    YpCalendarEntryOut,
    YpCockpitOut,
    YpConsumable,
    YpConsumableOut,
    YpDiagnosis,
    YpDiagnosisOut,
    YpPlant,
    YpPlantOut,
    YpTool,
    YpToolOut,
    YpToolReadinessOut,
    YpYard,
    YpYardOut,
)

router = APIRouter(tags=["yard-pro"])


# ---------------------------------------------------------------------------
# GDPR Art. 17 response shape — see services/gdpr_service.py for the cascade.
# ---------------------------------------------------------------------------


class YpDeleteYardOut(BaseModel):
    """Response payload for ``DELETE /yards/{yard_id}``.

    - ``deleted``: ``true`` on a real delete; ``false`` on a dry-run.
    - ``tables_purged``: per-table row counts that were (or would be)
      removed by the cascade — derived from ``SQLModel.metadata`` so
      future ``yp_*`` tables are auto-covered (RT-025 mitigation).
    - ``photos_purged``: UC Volume photo files removed under
      ``<PHOTOS_VOLUME_PATH>/<yard_id>/``. Zero when the volume path is
      not configured (local dev).
    - ``consent_revocations``: ``yp_dealer_relationships`` rows that were
      transitioned to ``consent_state=revoked`` before deletion.
    - ``dry_run``: echoes the request flag.
    """

    yard_id: int
    deleted: bool
    tables_purged: dict[str, int]
    photos_purged: int
    consent_revocations: int
    dry_run: bool


# ---------------------------------------------------------------------------
# Tenancy helpers — shared by the other yard-pro routers
# ---------------------------------------------------------------------------

#: Local-dev fallback user_key. Matches the seed (Martin's Stuttgart yard) so
#: ``curl ... -H 'X-Forwarded-User: martin@yard-pro.local'`` AND a bare
#: ``curl`` both work in ``apx dev start``. The Databricks Apps proxy
#: never lets a user spoof this header, so trusting it in production is
#: safe (lessons §21).
_LOCAL_DEV_FALLBACK_USER_KEY = "martin@yard-pro.local"


def _resolve_user_key(request: Request) -> str:
    """Resolve the calling user's identity from the auth-proxy header.

    Mirrors :func:`backend.rate_limit._user_or_ip` precedence:
    ``X-Forwarded-User`` first, then ``X-Forwarded-Preferred-Username``.
    In local dev (no proxy) falls back to the seeded Martin key so a
    bare ``curl`` to ``yards/me`` returns something useful.
    """
    for header in ("X-Forwarded-User", "X-Forwarded-Preferred-Username"):
        value = request.headers.get(header)
        if value:
            return value
    return _LOCAL_DEV_FALLBACK_USER_KEY


def get_caller_yard(request: Request, db) -> YpYard:
    """Return the yard belonging to the calling user.

    Raises 404 when no yard is seeded for the caller (the cockpit UI
    surfaces this as "no yard yet" rather than a 500). Used by every
    other yard-pro router that needs to enforce RLS.
    """
    user_key = _resolve_user_key(request)
    yard = db.exec(select(YpYard).where(YpYard.user_key == user_key)).first()
    if not yard:
        raise HTTPException(status_code=404, detail="No yard found for caller")
    return yard


def assert_yard_owned_by_caller(request: Request, db, yard_id: int) -> YpYard:
    """Look up a yard by ID and assert the caller owns it.

    Returns 404 (not 403) on cross-household access — the goal is to
    leak as little information as possible about other households'
    yard IDs. RT-016 cross-tenant isolation test enumerates these
    attack vectors.
    """
    user_key = _resolve_user_key(request)
    yard = db.get(YpYard, yard_id)
    if yard is None or yard.user_key != user_key:
        raise HTTPException(status_code=404, detail="Yard not found")
    return yard


# ---------------------------------------------------------------------------
# Routes
# ---------------------------------------------------------------------------


@router.get(
    "/yards/me",
    response_model=YpYardOut,
    operation_id="yp_getMyYard",
)
def get_my_yard(request: Request, db: SessionDep) -> YpYardOut:
    """Return the calling user's yard (one yard per user in P0)."""
    yard = get_caller_yard(request, db)
    return YpYardOut(
        id=yard.id or 0,
        display_name=yard.display_name,
        region_code=yard.region_code,
        lat=yard.lat,
        lng=yard.lng,
        size_m2=yard.size_m2,
        yard_metadata=yard.yard_metadata,
    )


@router.get(
    "/yards/{yard_id}/cockpit",
    response_model=YpCockpitOut,
    operation_id="yp_getCockpit",
)
def get_cockpit(yard_id: int, request: Request, db: SessionDep) -> YpCockpitOut:
    """One-shot UC1 anchor payload: yard + plants + tools + consumables +
    upcoming/overdue calendar + recent actions + recent diagnoses.

    Designed for <1s first paint per the demo gate in plan §2; the
    cockpit's child cards each take a slice of this response instead of
    issuing N parallel fetches on cold load. RLS enforced via
    :func:`assert_yard_owned_by_caller` — never returns another
    household's data even if the caller knows their yard_id.
    """
    yard = assert_yard_owned_by_caller(request, db, yard_id)
    now = datetime.now(timezone.utc)

    plants = list(
        db.exec(
            select(YpPlant).where(YpPlant.yard_id == yard.id).order_by(YpPlant.id)  # type: ignore[invalid-argument-type]
        ).all()
    )
    tools = list(
        db.exec(
            select(YpTool).where(YpTool.yard_id == yard.id).order_by(YpTool.id)  # type: ignore[invalid-argument-type]
        ).all()
    )
    consumables = list(
        db.exec(
            select(YpConsumable)
            .where(YpConsumable.yard_id == yard.id)
            .order_by(YpConsumable.id)  # type: ignore[invalid-argument-type]
        ).all()
    )

    upcoming = list(
        db.exec(
            select(YpCalendarEntry)
            .where(
                YpCalendarEntry.yard_id == yard.id,
                YpCalendarEntry.scheduled_at >= now,
                YpCalendarEntry.status == YardProCalendarStatus.planned,
            )
            .order_by(YpCalendarEntry.scheduled_at)  # type: ignore[invalid-argument-type]
            .limit(20)
        ).all()
    )
    overdue = list(
        db.exec(
            select(YpCalendarEntry)
            .where(
                YpCalendarEntry.yard_id == yard.id,
                YpCalendarEntry.scheduled_at < now,
                YpCalendarEntry.status == YardProCalendarStatus.planned,
            )
            .order_by(YpCalendarEntry.scheduled_at.desc())  # type: ignore[unresolved-attribute]
            .limit(20)
        ).all()
    )

    recent_actions = list(
        db.exec(
            select(YpActionLog)
            .where(YpActionLog.yard_id == yard.id)
            .order_by(YpActionLog.occurred_at.desc())  # type: ignore[unresolved-attribute]
            .limit(20)
        ).all()
    )
    recent_diagnoses = list(
        db.exec(
            select(YpDiagnosis)
            .where(YpDiagnosis.yard_id == yard.id)
            .order_by(YpDiagnosis.created_at.desc())  # type: ignore[unresolved-attribute]
            .limit(10)
        ).all()
    )

    return YpCockpitOut(
        yard=YpYardOut(
            id=yard.id or 0,
            display_name=yard.display_name,
            region_code=yard.region_code,
            lat=yard.lat,
            lng=yard.lng,
            size_m2=yard.size_m2,
            yard_metadata=yard.yard_metadata,
        ),
        plants=[
            YpPlantOut(
                id=p.id or 0,
                yard_id=p.yard_id,
                species=p.species,
                variety=p.variety,
                planted_at=p.planted_at,
                notes=p.notes,
            )
            for p in plants
        ],
        tools=[
            YpToolOut(
                id=t.id or 0,
                yard_id=t.yard_id,
                kind=t.kind,
                display_name=t.display_name,
                model_year=t.model_year,
                battery_family=t.battery_family,
                last_serviced_at=t.last_serviced_at,
            )
            for t in tools
        ],
        consumables=[
            YpConsumableOut(
                id=c.id or 0,
                yard_id=c.yard_id,
                kind=c.kind,
                display_name=c.display_name,
                quantity=c.quantity,
                unit=c.unit,
                last_restock_at=c.last_restock_at,
            )
            for c in consumables
        ],
        upcoming_calendar=[
            YpCalendarEntryOut(
                id=e.id or 0,
                yard_id=e.yard_id,
                title=e.title,
                description=e.description,
                scheduled_at=e.scheduled_at,
                target_plant_id=e.target_plant_id,
                tool_id=e.tool_id,
                status=e.status,
            )
            for e in upcoming
        ],
        overdue_calendar=[
            YpCalendarEntryOut(
                id=e.id or 0,
                yard_id=e.yard_id,
                title=e.title,
                description=e.description,
                scheduled_at=e.scheduled_at,
                target_plant_id=e.target_plant_id,
                tool_id=e.tool_id,
                status=e.status,
            )
            for e in overdue
        ],
        recent_actions=[
            YpActionLogOut(
                id=a.id or 0,
                yard_id=a.yard_id,
                action_type=a.action_type,
                target_plant_id=a.target_plant_id,
                tool_id=a.tool_id,
                consumable_id=a.consumable_id,
                occurred_at=a.occurred_at,
                notes=a.notes,
                source=a.source,
                human_confirmed_at=a.human_confirmed_at,
            )
            for a in recent_actions
        ],
        recent_diagnoses=[
            YpDiagnosisOut(
                id=d.id or 0,
                yard_id=d.yard_id,
                photo_uri=d.photo_uri,
                model_version=d.model_version,
                predictions=d.predictions,
                top_label=d.top_label,
                top_confidence=d.top_confidence,
                accepted_label=d.accepted_label,
                status=d.status,
                created_at=d.created_at,
            )
            for d in recent_diagnoses
        ],
        tool_readiness=[
            YpToolReadinessOut(
                tool_id=r.tool_id,
                battery_pct=r.battery_pct,
                blade_hours_since_sharpening=r.blade_hours_since_sharpening,
                last_session_at=r.last_session_at,
                last_event_type=r.last_event_type,
                last_event_at=r.last_event_at,
                payload=r.payload,
                updated_at=r.updated_at,
            )
            for r in list_readiness_for_yard(db, yard.id or 0)
        ],
        nudges=list_nudges_for_yard(db, yard.id or 0),
    )


@router.delete(
    "/yards/{yard_id}",
    response_model=YpDeleteYardOut,
    operation_id="yp_deleteYard",
)
def delete_yard(
    yard_id: int,
    request: Request,
    db: SessionDep,
    ws: WorkspaceClient = Depends(get_obo_ws),
    dry_run: bool = False,
) -> YpDeleteYardOut:
    """GDPR Art. 17 (right to be forgotten) — delete one yard's data.

    Cascade detail and out-of-scope boundary live in
    :func:`services.gdpr_service.delete_yard_cascade`. Summary:

    - Lakebase: every ``yp_*`` row referencing this yard (enumerated
      from ``SQLModel.metadata.tables`` — RT-025 mitigation).
    - UC Volume: ``<PHOTOS_VOLUME_PATH>/<yard_id>/`` prefix (no-op when
      ``PHOTOS_VOLUME_PATH`` is unset in local dev).
    - Consent: ``yp_dealer_relationships`` rows are tombstoned to
      ``consent_state=revoked`` (with ``revoked_at``) and flushed
      BEFORE the row is deleted, so the transition is visible to any
      downstream Lakehouse Sync.
    - Out of scope here: Delta Bronze/Silver/Gold propagation — handled
      by Lakehouse Sync within the sync interval.

    RLS: only the yard's owner can delete it. Cross-tenant attempts
    return 404 (never 403 — leak as little as possible about other
    households' yard IDs; same convention as
    :func:`assert_yard_owned_by_caller`).

    Idempotency: a second DELETE on the same yard returns 404 because
    the row no longer exists.

    ``?dry_run=true`` returns the same response shape with the row
    counts that *would* be deleted, plus ``dry_run=true`` and
    ``deleted=false``. No DB writes occur and no volume files are
    removed.
    """
    yard = assert_yard_owned_by_caller(request, db, yard_id)
    assert yard.id is not None  # narrowed by the helper
    result = delete_yard_cascade(db, ws, yard.id, dry_run=dry_run)
    return YpDeleteYardOut(
        yard_id=result.yard_id,
        deleted=not result.dry_run,
        tables_purged=result.tables_purged,
        photos_purged=result.photos_purged,
        consent_revocations=result.consent_revocations,
        dry_run=result.dry_run,
    )


class YpYardCoachTranscriptsExternal(BaseModel):
    """Pointer to the consent-gated Delta coach transcript mirror
    (Art. 15 + Art. 20). The transcripts themselves live in
    ``yard_pro_bronze.coach_transcripts`` — see plan §5 retention."""

    source: str
    consent_gated: bool
    retention_unconsented_days: int
    retention_consented_months: int
    note: str


class YpYardExportPhotos(BaseModel):
    volume_path: str
    uris: list[str]


class YpYardPortabilityPayload(BaseModel):
    yard_id: int
    yards: list[dict]
    tables: dict[str, list[dict]]
    photos: YpYardExportPhotos
    coach_transcripts_external: YpYardCoachTranscriptsExternal


class YpYardPortabilityExportOut(BaseModel):
    """Stable Art. 20 envelope. The bytes-level schema is documented in
    ``docs/projects/yard-pro-data-export-schema.md``; this Pydantic
    model is the in-process validator for third-party importers."""

    schema_version: str
    article: str
    generated_at: str
    yard: YpYardPortabilityPayload


class YpYardAccessExportOut(BaseModel):
    """Art. 15 envelope (stable top-level keys; flexible `tables` shape).

    The dict-typed fields (``tables`` and the row lists) are intentional
    — table coverage is derived from SQLModel.metadata at request time,
    so a static Pydantic type would silently lag the source of truth.
    Shape stability is enforced by
    ``test_export_schema_keys_stable_regression``."""

    article: str
    generated_at: str
    yard_id: int
    yards: list[dict]
    tables: dict[str, list[dict]]
    photos: YpYardExportPhotos
    coach_transcripts_external: YpYardCoachTranscriptsExternal


@router.get(
    "/yards/{yard_id}/export/access",
    response_model=YpYardAccessExportOut,
    operation_id="yp_exportYardAccess",
)
def export_yard_access_endpoint(
    yard_id: int,
    request: Request,
    db: SessionDep,
    ws: WorkspaceClient = Depends(get_obo_ws),
) -> dict:
    """GDPR Art. 15 (right of access) export.

    Returns a structured snapshot of every ``yp_*`` row referencing the
    yard, plus UC Volume photo URIs (URIs only — bytes never inlined,
    RT-024), plus a pointer to the consent-gated Delta coach transcript
    mirror. RLS enforced via :func:`assert_yard_owned_by_caller`.

    No ``response_model`` because the snapshot shape includes free-form
    ``tables`` keyed by SQLModel.metadata at request time — a Pydantic
    static schema would drift from the source of truth. Shape stability
    is regression-tested in
    ``tests/projects/yard_pro/test_gdpr_art15_access_export.py``.
    """
    yard = assert_yard_owned_by_caller(request, db, yard_id)
    assert yard.id is not None
    return export_yard_access(db, ws, yard.id)


@router.get(
    "/yards/{yard_id}/export/portability",
    response_model=YpYardPortabilityExportOut,
    operation_id="yp_exportYardPortability",
)
def export_yard_portability_endpoint(
    yard_id: int,
    request: Request,
    db: SessionDep,
    ws: WorkspaceClient = Depends(get_obo_ws),
) -> dict:
    """GDPR Art. 20 (right to data portability) export.

    Same underlying data as Art. 15 but framed under a versioned JSON
    Schema (see ``docs/projects/yard-pro-data-export-schema.md``). RLS
    same as the access export.
    """
    yard = assert_yard_owned_by_caller(request, db, yard_id)
    assert yard.id is not None
    return export_yard_portability(db, ws, yard.id)


__all__ = [
    "router",
    "_resolve_user_key",
    "get_caller_yard",
    "assert_yard_owned_by_caller",
]
