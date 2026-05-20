"""Idempotency-Key 24h cache-replay regression tests (plan §9, §12 P1).

Behavior under test: when a client sends ``Idempotency-Key`` on
``POST /actions`` or ``POST /diagnose``, a second request with the same
key for the same yard within 24h returns the **cached** response (status
200) without re-executing the side effect. Outside the 24h window the
same key is treated as fresh and creates a new row.

Test names reference the **symptom** (replay safety, double-fire,
expired key) so future refactors that move the check elsewhere still
exercise the same contract.
"""
from __future__ import annotations

from datetime import datetime, timedelta, timezone
from io import BytesIO

import pytest

import innovation_factory.backend.projects.yard_pro.models  # noqa: F401


MARTIN_HEADERS = {"X-Forwarded-User": "martin@yard-pro.local"}
OTHER_HEADERS = {"X-Forwarded-User": "klaus@other.local"}


def _seed_yard(session, user_key: str, display_name: str = "Test Yard"):
    from sqlmodel import select

    from innovation_factory.backend.projects.yard_pro.models import YpYard

    existing = session.exec(
        select(YpYard).where(YpYard.user_key == user_key)
    ).first()
    if existing:
        return existing
    yard = YpYard(
        user_key=user_key,
        display_name=display_name,
        region_code="DE-BW",
        lat=48.7,
        lng=9.2,
        size_m2=600.0,
        yard_metadata={},
    )
    session.add(yard)
    session.commit()
    session.refresh(yard)
    return yard


@pytest.fixture
def martin_yard(session):
    return _seed_yard(session, "martin@yard-pro.local", "Martin's Yard")


@pytest.fixture
def klaus_yard(session):
    return _seed_yard(session, "klaus@other.local", "Klaus's Yard")


# ---------------------------------------------------------------------------
# POST /actions
# ---------------------------------------------------------------------------


class TestActionsReplay:
    """``POST /actions`` 24h cache-replay invariants."""

    def test_same_key_within_window_returns_cached_200(
        self, client, session, martin_yard
    ):
        body = {"action_type": "mow", "source": "user", "notes": "first"}
        headers = {**MARTIN_HEADERS, "Idempotency-Key": "abc-123"}

        first = client.post(
            "/api/projects/yard-pro/actions", json=body, headers=headers
        )
        assert first.status_code == 201, first.text
        first_body = first.json()

        # Second call with the same key — same body or different body, the
        # cached response wins. We deliberately change the notes to prove
        # the original wins, not the new payload.
        second_body = {**body, "notes": "different but ignored"}
        second = client.post(
            "/api/projects/yard-pro/actions",
            json=second_body,
            headers=headers,
        )
        assert second.status_code == 200, second.text
        assert second.json() == first_body

    def test_same_key_outside_window_creates_new_row(
        self, client, session, martin_yard
    ):
        """Sentry that the 24h cutoff actually expires. Backdates the
        first row's ``created_at`` past the window and asserts the second
        write goes through with a fresh id."""
        from sqlmodel import select

        from innovation_factory.backend.projects.yard_pro.models import (
            YpActionLog,
        )

        headers = {**MARTIN_HEADERS, "Idempotency-Key": "old-key-xyz"}
        body = {"action_type": "mow", "source": "user", "notes": "first"}

        first = client.post(
            "/api/projects/yard-pro/actions", json=body, headers=headers
        )
        assert first.status_code == 201, first.text

        # Backdate the row.
        row = session.exec(
            select(YpActionLog).where(YpActionLog.idempotency_key == "old-key-xyz")
        ).one()
        row.created_at = datetime.now(timezone.utc) - timedelta(hours=25)
        session.add(row)
        session.commit()

        second = client.post(
            "/api/projects/yard-pro/actions", json=body, headers=headers
        )
        assert second.status_code == 201, second.text
        assert second.json()["id"] != first.json()["id"]

    def test_same_key_different_yard_creates_new_row(
        self, client, session, martin_yard, klaus_yard
    ):
        """Replay key is tuple ``(yard_id, idempotency_key)`` — same key
        reused by a different yard MUST create a new row, not collide."""
        body = {"action_type": "mow", "source": "user", "notes": "first"}

        m = client.post(
            "/api/projects/yard-pro/actions",
            json=body,
            headers={**MARTIN_HEADERS, "Idempotency-Key": "shared-key"},
        )
        assert m.status_code == 201, m.text
        k = client.post(
            "/api/projects/yard-pro/actions",
            json=body,
            headers={**OTHER_HEADERS, "Idempotency-Key": "shared-key"},
        )
        assert k.status_code == 201, k.text
        assert m.json()["id"] != k.json()["id"]
        assert m.json()["yard_id"] != k.json()["yard_id"]

    def test_different_keys_same_yard_create_two_rows(
        self, client, session, martin_yard
    ):
        body = {"action_type": "mow", "source": "user", "notes": "first"}
        a = client.post(
            "/api/projects/yard-pro/actions",
            json=body,
            headers={**MARTIN_HEADERS, "Idempotency-Key": "key-A"},
        )
        b = client.post(
            "/api/projects/yard-pro/actions",
            json=body,
            headers={**MARTIN_HEADERS, "Idempotency-Key": "key-B"},
        )
        assert a.status_code == 201 and b.status_code == 201
        assert a.json()["id"] != b.json()["id"]

    def test_no_key_each_request_creates_new_row(
        self, client, session, martin_yard
    ):
        body = {"action_type": "mow", "source": "user", "notes": "first"}
        a = client.post(
            "/api/projects/yard-pro/actions", json=body, headers=MARTIN_HEADERS
        )
        b = client.post(
            "/api/projects/yard-pro/actions", json=body, headers=MARTIN_HEADERS
        )
        assert a.status_code == 201 and b.status_code == 201
        assert a.json()["id"] != b.json()["id"]


# ---------------------------------------------------------------------------
# POST /diagnose
# ---------------------------------------------------------------------------


class TestDiagnoseReplay:
    """``POST /diagnose`` 24h cache-replay invariants.

    Diagnose's "not configured" path returns 503 in local dev (the seed's
    VISION_ENDPOINT is empty). For replay tests we **insert a YpDiagnosis
    row directly** to simulate a prior successful diagnosis, then assert
    that a second multipart upload with the matching Idempotency-Key
    short-circuits to the cached row without hitting the vision endpoint.
    """

    def _prior_diagnosis(self, session, yard_id: int, key: str, created_at=None):
        from innovation_factory.backend.projects.yard_pro.models import (
            YardProDiagnosisStatus,
            YpDiagnosis,
        )

        d = YpDiagnosis(
            yard_id=yard_id,
            photo_uri=f"yard_pro/photos/{yard_id}/seed.bin",
            model_version="test-vision-v0",
            predictions={"predictions": [{"name": "fusarium", "confidence": 0.83}]},
            top_label="fusarium",
            top_confidence=0.83,
            status=YardProDiagnosisStatus.pending,
            idempotency_key=key,
            created_at=created_at or datetime.now(timezone.utc),
        )
        session.add(d)
        session.commit()
        session.refresh(d)
        return d

    def test_same_key_within_window_returns_cached_200(
        self, client, session, martin_yard
    ):
        prior = self._prior_diagnosis(session, martin_yard.id, "diag-key-1")

        # Replay path runs BEFORE the vision call — so even with
        # VISION_ENDPOINT empty, the cached path returns 200 (not 503).
        upload = {"file": ("x.jpg", BytesIO(b"\xff\xd8\xff\xd9"), "image/jpeg")}
        resp = client.post(
            "/api/projects/yard-pro/diagnose",
            headers={**MARTIN_HEADERS, "Idempotency-Key": "diag-key-1"},
            files=upload,
        )
        assert resp.status_code == 200, resp.text
        body = resp.json()
        assert body["id"] == prior.id
        assert body["top_label"] == "fusarium"
        assert body["second_opinion_cta"]  # non-empty CTA preserved
        assert body["advisory"] is True

    def test_same_key_outside_window_falls_through(
        self, client, session, martin_yard
    ):
        """Stale prior row outside the 24h window does NOT short-circuit;
        the replay returns 503 because VISION_ENDPOINT is unset (i.e. we
        prove the cache didn't fire by observing the non-cached failure
        mode)."""
        old = datetime.now(timezone.utc) - timedelta(hours=25)
        self._prior_diagnosis(session, martin_yard.id, "diag-key-2", created_at=old)

        upload = {"file": ("x.jpg", BytesIO(b"\xff\xd8\xff\xd9"), "image/jpeg")}
        resp = client.post(
            "/api/projects/yard-pro/diagnose",
            headers={**MARTIN_HEADERS, "Idempotency-Key": "diag-key-2"},
            files=upload,
        )
        # Cache miss → the real handler runs → VISION_ENDPOINT empty →
        # structured 503 (lessons §18 path, not 500).
        assert resp.status_code == 503, resp.text

    def test_same_key_different_yard_falls_through(
        self, client, session, martin_yard, klaus_yard
    ):
        """A prior diagnosis with the same key on a DIFFERENT yard must
        not satisfy Martin's replay query."""
        self._prior_diagnosis(session, klaus_yard.id, "shared-diag-key")

        upload = {"file": ("x.jpg", BytesIO(b"\xff\xd8\xff\xd9"), "image/jpeg")}
        resp = client.post(
            "/api/projects/yard-pro/diagnose",
            headers={**MARTIN_HEADERS, "Idempotency-Key": "shared-diag-key"},
            files=upload,
        )
        # Cache miss for Martin → falls through to vision (which is not
        # configured) → 503. This proves the (yard_id, key) tuple is
        # the dedup key, not just key.
        assert resp.status_code == 503, resp.text

    def test_no_key_disables_replay(self, client, session, martin_yard):
        """Without a key, every POST falls through to the real handler.
        Asserts the cache isn't accidentally activated by some sentinel
        key value."""
        self._prior_diagnosis(session, martin_yard.id, "stored-key")
        upload = {"file": ("x.jpg", BytesIO(b"\xff\xd8\xff\xd9"), "image/jpeg")}
        resp = client.post(
            "/api/projects/yard-pro/diagnose",
            headers=MARTIN_HEADERS,
            files=upload,
        )
        assert resp.status_code == 503, resp.text
