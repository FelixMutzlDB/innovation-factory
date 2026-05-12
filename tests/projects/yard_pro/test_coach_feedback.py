"""Regression tests for the coach advisory feedback loop (plan §8).

Wire contract:
- POST /coach/feedback upserts on ``(yard_id, response_id)`` so a user
  can flip thumbs_up → thumbs_down without two rows accumulating.
- GET /coach/feedback/stats returns count + thumbs_down_rate + flagged
  boolean where flagged = ``total_count >= 100 AND thumbs_down_rate > 0.05``.
- RLS: hostile user can't submit or query stats for another yard.
- Art. 22 boundary: feedback POSTs do NOT write into ``yp_action_log``.
"""
from __future__ import annotations

import pytest
from sqlmodel import select

import innovation_factory.backend.projects.yard_pro.models  # noqa: F401


MARTIN_HEADERS = {"X-Forwarded-User": "feedback-martin@yard-pro.local"}
OTHER_HEADERS = {"X-Forwarded-User": "feedback-hostile@yard-pro.local"}


def _seed_yard(session, user_key: str, display_name: str = "Feedback Yard"):
    from innovation_factory.backend.projects.yard_pro.models import YpYard

    existing = session.exec(
        select(YpYard).where(YpYard.user_key == user_key)
    ).first()
    if existing:
        return existing
    y = YpYard(
        user_key=user_key,
        display_name=display_name,
        region_code="DE-BW",
        lat=48.7,
        lng=9.2,
        size_m2=600.0,
        yard_metadata={},
    )
    session.add(y)
    session.commit()
    session.refresh(y)
    return y


def _seed_assistant_message(session, yard_id: int, model_version: str = "test-v1") -> int:
    """Seed a session + assistant message and return the message id."""
    from innovation_factory.backend.projects.yard_pro.models import (
        YardProChatRole,
        YpCoachMessage,
        YpCoachSession,
    )

    s = YpCoachSession(yard_id=yard_id, title="Test session")
    session.add(s)
    session.commit()
    session.refresh(s)
    m = YpCoachMessage(
        session_id=s.id,
        role=YardProChatRole.assistant,
        content="some advice",
        citations=[],
        model_version=model_version,
        is_recommendation=False,
        advisory=True,
    )
    session.add(m)
    session.commit()
    session.refresh(m)
    return m.id  # type: ignore[return-value]


@pytest.fixture
def martin_yard(session):
    return _seed_yard(session, "feedback-martin@yard-pro.local", "Martin's Yard")


@pytest.fixture
def hostile_yard(session):
    return _seed_yard(session, "feedback-hostile@yard-pro.local", "Hostile Yard")


@pytest.fixture
def martin_response_id(session, martin_yard):
    return _seed_assistant_message(session, martin_yard.id, "model-A")


class TestFeedbackSubmit:
    def test_submit_creates_row(self, client, session, martin_yard, martin_response_id):
        """Scope row count by response_id since the session-scoped engine
        is shared across tests — other tests in this module also write
        feedback rows against the same yard."""
        from innovation_factory.backend.projects.yard_pro.models import YpCoachFeedback

        resp = client.post(
            "/api/projects/yard-pro/coach/feedback",
            headers=MARTIN_HEADERS,
            json={"response_id": str(martin_response_id), "signal": "thumbs_down"},
        )
        assert resp.status_code == 201, resp.text
        body = resp.json()
        assert body["signal"] == "thumbs_down"
        assert body["model_version"] == "model-A"

        rows = list(
            session.exec(
                select(YpCoachFeedback).where(
                    YpCoachFeedback.response_id == str(martin_response_id)
                )
            ).all()
        )
        assert len(rows) == 1

    def test_resubmit_same_response_upserts_not_dupes(
        self, client, session, martin_yard, martin_response_id
    ):
        """Plan §8 upsert semantics — two POSTs with the same
        (yard_id, response_id) produce exactly one row."""
        from innovation_factory.backend.projects.yard_pro.models import YpCoachFeedback

        client.post(
            "/api/projects/yard-pro/coach/feedback",
            headers=MARTIN_HEADERS,
            json={"response_id": str(martin_response_id), "signal": "thumbs_up"},
        )
        second = client.post(
            "/api/projects/yard-pro/coach/feedback",
            headers=MARTIN_HEADERS,
            json={"response_id": str(martin_response_id), "signal": "thumbs_down"},
        )
        assert second.status_code == 201, second.text

        rows = list(
            session.exec(
                select(YpCoachFeedback).where(
                    YpCoachFeedback.response_id == str(martin_response_id)
                )
            ).all()
        )
        assert len(rows) == 1
        assert rows[0].signal.value == "thumbs_down"

    def test_submit_404_when_response_not_owned(
        self, client, session, martin_yard, hostile_yard, martin_response_id
    ):
        """RLS: a hostile yard can't submit feedback against another
        yard's response."""
        resp = client.post(
            "/api/projects/yard-pro/coach/feedback",
            headers=OTHER_HEADERS,
            json={"response_id": str(martin_response_id), "signal": "thumbs_down"},
        )
        assert resp.status_code == 404, resp.text

    def test_submit_404_when_response_missing(
        self, client, session, martin_yard
    ):
        resp = client.post(
            "/api/projects/yard-pro/coach/feedback",
            headers=MARTIN_HEADERS,
            json={"response_id": "999999", "signal": "thumbs_down"},
        )
        assert resp.status_code == 404, resp.text

    def test_submit_400_when_response_id_not_int(
        self, client, session, martin_yard
    ):
        resp = client.post(
            "/api/projects/yard-pro/coach/feedback",
            headers=MARTIN_HEADERS,
            json={"response_id": "not-an-int", "signal": "thumbs_down"},
        )
        assert resp.status_code == 400, resp.text

    def test_submit_rejects_feedback_on_user_message(
        self, client, session, martin_yard
    ):
        """Feedback only makes sense on assistant turns. Feedback on a
        user-authored message is a 400."""
        from innovation_factory.backend.projects.yard_pro.models import (
            YardProChatRole,
            YpCoachMessage,
            YpCoachSession,
        )

        s = YpCoachSession(yard_id=martin_yard.id, title="User-turn test")
        session.add(s)
        session.commit()
        session.refresh(s)
        m = YpCoachMessage(
            session_id=s.id,
            role=YardProChatRole.user,
            content="what should i do?",
            advisory=False,
        )
        session.add(m)
        session.commit()
        session.refresh(m)

        resp = client.post(
            "/api/projects/yard-pro/coach/feedback",
            headers=MARTIN_HEADERS,
            json={"response_id": str(m.id), "signal": "thumbs_down"},
        )
        assert resp.status_code == 400, resp.text


class TestFeedbackDoesNotWriteActionLog:
    """Art. 22 boundary: feedback is audit signal, not a confirmed
    action. The feedback endpoint MUST NOT write into yp_action_log."""

    def test_no_action_log_row_after_feedback(
        self, client, session, martin_yard, martin_response_id
    ):
        from innovation_factory.backend.projects.yard_pro.models import YpActionLog

        before = len(
            list(
                session.exec(
                    select(YpActionLog).where(YpActionLog.yard_id == martin_yard.id)
                ).all()
            )
        )
        resp = client.post(
            "/api/projects/yard-pro/coach/feedback",
            headers=MARTIN_HEADERS,
            json={"response_id": str(martin_response_id), "signal": "thumbs_down"},
        )
        assert resp.status_code == 201, resp.text
        after = len(
            list(
                session.exec(
                    select(YpActionLog).where(YpActionLog.yard_id == martin_yard.id)
                ).all()
            )
        )
        assert after == before  # No action_log writes.


class TestFeedbackStats:
    """The §8 5% auto-flag rule lives in /coach/feedback/stats."""

    def _seed_n_thumbs_down(
        self, session, yard_id: int, model_version: str, n: int
    ):
        """Insert N thumbs_down feedback rows for the given model_version.

        We bypass the endpoint here because the upsert keys on
        ``(yard_id, response_id)`` — to reach n=100 cleanly we need 100
        distinct response_ids, so we seed assistant messages 1:1 and
        write the feedback rows directly."""
        from innovation_factory.backend.projects.yard_pro.models import (
            YardProChatRole,
            YardProCoachFeedbackSignal,
            YpCoachFeedback,
            YpCoachMessage,
            YpCoachSession,
        )

        s = YpCoachSession(yard_id=yard_id, title=f"stats {model_version}")
        session.add(s)
        session.commit()
        session.refresh(s)
        for i in range(n):
            m = YpCoachMessage(
                session_id=s.id,
                role=YardProChatRole.assistant,
                content=f"msg {i}",
                model_version=model_version,
                advisory=True,
            )
            session.add(m)
            session.commit()
            session.refresh(m)
            session.add(
                YpCoachFeedback(
                    yard_id=yard_id,
                    response_id=str(m.id),
                    model_version=model_version,
                    signal=YardProCoachFeedbackSignal.thumbs_down,
                )
            )
        session.commit()

    def test_below_100_turns_never_flags(
        self, client, session, martin_yard
    ):
        """Even 99/99 thumbs_down doesn't flag below the 100-turn floor.

        Uses a unique model_version per test to keep stats scoped — the
        session-scoped engine doesn't reset between tests."""
        self._seed_n_thumbs_down(session, martin_yard.id, "model-low-99", 99)
        resp = client.get(
            "/api/projects/yard-pro/coach/feedback/stats?model_version=model-low-99",
            headers=MARTIN_HEADERS,
        )
        assert resp.status_code == 200, resp.text
        body = resp.json()
        assert body["total_count"] == 99
        assert body["thumbs_down_count"] == 99
        assert body["flagged"] is False

    def test_at_100_all_thumbs_down_flags(
        self, client, session, martin_yard
    ):
        self._seed_n_thumbs_down(session, martin_yard.id, "model-high-100", 100)
        resp = client.get(
            "/api/projects/yard-pro/coach/feedback/stats?model_version=model-high-100",
            headers=MARTIN_HEADERS,
        )
        body = resp.json()
        assert body["total_count"] == 100
        assert body["thumbs_down_rate"] == 1.0
        assert body["flagged"] is True

    def test_stats_scoped_per_yard(
        self, client, session, martin_yard, hostile_yard
    ):
        """Stats query is yard-scoped — Martin's 100 thumbs_down on
        model-x doesn't flag for Klaus."""
        self._seed_n_thumbs_down(session, martin_yard.id, "model-x-scoped", 100)
        resp = client.get(
            "/api/projects/yard-pro/coach/feedback/stats?model_version=model-x-scoped",
            headers=OTHER_HEADERS,
        )
        assert resp.status_code == 200, resp.text
        body = resp.json()
        assert body["total_count"] == 0
        assert body["flagged"] is False
