"""Dealer endpoints (UC6, P5).

Two distinct surfaces share this router by design (plan §12 Q6: "same
deployment, sub-route ``/dealer/*``, separate service-principal UC grants
for Klaus"):

**Consumer-side (yard owner, e.g. Martin)** — three endpoints, all
RLS-scoped by ``X-Forwarded-User`` → ``YpYard.user_key``:

  - ``POST   /dealer/relationships``              open consent (idempotent)
  - ``GET    /dealer/relationships``              caller's relationships
  - ``DELETE /dealer/relationships/{id}``         revoke (idempotent)
  - ``PATCH  /dealer/relationships/{id}/consent`` advance state (pending→granted)

**Dealer-side (Klaus)** — one endpoint, scoped by ``X-Forwarded-Dealer``:

  - ``GET /dealer/customers/anonymized``          Klaus's view, gold table

The dealer-side path mirrors the ``X-Forwarded-User`` pattern from
``rate_limit._user_or_ip`` (lessons §21): the Databricks Apps proxy is
trusted to set ``X-Forwarded-Dealer`` at the edge, never the user. In
local dev (no proxy) the test harness sets the header directly so the
RLS-scoping tests (``test_dealer_klaus_isolation``) can drive it.

Critical invariants (plan §2 + §8) — every route below enforces one:

- **Append-only consent.** The PATCH/POST/DELETE paths NEVER UPDATE
  ``consent_state`` on an existing row — they go through
  :mod:`consent_service` which inserts new rows. Regression test:
  ``test_dealer_consent_state_machine``.
- **Anonymized only.** ``GET /dealer/customers/anonymized`` returns
  ``yard_id_hash`` only, never ``yard_id``. Regression test:
  ``test_dealer_anonymization``.
- **Granted-only flow.** Klaus's view filters by latest-state-granted.
  Regression test: ``test_klaus_cannot_see_revoked_household_data``.
- **No "do it for me" affordance.** Consent transitions require an
  explicit consumer request. No internal code path opens consent on
  behalf of the consumer. (The aggregation_service is a downstream
  reader of consent state, never a writer.)
"""
from __future__ import annotations

from datetime import datetime
from typing import Optional

from fastapi import APIRouter, HTTPException, Request
from pydantic import BaseModel
from sqlmodel import select

from ....dependencies import SessionDep
from ....input_sanitize import sanitize_text
from .. import databricks_config
from ..models import (
    YardProConsentState,
    YpDealerRelationship,
    YpYard,
)
from ..services import consent_service
from ..services.aggregation_service import (
    AnonymizedRecord,
    HmacSecretMissingError,
    anonymize_consented_yards,
)
from .yards import get_caller_yard

router = APIRouter(tags=["yard-pro"])


# ---------------------------------------------------------------------------
# I/O schemas
# ---------------------------------------------------------------------------


class YpDealerRelationshipOut(BaseModel):
    """One relationship row exposed to the consumer cockpit.

    Designed for the "Share anonymized yard data with my dealer" toggle
    in the cockpit UI: ``consent_state`` drives the toggle's three-state
    rendering (none/pending → "not connected", granted → "sharing",
    revoked → "not connected").
    """

    id: int
    yard_id: int
    dealer_id: str
    consent_state: YardProConsentState
    consent_at: Optional[datetime]
    revoked_at: Optional[datetime]
    created_at: datetime


class YpDealerRelationshipCreate(BaseModel):
    """``POST /dealer/relationships`` payload — household opts in."""

    dealer_id: str


class YpDealerConsentTransitionIn(BaseModel):
    """``PATCH /dealer/relationships/{id}/consent`` payload.

    The frontend specifies the target state explicitly so the API
    surface is symmetric: the same endpoint can advance pending →
    granted OR ``granted → revoked``. Re-opt-in (revoked → pending)
    also flows through this path.
    """

    target_state: YardProConsentState


class YpDealerCustomerSummaryOut(BaseModel):
    """One row of the dealer-side anonymized view (UC6).

    Shape matches ``yard_pro_gold.dealer_customer_summary`` (plan §5;
    seeded in ``seed_uc_tables.py``). Field set intentionally omits
    ``yard_id``, ``user_key``, raw ``lat``/``lng``, plant species, and
    every other PII column — only the HMAC-derived hash + bucketed
    fields are exposed.
    """

    yard_id_hash: str
    dealer_id: str
    region_bucket: str
    yard_size_bucket: str
    tool_inventory_hash: str
    robotic_mower_age_years: int
    last_service_event_age_days: int
    consent_state: str


# ---------------------------------------------------------------------------
# Dealer-side tenancy helper — mirrors yards._resolve_user_key
# ---------------------------------------------------------------------------


_LOCAL_DEV_FALLBACK_DEALER_ID = "dealer_stuttgart_nord"


def _resolve_dealer_id(request: Request) -> str:
    """Resolve Klaus's dealer identity from the auth-proxy header.

    Mirrors :func:`yards._resolve_user_key`: trust the proxy-set
    ``X-Forwarded-Dealer`` header in production (the Databricks Apps
    proxy is the only writer; never user-set). In local dev (no proxy)
    fall back to the seeded ``dealer_stuttgart_nord`` so a bare ``curl``
    to ``/dealer/customers/anonymized`` returns something useful.
    """
    value = request.headers.get("X-Forwarded-Dealer")
    if value:
        return value
    return _LOCAL_DEV_FALLBACK_DEALER_ID


def _to_relationship_out(row: YpDealerRelationship) -> YpDealerRelationshipOut:
    return YpDealerRelationshipOut(
        id=row.id or 0,
        yard_id=row.yard_id,
        dealer_id=row.dealer_id,
        consent_state=row.consent_state,
        consent_at=row.consent_at,
        revoked_at=row.revoked_at,
        created_at=row.created_at,
    )


def _resolve_relationship_pair(
    db, request: Request, relationship_id: int
) -> tuple[YpDealerRelationship, YpYard]:
    """Look up a relationship row by id, assert the caller owns the yard.

    Returns the row + the caller's yard. Raises 404 on cross-tenant
    access (never 403 — leak as little as possible about which
    relationship IDs exist, same convention as
    :func:`yards.assert_yard_owned_by_caller`).
    """
    yard = get_caller_yard(request, db)
    row = db.get(YpDealerRelationship, relationship_id)
    if row is None or row.yard_id != yard.id:
        raise HTTPException(status_code=404, detail="Relationship not found")
    return row, yard


# ---------------------------------------------------------------------------
# Consumer-side endpoints — RLS by X-Forwarded-User
# ---------------------------------------------------------------------------


@router.post(
    "/dealer/relationships",
    response_model=YpDealerRelationshipOut,
    operation_id="yp_createDealerRelationship",
    status_code=201,
)
def create_dealer_relationship(
    request: Request,
    payload: YpDealerRelationshipCreate,
    db: SessionDep,
) -> YpDealerRelationshipOut:
    """Open a dealer relationship for the caller's yard.

    State machine entry point (consent_service.open_relationship):

    - First call → transitions ``none_`` to ``pending``; status 201.
    - Repeat call while ``pending`` or ``granted`` → no-op (idempotent);
      returns the latest row.
    - Repeat call while ``revoked`` → re-opt-in via a new
      ``revoked → pending`` row.

    The dealer_id is sanitized at the API boundary (lessons §20). The
    yard_id is taken from the caller's resolved yard; any client-
    supplied yard_id would be ignored — the model has no such field,
    closing the RT-016 body-override vector.
    """
    yard = get_caller_yard(request, db)
    cleaned = sanitize_text(payload.dealer_id)
    dealer_id = cleaned if isinstance(cleaned, str) else ""
    if not dealer_id:
        raise HTTPException(status_code=400, detail="dealer_id is required")

    row, _created = consent_service.open_relationship(
        db, yard_id=yard.id or 0, dealer_id=dealer_id
    )
    db.commit()
    db.refresh(row)
    return _to_relationship_out(row)


@router.get(
    "/dealer/relationships",
    response_model=list[YpDealerRelationshipOut],
    operation_id="yp_listDealerRelationships",
)
def list_dealer_relationships(
    request: Request, db: SessionDep
) -> list[YpDealerRelationshipOut]:
    """List the caller's dealer relationships (latest row per dealer).

    RLS-scoped to the caller's yard. Returns ONE row per dealer_id —
    the most recent transition. The full event-sourced history is not
    exposed via the API; ``consent_service.list_for_yard`` is the
    deduplicator.
    """
    yard = get_caller_yard(request, db)
    latest = consent_service.list_for_yard(db, yard.id or 0)
    return [_to_relationship_out(r) for r in latest]


@router.patch(
    "/dealer/relationships/{relationship_id}/consent",
    response_model=YpDealerRelationshipOut,
    operation_id="yp_setDealerConsent",
)
def set_dealer_consent(
    relationship_id: int,
    request: Request,
    payload: YpDealerConsentTransitionIn,
    db: SessionDep,
) -> YpDealerRelationshipOut:
    """Advance the consent state machine for a relationship.

    The new state is supplied by the caller; consent_service validates
    against the transition table:

    - ``pending → granted`` — household confirms after first POST.
    - ``granted → revoked`` — household pulls consent.
    - ``revoked → pending`` — household re-opts-in.

    Returns the **new** row (event-sourced — never the old one); the
    consumer cockpit's toggle re-renders from the response. Invalid
    transitions raise 400 with both states named in the error body
    so a downstream log scrape can group them.
    """
    row, yard = _resolve_relationship_pair(db, request, relationship_id)
    try:
        new_row = consent_service.transition(
            db,
            yard_id=yard.id or 0,
            dealer_id=row.dealer_id,
            target_state=payload.target_state,
        )
    except consent_service.ConsentTransitionError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    db.commit()
    db.refresh(new_row)
    return _to_relationship_out(new_row)


@router.delete(
    "/dealer/relationships/{relationship_id}",
    response_model=YpDealerRelationshipOut,
    operation_id="yp_revokeDealerRelationship",
)
def revoke_dealer_relationship(
    relationship_id: int, request: Request, db: SessionDep
) -> YpDealerRelationshipOut:
    """Revoke consent for a relationship (consumer convenience path).

    Always returns 200 with the latest row:

    - ``granted`` → transition to ``revoked``; returns the new row.
    - ``pending`` → no-op; returns the latest pending row.
    - ``revoked`` → no-op (idempotent); returns the latest revoked row.

    This is intentionally forgiving: a privacy-first UI should never
    error on "you tried to revoke something already revoked".
    """
    row, yard = _resolve_relationship_pair(db, request, relationship_id)
    latest, _changed = consent_service.revoke_relationship(
        db, yard_id=yard.id or 0, dealer_id=row.dealer_id
    )
    db.commit()
    db.refresh(latest)
    return _to_relationship_out(latest)


# ---------------------------------------------------------------------------
# Dealer-side endpoint — RLS by X-Forwarded-Dealer
# ---------------------------------------------------------------------------


@router.get(
    "/dealer/customers/anonymized",
    response_model=list[YpDealerCustomerSummaryOut],
    operation_id="yp_listDealerCustomersAnonymized",
)
def list_dealer_customers_anonymized(
    request: Request, db: SessionDep
) -> list[YpDealerCustomerSummaryOut]:
    """Klaus's view: anonymized customer summaries for HIS dealer scope.

    RLS: scoped by ``X-Forwarded-Dealer`` → ``dealer_id`` so Klaus only
    sees rows for his dealer code. Filter applies AFTER the
    aggregation_service produces records; the producer itself reads
    consent_state on every batch and excludes households with
    ``consent_state != 'granted'`` (RT-012 + RT-022).

    The returned rows carry **only** ``yard_id_hash`` — never the raw
    ``yard_id``. This is the irreversible-at-ingest rail at the
    surface: even a dealer who somehow obtained a raw yard_id couldn't
    cross-reference it to a hash without the rotating HMAC secret.

    Failure mode when ``DEALER_HMAC_SECRET`` is unset: 503 with a clear
    message. The aggregation_service refuses to emit hashes against an
    empty secret (would produce a known-plaintext hash that defeats the
    irreversibility rail).
    """
    dealer_id = _resolve_dealer_id(request)
    if not databricks_config.DEALER_HMAC_SECRET:
        # Match the "not configured" pattern (lessons §18) — clear 503,
        # never a 500. The dealer panel UI renders an empty-state.
        raise HTTPException(
            status_code=503,
            detail=(
                "Dealer anonymization not configured: set "
                "YARD_PRO_DEALER_HMAC_SECRET per the runbook §12."
            ),
        )
    try:
        records = anonymize_consented_yards(db)
    except HmacSecretMissingError as exc:
        raise HTTPException(status_code=503, detail=str(exc)) from exc
    return [
        _to_summary_out(r) for r in records if r.dealer_id == dealer_id
    ]


def _to_summary_out(record: AnonymizedRecord) -> YpDealerCustomerSummaryOut:
    """Project an :class:`AnonymizedRecord` to the API response shape.

    The two shapes are intentionally parallel — they share the same
    fields and the projection is a 1:1 copy. We keep them as separate
    types so the producer side (aggregation_service) stays decoupled
    from the FastAPI response_model wiring.
    """
    return YpDealerCustomerSummaryOut(
        yard_id_hash=record.yard_id_hash,
        dealer_id=record.dealer_id,
        region_bucket=record.region_bucket,
        yard_size_bucket=record.yard_size_bucket,
        tool_inventory_hash=record.tool_inventory_hash,
        robotic_mower_age_years=record.robotic_mower_age_years,
        last_service_event_age_days=record.last_service_event_age_days,
        consent_state=record.consent_state,
    )


__all__ = [
    "router",
]
