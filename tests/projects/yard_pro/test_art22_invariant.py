"""GDPR Art. 22 — load-bearing invariant regression test for yard-pro.

Plan §2 non-negotiable: no solely-automated decisions with significant
effect. Backend enforces this by rejecting any ``yp_action_log`` write
whose ``source != 'user'`` AND ``human_confirmed_at is None``. The
matching ``PATCH /actions/{id}/confirm`` route flips the timestamp once
the user clicks "Mark as done".

Test names reference the **symptom** (Art. 22, the load-bearing rail),
not the implementation. If a future refactor moves the check out of
the router into middleware or a SQLModel validator, these tests must
still pass.
"""
from __future__ import annotations

from datetime import datetime, timezone

import pytest

# Import yard_pro models at module level so they register with
# SQLModel.metadata BEFORE the session-scoped ``engine`` fixture in the
# top-level conftest runs ``create_all``. Pytest imports all test
# modules during collection, so this happens early enough.
import innovation_factory.backend.projects.yard_pro.models  # noqa: F401


MARTIN_HEADERS = {"X-Forwarded-User": "martin@yard-pro.local"}


def _seed_martin_yard(session):
    """Idempotent local seed for these tests — independent of the
    production ``seed_yp_data`` so the test owns its data shape."""
    from sqlmodel import select

    from innovation_factory.backend.projects.yard_pro.models import YpYard

    existing = session.exec(
        select(YpYard).where(YpYard.user_key == "martin@yard-pro.local")
    ).first()
    if existing:
        return existing
    yard = YpYard(
        user_key="martin@yard-pro.local",
        display_name="Martin's Yard (test)",
        region_code="DE-BW",
        lat=48.7758,
        lng=9.1829,
        size_m2=900.0,
        yard_metadata={},
    )
    session.add(yard)
    session.commit()
    session.refresh(yard)
    return yard


class TestArt22LoadBearingRail:
    """The four endpoint shapes the rail must enforce."""

    def test_coach_recommendation_without_confirm_returns_400_and_names_art22(
        self, client, session
    ):
        """A coach-sourced row with no human_confirmed_at MUST be rejected.
        Symptom: clicking nothing in the UI cannot silently log a 'done'
        action attributed to the user."""
        _seed_martin_yard(session)
        resp = client.post(
            "/api/projects/yard-pro/actions",
            headers=MARTIN_HEADERS,
            json={
                "action_type": "fertilize",
                "notes": "Apply X-fertilizer to lawn (suggested)",
                "source": "coach_recommendation",
            },
        )
        assert resp.status_code == 400, resp.text
        # The error body must NAME the Art. 22 rail so a downstream
        # log scrape / observability dashboard can group these.
        assert "Art. 22" in resp.json()["detail"]

    def test_telemetry_nudge_without_confirm_returns_400(self, client, session):
        """Same rail applies to UC4 telemetry nudges (battery_low, stuck,
        maintenance_due) — the cockpit's "Snooze / Mark as done" UI is
        the only path that flips the timestamp."""
        _seed_martin_yard(session)
        resp = client.post(
            "/api/projects/yard-pro/actions",
            headers=MARTIN_HEADERS,
            json={
                "action_type": "other",
                "notes": "Robotic mower battery low",
                "source": "telemetry_nudge",
            },
        )
        assert resp.status_code == 400, resp.text
        assert "Art. 22" in resp.json()["detail"]

    def test_user_action_without_confirm_is_allowed(self, client, session):
        """User-sourced rows don't need an explicit confirm timestamp —
        the source itself IS the confirmation. This is the common path."""
        _seed_martin_yard(session)
        resp = client.post(
            "/api/projects/yard-pro/actions",
            headers=MARTIN_HEADERS,
            json={
                "action_type": "mow",
                "notes": "Mowed the lawn",
                "source": "user",
            },
        )
        assert resp.status_code == 201, resp.text
        body = resp.json()
        assert body["source"] == "user"
        assert body["human_confirmed_at"] is None

    def test_coach_recommendation_with_confirm_is_allowed(self, client, session):
        """A coach-sourced row WITH an explicit human_confirmed_at must
        succeed — this is what the frontend "Mark as done" button
        produces (it accepts the AI suggestion and records the click)."""
        _seed_martin_yard(session)
        now = datetime.now(timezone.utc).isoformat()
        resp = client.post(
            "/api/projects/yard-pro/actions",
            headers=MARTIN_HEADERS,
            json={
                "action_type": "fertilize",
                "notes": "User accepted coach suggestion",
                "source": "coach_recommendation",
                "human_confirmed_at": now,
            },
        )
        assert resp.status_code == 201, resp.text
        body = resp.json()
        assert body["source"] == "coach_recommendation"
        assert body["human_confirmed_at"] is not None


class TestConfirmActionRail:
    """The PATCH /actions/{id}/confirm endpoint flips a null timestamp
    to non-null. P0 forbids the unconfirmed POST entirely, but the
    confirm route exists so the same shape works in P1+ when a worker
    inserts unconfirmed rows via internal paths."""

    def test_confirm_flips_human_confirmed_at(self, client, session):
        """Confirm sets ``human_confirmed_at`` from null → not-null."""
        from innovation_factory.backend.projects.yard_pro.models import (
            YardProActionSource,
            YardProActionType,
            YpActionLog,
        )

        yard = _seed_martin_yard(session)
        # Bypass the API and insert an unconfirmed coach row directly —
        # simulating the future worker path. The router's enforcement
        # is at the HTTP boundary; internal code paths can still write
        # unconfirmed rows that the confirm endpoint then resolves.
        entry = YpActionLog(
            yard_id=yard.id,
            action_type=YardProActionType.fertilize,
            occurred_at=datetime.now(timezone.utc),
            notes="Pending coach suggestion",
            source=YardProActionSource.coach_recommendation,
            human_confirmed_at=None,
        )
        session.add(entry)
        session.commit()
        session.refresh(entry)

        before = entry.human_confirmed_at
        assert before is None

        resp = client.patch(
            f"/api/projects/yard-pro/actions/{entry.id}/confirm",
            headers=MARTIN_HEADERS,
        )
        assert resp.status_code == 200, resp.text
        body = resp.json()
        assert body["human_confirmed_at"] is not None

    def test_confirm_returns_404_for_unknown_action(self, client, session):
        _seed_martin_yard(session)
        resp = client.patch(
            "/api/projects/yard-pro/actions/99999999/confirm",
            headers=MARTIN_HEADERS,
        )
        assert resp.status_code == 404


class TestIdempotencyKeySchemaOnly:
    """P0 ships the column; the 24h replay-cache logic is deferred to P1
    (plan §12). Verify the column is populated end-to-end so the index
    works as soon as the cache turns on."""

    def test_idempotency_key_persisted_from_header(self, client, session):
        from sqlmodel import select

        from innovation_factory.backend.projects.yard_pro.models import (
            YpActionLog,
        )

        _seed_martin_yard(session)
        resp = client.post(
            "/api/projects/yard-pro/actions",
            headers={
                **MARTIN_HEADERS,
                "Idempotency-Key": "test-key-abc-123",
            },
            json={
                "action_type": "water",
                "notes": "Watered the roses",
                "source": "user",
            },
        )
        assert resp.status_code == 201, resp.text
        action_id = resp.json()["id"]
        row = session.exec(
            select(YpActionLog).where(YpActionLog.id == action_id)
        ).first()
        assert row is not None
        assert row.idempotency_key == "test-key-abc-123"
