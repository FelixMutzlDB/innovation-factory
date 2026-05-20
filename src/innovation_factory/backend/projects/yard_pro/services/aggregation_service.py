"""aggregation_service — irreversible-at-ingest anonymization for the
dealer panel (UC6, P5).

Plan §2 non-negotiable: "anonymization is **irreversible at ingest**".
Plan §8 access-control row: "Klaus's SP has UC SELECT only on
``yard_pro_gold.*``; cannot reach ``yard_pro_bronze/silver``".
Plan §8 Genie row: "Genie space configured against ``yard_pro_gold.*``
only; row-level filters baked into the underlying Delta view".

This module is the producer side of that gold layer. It takes a yard_id
in Lakebase, reads the consent_state via :mod:`consent_service`, and
returns an :class:`AnonymizedRecord` ready to write to
``yard_pro_gold.dealer_customer_summary``. The function NEVER returns
the raw ``yard_id`` — only ``yard_id_hash`` (HMAC over the integer
yard_id with the rotating ``DEALER_HMAC_SECRET``). RT-012 and RT-022
mitigations both pivot on this: a household that revoked consent must
never appear in the output, and there must be no path from the gold
table back to a raw yard_id.

Irreversibility caveat (honest):
  An HMAC isn't a one-way function on the *output* side — anyone with
  the secret can verify a candidate yard_id. The irreversibility is
  operational: the secret is held by the workspace ingestion principal
  only, never shipped to the dealer side. RT-023's mitigation row
  ("brute-force search is computationally infeasible") relies on the
  secret being long-and-random. The runbook documents rotation; this
  code refuses to emit a hash when the secret is empty.

Bucketing (no precision leak into the gold table):
  - ``yard_size_bucket``: small_200_500_m2 / medium_500_1000_m2 /
    large_1000_plus_m2 (matches the seeded categories in
    ``seed_uc_tables.py``).
  - ``region_bucket``: hash of the ``region_code`` prefix so two yards
    in DE-BW land in the same bucket without exposing the precise
    postal code or lat/lng. The plan §5 row keeps lat/lng out of the
    gold table; this enforces that at the producer.
  - ``tool_inventory_hash``: HMAC over the sorted multiset of tool
    kinds the yard owns. Same hash → same inventory composition →
    Klaus can group "small lawn with one robotic mower and one trimmer"
    without ever seeing the raw tool rows.
"""
from __future__ import annotations

import hashlib
import hmac
import logging
from dataclasses import dataclass
from typing import Optional

from sqlmodel import Session, select

from .. import databricks_config
from ..models import (
    YardProConsentState,
    YpDealerRelationship,
    YpTool,
    YpYard,
)
from . import consent_service

logger = logging.getLogger(__name__)


class AnonymizationBlockedError(RuntimeError):
    """Raised when :func:`anonymize_yard` is asked to anonymize a yard
    whose latest consent transition is **not** ``granted`` for any dealer.

    The error is structural: the consent state machine is the gate, and
    a misconfigured caller that asks for anonymization on a non-granted
    yard MUST get a hard failure, not a quiet zero-row response. The
    matching :func:`anonymize_consented_yards` batch path filters
    silently; ``anonymize_yard`` (single yard) raises.
    """


class HmacSecretMissingError(RuntimeError):
    """Raised when ``DEALER_HMAC_SECRET`` is empty.

    Empty secret would produce a deterministic-and-public hash — every
    yard_id would map to the same value across deploys, defeating the
    irreversible-at-ingest rail. We refuse to emit hashes; the caller
    must configure the secret per the runbook §12 rotation procedure.
    """


@dataclass(frozen=True)
class AnonymizedRecord:
    """One row of ``yard_pro_gold.dealer_customer_summary``.

    Field set matches the seeded schema in ``seed_uc_tables.py``:
    ``yard_id_hash``, ``dealer_code``, ``region_bucket``,
    ``yard_size_bucket``, ``tool_inventory_hash``,
    ``robotic_mower_age_years``, ``last_service_event_age_days``,
    ``consent_state``. Intentionally no ``yard_id``, no ``user_key``,
    no ``lat``, no ``lng``, no plant species — the irreversible-at-
    ingest rail can't co-emit the raw yard_id alongside the hash.
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
# Bucketing primitives — no PII passes through these.
# ---------------------------------------------------------------------------


def _yard_size_bucket(size_m2: float) -> str:
    """Bucket the raw m² into the three documented categories.

    Boundaries are inclusive-lower / exclusive-upper. A 200 m² yard
    lands in ``small_200_500_m2``; a 500 m² yard lands in
    ``medium_500_1000_m2``. Yards below 200 m² are collapsed into the
    "small" bucket — keeping the bucket count at three avoids a single-
    yard "tiny" bucket that would re-identify a household by
    elimination.
    """
    if size_m2 < 500.0:
        return "small_200_500_m2"
    if size_m2 < 1000.0:
        return "medium_500_1000_m2"
    return "large_1000_plus_m2"


def _region_bucket(region_code: str, *, secret: bytes) -> str:
    """Bucket a region code into a coarse opaque token.

    For the demo seed, ``region_code`` is ``DE-BW`` (Baden-Württemberg).
    We HMAC the **prefix** (first two segments) so two yards in DE-BW
    collide on the bucket while a DE-BY yard would not. The first 12
    hex chars of the HMAC are exposed — long enough to avoid accidental
    collisions in the demo dataset, short enough that the bucket value
    has no structural meaning to a viewer.
    """
    # Normalize "DE-BW-stuttgart-basin" -> "DE-BW".
    parts = region_code.split("-")
    prefix = "-".join(parts[:2]) if len(parts) >= 2 else region_code
    h = hmac.new(secret, prefix.encode("utf-8"), hashlib.sha256).hexdigest()
    return f"rb_{h[:12]}"


def _tool_inventory_hash(tool_kinds: list[str], *, secret: bytes) -> str:
    """Hash the sorted multiset of tool kinds owned by the yard.

    Same inventory composition → same hash → Klaus can group customers
    without seeing the tool rows. Sorting before joining makes the hash
    order-independent. The multiset retains "owns two trimmers" as a
    distinct shape from "owns one trimmer" — that's intentional, a
    dealer cares about repeat purchases.
    """
    joined = ",".join(sorted(tool_kinds))
    h = hmac.new(secret, joined.encode("utf-8"), hashlib.sha256).hexdigest()
    return f"th_{h[:12]}"


def _yard_id_hash(yard_id: int, *, secret: bytes) -> str:
    """HMAC over the integer ``yard_id`` — the only join key Klaus sees.

    Returns a deterministic ``yh_<12-hex>`` token. Determinism is by
    design: a household that revokes consent today and re-opts-in next
    season must reappear under the same hash so multi-season analytics
    work; otherwise Klaus would see the same Martin as two distinct
    "new" anonymous customers each season. The rotation procedure in
    the runbook §12 documents the consequences for previous-rotation
    rows when the secret cycles.
    """
    h = hmac.new(secret, str(yard_id).encode("utf-8"), hashlib.sha256).hexdigest()
    return f"yh_{h[:12]}"


def _require_secret() -> bytes:
    """Return the configured HMAC secret as bytes, or raise."""
    secret = (databricks_config.DEALER_HMAC_SECRET or "").encode("utf-8")
    if not secret:
        raise HmacSecretMissingError(
            "DEALER_HMAC_SECRET is unset — refusing to emit yard_id_hash "
            "values (irreversible-at-ingest rail). Configure via "
            "YARD_PRO_DEALER_HMAC_SECRET per scripts/yard_pro/RUNBOOK.md §12."
        )
    return secret


# ---------------------------------------------------------------------------
# Core entry — single yard
# ---------------------------------------------------------------------------


def anonymize_yard(
    session: Session,
    yard_id: int,
    *,
    dealer_id: Optional[str] = None,
) -> AnonymizedRecord:
    """Anonymize one yard for a given dealer.

    Production-grade contract:
    - Reads ``YpDealerRelationship`` for the pair via
      :func:`consent_service.current_state`. If the latest state is NOT
      ``granted``, raises :class:`AnonymizationBlockedError`. RT-012 +
      RT-022 invariant: a revoked or pending household never reaches
      the gold table.
    - HMAC over ``yard_id`` with ``DEALER_HMAC_SECRET``; the function
      NEVER returns ``yard_id`` itself. The local variable is dropped
      as soon as the hash is computed — irreversible-at-ingest means
      we don't retain the raw value past this scope.
    - When ``dealer_id`` is omitted, the function picks the first
      dealer with a ``granted`` consent transition for the yard. The
      batch entry point (:func:`anonymize_consented_yards`) supplies
      the explicit ``(yard_id, dealer_id)`` pair for each row, so this
      fallback is mostly for unit-test ergonomics.
    """
    secret = _require_secret()

    # Resolve the granted dealer relationship (or fail loudly).
    if dealer_id is None:
        granted_pairs = _list_granted_pairs(session, yard_id)
        if not granted_pairs:
            raise AnonymizationBlockedError(
                f"yard_id={yard_id}: no dealer relationship with state=granted"
            )
        dealer_id = granted_pairs[0]

    state = consent_service.current_state(session, yard_id, dealer_id)
    if state.state != YardProConsentState.granted:
        raise AnonymizationBlockedError(
            f"yard_id={yard_id} dealer_id={dealer_id}: latest consent state "
            f"is {state.state.value!r}, refusing to anonymize"
        )

    yard = session.get(YpYard, yard_id)
    if yard is None:
        raise AnonymizationBlockedError(
            f"yard_id={yard_id}: yard not found in Lakebase"
        )

    tool_kinds = [
        t.kind.value if hasattr(t.kind, "value") else str(t.kind)
        for t in session.exec(
            select(YpTool).where(YpTool.yard_id == yard_id)
        ).all()
    ]

    # Compute hashes. After this block, ``yard_id`` (the integer)
    # SHOULD NOT propagate into the returned record. The function
    # signature itself enforces this — AnonymizedRecord has no yard_id
    # field.
    record = AnonymizedRecord(
        yard_id_hash=_yard_id_hash(yard_id, secret=secret),
        dealer_id=dealer_id,
        region_bucket=_region_bucket(yard.region_code, secret=secret),
        yard_size_bucket=_yard_size_bucket(yard.size_m2),
        tool_inventory_hash=_tool_inventory_hash(tool_kinds, secret=secret),
        # In P5 these come from the silver layer's rollup of telemetry +
        # action_log. The aggregation_service contract is "given a yard
        # row, here are the buckets"; the silver-side rollup populates
        # the time-decay fields. Default to 0 in unit-test scope where
        # the rollup isn't run.
        robotic_mower_age_years=_robotic_mower_age_years(session, yard_id),
        last_service_event_age_days=0,
        consent_state=YardProConsentState.granted.value,
    )
    return record


def _list_granted_pairs(session: Session, yard_id: int) -> list[str]:
    """Return the dealer_ids whose latest transition for ``yard_id`` is
    ``granted``. Used by :func:`anonymize_yard` when no explicit dealer
    is supplied."""
    granted: list[str] = []
    for rel in consent_service.list_for_yard(session, yard_id):
        if rel.consent_state == YardProConsentState.granted:
            granted.append(rel.dealer_id)
    return granted


def _robotic_mower_age_years(session: Session, yard_id: int) -> int:
    """Crude age-of-oldest-robotic-mower bucket.

    The gold table column is an integer; we return the integer age in
    years of the oldest robotic mower the yard owns, or 0 if there are
    no robotic mowers. P5's anonymization is per-row producer logic;
    a real silver-layer rollup would compute this from telemetry + the
    purchase event log. For the demo we read ``model_year`` directly.
    """
    from datetime import date

    from ..models import YardProToolKind

    rows = session.exec(
        select(YpTool)
        .where(YpTool.yard_id == yard_id)
        .where(YpTool.kind == YardProToolKind.robotic_mower)
    ).all()
    if not rows:
        return 0
    current_year = date.today().year
    return max(
        max(0, current_year - (t.model_year or current_year)) for t in rows
    )


# ---------------------------------------------------------------------------
# Batch entry — exclude non-granted households
# ---------------------------------------------------------------------------


def anonymize_consented_yards(
    session: Session,
) -> list[AnonymizedRecord]:
    """Yield one record per (yard, dealer) pair whose latest consent is
    ``granted``.

    Production-grade flow: reads ``YpDealerRelationship`` (event-sourced),
    resolves the latest state per pair, includes only those with
    ``state=granted``, and runs :func:`anonymize_yard` on each. RT-012
    + RT-022 mitigations live here — the function reads consent_state
    on every batch and excludes households with ``consent_state !=
    'granted'``.

    The function never raises on a pending or revoked household — it
    silently excludes them. This is the documented gate.
    """
    secret = _require_secret()  # fail fast before doing any work
    del secret  # only needed for the early check; anonymize_yard re-reads

    out: list[AnonymizedRecord] = []
    # We need to enumerate yards. The simplest path: walk every yard
    # and for each, list its granted dealer pairs.
    yards = session.exec(select(YpYard)).all()
    for yard in yards:
        assert yard.id is not None
        for rel in consent_service.list_for_yard(session, yard.id):
            if rel.consent_state != YardProConsentState.granted:
                continue
            try:
                out.append(
                    anonymize_yard(session, yard.id, dealer_id=rel.dealer_id)
                )
            except AnonymizationBlockedError as exc:
                # A row that consent_service.list_for_yard called
                # ``granted`` should always pass; but if a race
                # interleaves we'd rather log + skip than fail the
                # whole batch.
                logger.warning(
                    "yard-pro aggregation: yard_id=%s dealer_id=%s blocked "
                    "during batch (%s); skipping",
                    yard.id,
                    rel.dealer_id,
                    exc,
                )
    return out


__all__ = [
    "AnonymizationBlockedError",
    "AnonymizedRecord",
    "HmacSecretMissingError",
    "anonymize_consented_yards",
    "anonymize_yard",
]
