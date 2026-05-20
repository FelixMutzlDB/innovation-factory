"""Dealer consent state-machine regression test (UC6, plan §8 P2).

Plan §8 "Consent state machine" row:
  ``yp_dealer_relationships.consent_state`` is the single gate;
  aggregation pipeline reads it on every batch and excludes households
  with ``consent_state != 'granted'``. **State changes are append-only**
  (no UPDATE on ``consent_state``; new row on every transition).

Test names reference the **symptom** (the state-machine invariant the
plan rests on) — not the implementation. If a future refactor moves the
state machine into a different module, these tests must still pass.

Coverage:
- Valid transitions: ``none_ → pending → granted``, ``granted →
  revoked``, ``revoked → pending``.
- Invalid transitions raise 400 (router) / ``ConsentTransitionError``
  (service).
- Append-only: every transition writes a new row; ``consent_state`` is
  never UPDATEd on an existing row.
- ``revoked_at`` and ``consent_at`` are set correctly.
- RLS: a caller can't PATCH or DELETE another household's relationship.
- Idempotency: re-POST while ``granted`` is a no-op (returns 201 with
  the existing row's id); re-DELETE while ``revoked`` is a no-op.
"""
from __future__ import annotations

import uuid

import pytest

# Register yard_pro models with SQLModel.metadata at import time.
import innovation_factory.backend.projects.yard_pro.models  # noqa: F401


@pytest.fixture
def martin_yard(session):
    """Seed Martin's yard with a randomized user_key (engine is session-
    scoped — committed rows persist; randomization keeps tests isolated).
    """
    from innovation_factory.backend.projects.yard_pro.models import YpYard

    user_key = f"martin-{uuid.uuid4().hex[:8]}@yard-pro.local"
    yard = YpYard(
        user_key=user_key,
        display_name="Martin's Yard (consent test)",
        region_code="DE-BW",
        size_m2=900.0,
        yard_metadata={},
    )
    session.add(yard)
    session.commit()
    session.refresh(yard)
    return {
        "yard": yard,
        "headers": {"X-Forwarded-User": user_key},
        "user_key": user_key,
    }


@pytest.fixture
def bob_yard(session):
    """Second yard for RLS cross-tenant tests."""
    from innovation_factory.backend.projects.yard_pro.models import YpYard

    user_key = f"bob-{uuid.uuid4().hex[:8]}@yard-pro.local"
    yard = YpYard(
        user_key=user_key,
        display_name="Bob's Yard (consent test)",
        region_code="DE-BW",
        size_m2=600.0,
        yard_metadata={},
    )
    session.add(yard)
    session.commit()
    session.refresh(yard)
    return {
        "yard": yard,
        "headers": {"X-Forwarded-User": user_key},
        "user_key": user_key,
    }


# ---------------------------------------------------------------------------
# Service-layer transition table
# ---------------------------------------------------------------------------


class TestConsentTransitionTable:
    """Validates the append-only state machine at the service layer.

    These are deliberately router-free — exercising the
    :mod:`consent_service` directly so the state machine is verifiable
    even if the router moves."""

    def test_none_to_pending_appends_a_row(self, session, martin_yard):
        from innovation_factory.backend.projects.yard_pro.models import (
            YardProConsentState,
            YpDealerRelationship,
        )
        from innovation_factory.backend.projects.yard_pro.services import (
            consent_service,
        )

        yard_id = martin_yard["yard"].id
        before = session.exec(
            __import__(
                "sqlmodel"
            ).select(YpDealerRelationship)
            .where(YpDealerRelationship.yard_id == yard_id)
        ).all()
        assert len(before) == 0

        new_row = consent_service.transition(
            session,
            yard_id=yard_id,
            dealer_id="dealer_stuttgart_nord",
            target_state=YardProConsentState.pending,
        )
        session.commit()
        session.refresh(new_row)
        assert new_row.consent_state == YardProConsentState.pending
        assert new_row.consent_at is not None
        assert new_row.revoked_at is None

    def test_pending_to_granted_writes_new_row_does_not_update(
        self, session, martin_yard
    ):
        from sqlmodel import select

        from innovation_factory.backend.projects.yard_pro.models import (
            YardProConsentState,
            YpDealerRelationship,
        )
        from innovation_factory.backend.projects.yard_pro.services import (
            consent_service,
        )

        yard_id = martin_yard["yard"].id
        consent_service.transition(
            session,
            yard_id=yard_id,
            dealer_id="dealer_stuttgart_nord",
            target_state=YardProConsentState.pending,
        )
        session.commit()
        consent_service.transition(
            session,
            yard_id=yard_id,
            dealer_id="dealer_stuttgart_nord",
            target_state=YardProConsentState.granted,
        )
        session.commit()

        rows = session.exec(
            select(YpDealerRelationship)
            .where(YpDealerRelationship.yard_id == yard_id)
            .where(YpDealerRelationship.dealer_id == "dealer_stuttgart_nord")
            .order_by(YpDealerRelationship.created_at)  # type: ignore[invalid-argument-type]
        ).all()
        # APPEND-ONLY: two rows, not one mutated row.
        assert len(rows) == 2, (
            "Append-only invariant violated: expected 2 rows, "
            f"got {len(rows)}"
        )
        assert rows[0].consent_state == YardProConsentState.pending
        assert rows[1].consent_state == YardProConsentState.granted
        # The latest row's consent_at is set.
        assert rows[1].consent_at is not None

    def test_granted_to_revoked_sets_revoked_at(self, session, martin_yard):
        from innovation_factory.backend.projects.yard_pro.models import (
            YardProConsentState,
        )
        from innovation_factory.backend.projects.yard_pro.services import (
            consent_service,
        )

        yard_id = martin_yard["yard"].id
        dealer = "dealer_stuttgart_nord"
        for target in (
            YardProConsentState.pending,
            YardProConsentState.granted,
            YardProConsentState.revoked,
        ):
            consent_service.transition(
                session,
                yard_id=yard_id,
                dealer_id=dealer,
                target_state=target,
            )
        session.commit()

        state = consent_service.current_state(session, yard_id, dealer)
        assert state.state == YardProConsentState.revoked
        latest = session.get(
            __import__(
                "innovation_factory.backend.projects.yard_pro.models",
                fromlist=["YpDealerRelationship"],
            ).YpDealerRelationship,
            state.relationship_id,
        )
        assert latest is not None
        assert latest.revoked_at is not None

    def test_revoked_to_pending_re_opt_in_appends(self, session, martin_yard):
        """The household re-consents — must go through ``pending`` again."""
        from innovation_factory.backend.projects.yard_pro.models import (
            YardProConsentState,
        )
        from innovation_factory.backend.projects.yard_pro.services import (
            consent_service,
        )

        yard_id = martin_yard["yard"].id
        dealer = "dealer_stuttgart_nord"
        for target in (
            YardProConsentState.pending,
            YardProConsentState.granted,
            YardProConsentState.revoked,
            YardProConsentState.pending,
        ):
            consent_service.transition(
                session,
                yard_id=yard_id,
                dealer_id=dealer,
                target_state=target,
            )
        session.commit()
        state = consent_service.current_state(session, yard_id, dealer)
        assert state.state == YardProConsentState.pending

    @pytest.mark.parametrize(
        "transitions",
        [
            # none_ -> granted is not allowed (must pass through pending)
            ["granted"],
            # pending -> revoked is not allowed (only granted can be revoked)
            ["pending", "revoked"],
            # revoked -> granted is not allowed (must go via pending)
            ["pending", "granted", "revoked", "granted"],
            # granted -> pending is not allowed
            ["pending", "granted", "pending"],
        ],
    )
    def test_invalid_transition_raises_consent_transition_error(
        self, session, martin_yard, transitions
    ):
        from innovation_factory.backend.projects.yard_pro.models import (
            YardProConsentState,
        )
        from innovation_factory.backend.projects.yard_pro.services import (
            consent_service,
        )

        yard_id = martin_yard["yard"].id
        dealer = "dealer_invalid_test"
        # Apply all but the last successfully.
        for target_name in transitions[:-1]:
            consent_service.transition(
                session,
                yard_id=yard_id,
                dealer_id=dealer,
                target_state=YardProConsentState(target_name),
            )
        session.commit()
        # Final transition must fail.
        with pytest.raises(consent_service.ConsentTransitionError) as excinfo:
            consent_service.transition(
                session,
                yard_id=yard_id,
                dealer_id=dealer,
                target_state=YardProConsentState(transitions[-1]),
            )
        # Error message names both states so log scraping can group.
        msg = str(excinfo.value)
        assert "->" in msg
        assert transitions[-1] in msg


# ---------------------------------------------------------------------------
# Router contract
# ---------------------------------------------------------------------------


class TestDealerRouterStateMachine:
    def test_post_creates_pending_relationship(self, client, martin_yard):
        resp = client.post(
            "/api/projects/yard-pro/dealer/relationships",
            headers=martin_yard["headers"],
            json={"dealer_id": "dealer_stuttgart_nord"},
        )
        assert resp.status_code == 201, resp.text
        body = resp.json()
        assert body["consent_state"] == "pending"
        assert body["yard_id"] == martin_yard["yard"].id
        assert body["consent_at"] is not None
        assert body["revoked_at"] is None

    def test_post_is_idempotent_while_pending(self, client, martin_yard):
        first = client.post(
            "/api/projects/yard-pro/dealer/relationships",
            headers=martin_yard["headers"],
            json={"dealer_id": "dealer_stuttgart_nord"},
        )
        assert first.status_code == 201, first.text
        second = client.post(
            "/api/projects/yard-pro/dealer/relationships",
            headers=martin_yard["headers"],
            json={"dealer_id": "dealer_stuttgart_nord"},
        )
        assert second.status_code == 201, second.text
        # The second call MUST return the same relationship_id; no new row.
        assert second.json()["id"] == first.json()["id"]

    def test_post_is_idempotent_while_granted(
        self, client, martin_yard, session
    ):
        first = client.post(
            "/api/projects/yard-pro/dealer/relationships",
            headers=martin_yard["headers"],
            json={"dealer_id": "dealer_stuttgart_nord"},
        )
        pending_id = first.json()["id"]
        granted = client.patch(
            f"/api/projects/yard-pro/dealer/relationships/{pending_id}/consent",
            headers=martin_yard["headers"],
            json={"target_state": "granted"},
        )
        assert granted.status_code == 200, granted.text
        granted_id = granted.json()["id"]
        assert granted_id != pending_id  # append-only

        second_post = client.post(
            "/api/projects/yard-pro/dealer/relationships",
            headers=martin_yard["headers"],
            json={"dealer_id": "dealer_stuttgart_nord"},
        )
        assert second_post.status_code == 201
        # Idempotent: returns the same granted row id.
        assert second_post.json()["id"] == granted_id

    def test_patch_invalid_transition_returns_400(self, client, martin_yard):
        first = client.post(
            "/api/projects/yard-pro/dealer/relationships",
            headers=martin_yard["headers"],
            json={"dealer_id": "dealer_stuttgart_nord"},
        )
        rel_id = first.json()["id"]
        # pending -> revoked is invalid.
        resp = client.patch(
            f"/api/projects/yard-pro/dealer/relationships/{rel_id}/consent",
            headers=martin_yard["headers"],
            json={"target_state": "revoked"},
        )
        assert resp.status_code == 400, resp.text
        # The error body must name both states.
        detail = resp.json()["detail"]
        assert "pending" in detail
        assert "revoked" in detail

    def test_delete_revokes_granted_relationship(self, client, martin_yard):
        first = client.post(
            "/api/projects/yard-pro/dealer/relationships",
            headers=martin_yard["headers"],
            json={"dealer_id": "dealer_stuttgart_nord"},
        )
        rel_id = first.json()["id"]
        client.patch(
            f"/api/projects/yard-pro/dealer/relationships/{rel_id}/consent",
            headers=martin_yard["headers"],
            json={"target_state": "granted"},
        )
        delete = client.delete(
            f"/api/projects/yard-pro/dealer/relationships/{rel_id}",
            headers=martin_yard["headers"],
        )
        assert delete.status_code == 200, delete.text
        assert delete.json()["consent_state"] == "revoked"
        assert delete.json()["revoked_at"] is not None

    def test_delete_idempotent_on_already_revoked(self, client, martin_yard):
        first = client.post(
            "/api/projects/yard-pro/dealer/relationships",
            headers=martin_yard["headers"],
            json={"dealer_id": "dealer_stuttgart_nord"},
        )
        rel_id = first.json()["id"]
        client.patch(
            f"/api/projects/yard-pro/dealer/relationships/{rel_id}/consent",
            headers=martin_yard["headers"],
            json={"target_state": "granted"},
        )
        client.delete(
            f"/api/projects/yard-pro/dealer/relationships/{rel_id}",
            headers=martin_yard["headers"],
        )
        # Second DELETE — same revoked row returned, no error.
        second = client.delete(
            f"/api/projects/yard-pro/dealer/relationships/{rel_id}",
            headers=martin_yard["headers"],
        )
        assert second.status_code == 200, second.text
        assert second.json()["consent_state"] == "revoked"

    def test_list_returns_only_callers_relationships(
        self, client, martin_yard, bob_yard
    ):
        client.post(
            "/api/projects/yard-pro/dealer/relationships",
            headers=martin_yard["headers"],
            json={"dealer_id": "dealer_martin_only"},
        )
        client.post(
            "/api/projects/yard-pro/dealer/relationships",
            headers=bob_yard["headers"],
            json={"dealer_id": "dealer_bob_only"},
        )
        resp = client.get(
            "/api/projects/yard-pro/dealer/relationships",
            headers=martin_yard["headers"],
        )
        assert resp.status_code == 200
        dealer_ids = [r["dealer_id"] for r in resp.json()]
        assert "dealer_martin_only" in dealer_ids
        assert "dealer_bob_only" not in dealer_ids, (
            "RLS leak: Martin saw Bob's dealer relationship"
        )

    def test_patch_on_other_households_relationship_returns_404(
        self, client, martin_yard, bob_yard
    ):
        bob_rel = client.post(
            "/api/projects/yard-pro/dealer/relationships",
            headers=bob_yard["headers"],
            json={"dealer_id": "dealer_bob_only"},
        )
        bob_rel_id = bob_rel.json()["id"]
        # Martin tries to advance Bob's relationship.
        resp = client.patch(
            f"/api/projects/yard-pro/dealer/relationships/{bob_rel_id}/consent",
            headers=martin_yard["headers"],
            json={"target_state": "granted"},
        )
        assert resp.status_code == 404

    def test_delete_on_other_households_relationship_returns_404(
        self, client, martin_yard, bob_yard
    ):
        bob_rel = client.post(
            "/api/projects/yard-pro/dealer/relationships",
            headers=bob_yard["headers"],
            json={"dealer_id": "dealer_bob_only"},
        )
        bob_rel_id = bob_rel.json()["id"]
        resp = client.delete(
            f"/api/projects/yard-pro/dealer/relationships/{bob_rel_id}",
            headers=martin_yard["headers"],
        )
        assert resp.status_code == 404


# ---------------------------------------------------------------------------
# Append-only proof — count rows directly in the DB after each transition
# ---------------------------------------------------------------------------


class TestAppendOnlyInvariant:
    def test_every_transition_writes_a_new_row(
        self, client, martin_yard, session
    ):
        """Walk the full pending → granted → revoked → pending chain via
        the API and verify the table contains exactly 4 rows for the
        (yard_id, dealer_id) pair (one per transition)."""
        from sqlmodel import select

        from innovation_factory.backend.projects.yard_pro.models import (
            YpDealerRelationship,
        )

        first = client.post(
            "/api/projects/yard-pro/dealer/relationships",
            headers=martin_yard["headers"],
            json={"dealer_id": "dealer_append_only_test"},
        )
        rel_id = first.json()["id"]
        client.patch(
            f"/api/projects/yard-pro/dealer/relationships/{rel_id}/consent",
            headers=martin_yard["headers"],
            json={"target_state": "granted"},
        )
        client.delete(
            f"/api/projects/yard-pro/dealer/relationships/{rel_id}",
            headers=martin_yard["headers"],
        )
        # Re-opt-in via POST after revoke (revoked → pending).
        client.post(
            "/api/projects/yard-pro/dealer/relationships",
            headers=martin_yard["headers"],
            json={"dealer_id": "dealer_append_only_test"},
        )

        rows = session.exec(
            select(YpDealerRelationship)
            .where(
                YpDealerRelationship.yard_id == martin_yard["yard"].id
            )
            .where(
                YpDealerRelationship.dealer_id == "dealer_append_only_test"
            )
            .order_by(YpDealerRelationship.created_at)  # type: ignore[invalid-argument-type]
        ).all()
        states = [r.consent_state.value for r in rows]
        assert states == ["pending", "granted", "revoked", "pending"], (
            f"Expected pending/granted/revoked/pending chain, got {states}"
        )
