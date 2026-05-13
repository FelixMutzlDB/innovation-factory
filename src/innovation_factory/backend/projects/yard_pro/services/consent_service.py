"""consent_service — append-only state machine for ``yp_dealer_relationships``.

UC6 (P5) — the OEM B2B2C anchor sits behind a consent rail: the dealer
Genie space ONLY sees rows for households whose latest consent transition
is ``granted``. The state machine here is the load-bearing fence between
"Martin clicked the toggle" and "Klaus's Genie returns yard_A_hash". Two
non-negotiables, both from plan §8:

1. **Append-only.** A transition NEVER UPDATEs the ``consent_state``
   column on an existing row. Each transition is a brand-new row whose
   ``consent_state``, ``consent_at`` / ``revoked_at`` reflect the target
   state. The "current state" of a ``(yard_id, dealer_id)`` pair is the
   row with the latest ``created_at`` for that pair. This is event-
   sourced — the chain of rows IS the audit trail.

2. **Three valid transitions only:**
   - ``none_ → pending`` — household first expresses interest.
   - ``pending → granted`` — household confirms.
   - ``granted → revoked`` — household pulls consent (privacy-first).
   - ``revoked → pending`` — household re-opts-in. Goes back through
     ``pending`` deliberately so re-consent is a positive opt-in step,
     not a one-click reactivation.

   Any other transition raises :class:`ConsentTransitionError` with a
   clear error message naming both the from-state and the to-state.

The :func:`current_state` helper resolves the latest row for a pair
without touching legacy "consent_state on the parent row" patterns.
:func:`transition` does the validation + append in a single Session
operation; the caller commits.

GDPR Art. 17 cascade interaction
--------------------------------
``gdpr_service.delete_yard_cascade`` UPDATEs ``consent_state`` to
``revoked`` on every row referencing the yard *as a tombstone before
deletion*. That is a DIFFERENT rail — it's the GDPR Art. 17 fingerprint
on the WAL right before the rows disappear. The consumer-facing
:func:`transition` here is the only path the application code uses; it
never UPDATEs. The two rails coexist (one append-only, one tombstone-
then-delete) per plan §8 "Consent state machine".
"""
from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Optional

from sqlmodel import Session, select

from ..models import YardProConsentState, YpDealerRelationship


class ConsentTransitionError(ValueError):
    """Raised when a caller asks for an invalid state transition.

    Carries both the source state (``from_state``) and the target state
    (``to_state``) so the router can render a 400 with a precise error
    body. The string form names both states — a downstream log scraper
    can group these without parsing.
    """

    def __init__(
        self,
        from_state: YardProConsentState,
        to_state: YardProConsentState,
        *,
        yard_id: int,
        dealer_id: str,
    ):
        self.from_state = from_state
        self.to_state = to_state
        self.yard_id = yard_id
        self.dealer_id = dealer_id
        super().__init__(
            f"Invalid consent transition for yard_id={yard_id} "
            f"dealer_id={dealer_id}: {from_state.value} -> {to_state.value}"
        )


# ---------------------------------------------------------------------------
# Transition table — single source of truth. Encoded as a set so a future
# contributor adding a new state must update this table explicitly.
# ---------------------------------------------------------------------------

_VALID_TRANSITIONS: set[tuple[YardProConsentState, YardProConsentState]] = {
    (YardProConsentState.none_, YardProConsentState.pending),
    (YardProConsentState.pending, YardProConsentState.granted),
    (YardProConsentState.granted, YardProConsentState.revoked),
    # Re-opt-in deliberately routes through ``pending`` again. Reaching
    # ``granted`` from ``revoked`` directly would skip the explicit
    # household confirmation step.
    (YardProConsentState.revoked, YardProConsentState.pending),
}


@dataclass
class CurrentState:
    """Latest state for a ``(yard_id, dealer_id)`` pair.

    ``relationship_id`` is the id of the **latest** ``YpDealerRelationship``
    row in the chain. ``state`` is the consent state of that row.
    ``has_rows`` is False when no relationship has ever been created for
    the pair — in that case ``state`` is ``YardProConsentState.none_``
    by convention so the transition table works uniformly.
    """

    yard_id: int
    dealer_id: str
    state: YardProConsentState
    relationship_id: Optional[int]
    has_rows: bool


# ---------------------------------------------------------------------------
# Read path
# ---------------------------------------------------------------------------


def current_state(
    session: Session, yard_id: int, dealer_id: str
) -> CurrentState:
    """Resolve the current consent state for ``(yard_id, dealer_id)``.

    Reads the latest ``YpDealerRelationship`` row for the pair (ordered by
    ``created_at DESC``) and returns it as a :class:`CurrentState`. If no
    row exists yet, returns ``state=none_`` with ``has_rows=False`` so
    callers can use the result uniformly with the transition table.
    """
    latest = session.exec(
        select(YpDealerRelationship)
        .where(YpDealerRelationship.yard_id == yard_id)
        .where(YpDealerRelationship.dealer_id == dealer_id)
        .order_by(YpDealerRelationship.created_at.desc())  # type: ignore[unresolved-attribute]
        .limit(1)
    ).first()
    if latest is None:
        return CurrentState(
            yard_id=yard_id,
            dealer_id=dealer_id,
            state=YardProConsentState.none_,
            relationship_id=None,
            has_rows=False,
        )
    return CurrentState(
        yard_id=yard_id,
        dealer_id=dealer_id,
        state=latest.consent_state,
        relationship_id=latest.id,
        has_rows=True,
    )


def list_for_yard(
    session: Session, yard_id: int
) -> list[YpDealerRelationship]:
    """Return the latest-state row per ``(yard_id, dealer_id)`` for a yard.

    The consumer cockpit's "my dealer relationships" surface needs ONE
    row per dealer (the current state), not the full history. We resolve
    that by listing all rows ordered DESC by ``created_at`` and then
    deduplicating client-side by ``dealer_id``. The yards × dealers
    cardinality for a single household is single digits in P5, so this
    is fine without a window function.
    """
    rows = session.exec(
        select(YpDealerRelationship)
        .where(YpDealerRelationship.yard_id == yard_id)
        .order_by(YpDealerRelationship.created_at.desc())  # type: ignore[unresolved-attribute]
    ).all()
    seen: set[str] = set()
    latest: list[YpDealerRelationship] = []
    for row in rows:
        if row.dealer_id in seen:
            continue
        seen.add(row.dealer_id)
        latest.append(row)
    return latest


# ---------------------------------------------------------------------------
# Write path — append a new row representing the new state.
# ---------------------------------------------------------------------------


def transition(
    session: Session,
    *,
    yard_id: int,
    dealer_id: str,
    target_state: YardProConsentState,
) -> YpDealerRelationship:
    """Append a new ``YpDealerRelationship`` row encoding ``target_state``.

    Validates against :data:`_VALID_TRANSITIONS`. Caller is responsible
    for ``session.commit()``; this keeps :func:`transition` composable
    with router-side transactional patterns.

    Side effects on the new row:
    - ``consent_state`` = ``target_state``
    - ``consent_at`` = ``now`` when ``target_state`` is ``granted`` or
      ``pending``; preserved on the row only if non-None.
    - ``revoked_at`` = ``now`` when ``target_state`` is ``revoked``.

    Raises :class:`ConsentTransitionError` on an invalid transition.
    """
    state = current_state(session, yard_id, dealer_id)
    if (state.state, target_state) not in _VALID_TRANSITIONS:
        raise ConsentTransitionError(
            state.state, target_state, yard_id=yard_id, dealer_id=dealer_id
        )

    now = datetime.now(timezone.utc)
    consent_at: Optional[datetime] = None
    revoked_at: Optional[datetime] = None
    if target_state in (
        YardProConsentState.granted,
        YardProConsentState.pending,
    ):
        consent_at = now
    if target_state == YardProConsentState.revoked:
        revoked_at = now

    row = YpDealerRelationship(
        yard_id=yard_id,
        dealer_id=dealer_id,
        consent_state=target_state,
        consent_at=consent_at,
        revoked_at=revoked_at,
    )
    session.add(row)
    session.flush()  # populate id without committing the outer Session.
    return row


def open_relationship(
    session: Session,
    *,
    yard_id: int,
    dealer_id: str,
) -> tuple[YpDealerRelationship, bool]:
    """Idempotent ``POST /dealer/relationships``: open a relationship for a
    household + dealer pair.

    - ``none_`` → transition to ``pending``. Returns ``(row, created=True)``.
    - ``pending`` or ``granted`` → no-op; return the most recent row of
      that state. Returns ``(row, created=False)``. This is the
      idempotency invariant the spec demands: re-POST while already
      ``granted`` is a no-op.
    - ``revoked`` → transition to ``pending`` (re-opt-in). Returns
      ``(row, created=True)``.
    """
    state = current_state(session, yard_id, dealer_id)
    if state.state in (
        YardProConsentState.pending,
        YardProConsentState.granted,
    ):
        # Idempotent — return the latest row without inserting another.
        assert state.relationship_id is not None
        existing = session.get(YpDealerRelationship, state.relationship_id)
        assert existing is not None
        return existing, False
    new_row = transition(
        session,
        yard_id=yard_id,
        dealer_id=dealer_id,
        target_state=YardProConsentState.pending,
    )
    return new_row, True


def revoke_relationship(
    session: Session,
    *,
    yard_id: int,
    dealer_id: str,
) -> tuple[YpDealerRelationship, bool]:
    """Idempotent ``DELETE /dealer/relationships/{id}``: revoke consent.

    - ``granted`` → transition to ``revoked``. Returns ``(row, changed=True)``.
    - ``pending`` → transition is invalid per the table (pending → revoked
      is not allowed in the demo's state machine). Treated as a no-op
      that returns the latest pending row with ``changed=False`` so the
      consumer-side toggle's DELETE is forgiving — a user who cancels
      a still-pending request shouldn't get a 400.

      The append-only rail still holds: nothing is written.
    - ``revoked`` → idempotent no-op; return the latest row with
      ``changed=False``.
    - ``none_`` → 404 in the router (no relationship to revoke).

    Returns ``(latest_row, changed)``. The router converts ``None`` of
    ``latest_row`` into a 404; this helper assumes the caller has already
    verified ``has_rows``.
    """
    state = current_state(session, yard_id, dealer_id)
    if state.state == YardProConsentState.granted:
        new_row = transition(
            session,
            yard_id=yard_id,
            dealer_id=dealer_id,
            target_state=YardProConsentState.revoked,
        )
        return new_row, True
    # pending / revoked: no-op, return latest existing row.
    if state.relationship_id is None:
        # The router should have caught this; defensive code path.
        raise ConsentTransitionError(
            state.state,
            YardProConsentState.revoked,
            yard_id=yard_id,
            dealer_id=dealer_id,
        )
    latest = session.get(YpDealerRelationship, state.relationship_id)
    assert latest is not None
    return latest, False


__all__ = [
    "ConsentTransitionError",
    "CurrentState",
    "current_state",
    "list_for_yard",
    "open_relationship",
    "revoke_relationship",
    "transition",
]
