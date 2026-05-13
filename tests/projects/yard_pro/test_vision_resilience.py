"""Vision-resilience regression tests (plan §12 P1 / RT-002 + §9 Tier-2).

Three coupled invariants:
1. **Ensemble plausibility check** — on top_confidence ≥ 0.8 the
   classifier asks the FM API "is this label plausible?" and downgrades
   to "unsure" on disagreement (RT-002 Critical re-rating).
2. **Tier-2 diagnose queue** — unsure results (whether by the floor or
   the ensemble downgrade) enqueue an YpDiagnoseQueue row for batched
   second-pass review.
3. **kbqa_agent contract** — coach response parsing handles the live
   yard-pro KA endpoint shape (extract_agent_text contract).
"""
from __future__ import annotations

from datetime import datetime, timezone
from io import BytesIO

import pytest

import innovation_factory.backend.projects.yard_pro.models  # noqa: F401


MARTIN_HEADERS = {"X-Forwarded-User": "vision-resilience-martin@yard-pro.local"}


def _seed_yard(session, user_key: str = "vision-resilience-martin@yard-pro.local"):
    from sqlmodel import select

    from innovation_factory.backend.projects.yard_pro.models import YpYard

    existing = session.exec(
        select(YpYard).where(YpYard.user_key == user_key)
    ).first()
    if existing:
        return existing
    y = YpYard(
        user_key=user_key,
        display_name="Vision Test Yard",
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


# ---------------------------------------------------------------------------
# 1. Ensemble plausibility check (RT-002)
# ---------------------------------------------------------------------------


class TestEnsemblePlausibility:
    def test_returns_none_when_caller_is_unavailable(self):
        from innovation_factory.backend.projects.yard_pro.services.diagnose_service import (
            ensemble_plausibility_check,
        )

        assert ensemble_plausibility_check(None, "apple_scab", "context") is None

    def test_returns_true_on_yes(self):
        from innovation_factory.backend.projects.yard_pro.services.diagnose_service import (
            ensemble_plausibility_check,
        )

        result = ensemble_plausibility_check(lambda p: "YES", "apple_scab", "x")
        assert result is True

    def test_returns_false_on_no(self):
        from innovation_factory.backend.projects.yard_pro.services.diagnose_service import (
            ensemble_plausibility_check,
        )

        result = ensemble_plausibility_check(lambda p: "no.", "apple_scab", "x")
        assert result is False

    def test_returns_none_on_ambiguous_reply(self):
        from innovation_factory.backend.projects.yard_pro.services.diagnose_service import (
            ensemble_plausibility_check,
        )

        result = ensemble_plausibility_check(
            lambda p: "Maybe, hard to say without more context.",
            "apple_scab",
            "x",
        )
        assert result is None

    def test_returns_none_on_caller_exception(self):
        from innovation_factory.backend.projects.yard_pro.services.diagnose_service import (
            ensemble_plausibility_check,
        )

        def boom(_):
            raise RuntimeError("FM API down")

        assert ensemble_plausibility_check(boom, "apple_scab", "x") is None


class TestClassifyEnsembleIntegration:
    """Direct service-layer tests: confidence ≥ 0.8 + FM disagree
    → unsure + model_version annotated with the downgrade reason.
    Mocks the vision endpoint via monkeypatch."""

    def _mock_ws(self, monkeypatch, predictions):
        """Patch WorkspaceClient + VISION_ENDPOINT so classify() runs
        against a controlled response."""
        import innovation_factory.backend.projects.yard_pro.services.diagnose_service as svc

        class _FakeWs:
            class api_client:
                @staticmethod
                def do(*args, **kwargs):
                    return {"predictions": predictions}

        monkeypatch.setattr(svc, "VISION_ENDPOINT", "fake-endpoint")
        return _FakeWs()

    def test_high_confidence_downgrades_when_fm_says_no(self, monkeypatch):
        from innovation_factory.backend.projects.yard_pro.services import (
            diagnose_service as svc,
        )

        ws = self._mock_ws(monkeypatch, [{"name": "fusarium_blight", "confidence": 0.92}])
        result = svc.classify(
            ws,  # type: ignore[arg-type]
            b"fake",
            fm_plausibility_caller=lambda p: "NO",
            yard_context_text="Apple bark, May, Stuttgart microclimate",
        )
        assert result.unsure is True
        assert result.top_label == "unsure"
        assert "plausibility-downgrade" in result.model_version

    def test_high_confidence_kept_when_fm_says_yes(self, monkeypatch):
        from innovation_factory.backend.projects.yard_pro.services import (
            diagnose_service as svc,
        )

        ws = self._mock_ws(monkeypatch, [{"name": "fusarium_blight", "confidence": 0.92}])
        result = svc.classify(
            ws,  # type: ignore[arg-type]
            b"fake",
            fm_plausibility_caller=lambda p: "YES",
            yard_context_text="Apple bark, May, Stuttgart microclimate",
        )
        assert result.unsure is False
        assert result.top_label == "fusarium_blight"

    def test_low_confidence_does_not_invoke_plausibility(self, monkeypatch):
        """Below the threshold the FM caller MUST NOT fire (the confidence
        floor in _apply_confidence_floor already downgraded)."""
        from innovation_factory.backend.projects.yard_pro.services import (
            diagnose_service as svc,
        )

        fm_called = {"n": 0}

        def fm(p):
            fm_called["n"] += 1
            return "NO"

        ws = self._mock_ws(monkeypatch, [{"name": "fusarium_blight", "confidence": 0.45}])
        result = svc.classify(
            ws,  # type: ignore[arg-type]
            b"fake",
            fm_plausibility_caller=fm,
            yard_context_text="x",
        )
        assert result.unsure is True  # confidence floor downgrade
        assert result.top_label == "unsure"
        assert fm_called["n"] == 0, (
            "Plausibility check fired below the 0.8 threshold — the "
            "vision endpoint already said it wasn't sure, the FM API "
            "shouldn't be re-asked."
        )

    def test_high_confidence_with_no_fm_caller_keeps_label(self, monkeypatch):
        """Skip path: fm_plausibility_caller=None → no downgrade."""
        from innovation_factory.backend.projects.yard_pro.services import (
            diagnose_service as svc,
        )

        ws = self._mock_ws(monkeypatch, [{"name": "fusarium_blight", "confidence": 0.85}])
        result = svc.classify(
            ws,  # type: ignore[arg-type]
            b"fake",
            fm_plausibility_caller=None,
        )
        assert result.unsure is False
        assert result.top_label == "fusarium_blight"


# ---------------------------------------------------------------------------
# 2. Tier-2 diagnose queue
# ---------------------------------------------------------------------------


class TestTier2Queue:
    def test_unsure_diagnosis_enqueues_tier2_row(self, client, session, monkeypatch):
        """When the vision endpoint returns unsure (forced via mock),
        the POST /diagnose flow appends to yp_diagnose_queue."""
        from sqlmodel import select

        from innovation_factory.backend.projects.yard_pro.models import YpDiagnoseQueue
        import innovation_factory.backend.projects.yard_pro.services.diagnose_service as svc

        _seed_yard(session)

        # Mock classify() so we don't need a live vision endpoint.
        from innovation_factory.backend.projects.yard_pro.services.diagnose_service import (
            DiagnoseResult,
            _SECOND_OPINION_CTA,
        )

        def fake_classify(ws, image_bytes, **kwargs):
            return DiagnoseResult(
                predictions=[],
                top_label="unsure",
                top_confidence=0.0,
                unsure=True,
                second_opinion_cta=_SECOND_OPINION_CTA,
                model_version="mock-vision-unsure",
                response_id="fake-resp-123",
            )

        monkeypatch.setattr(svc, "VISION_ENDPOINT", "fake-endpoint")
        # Patch the classify symbol imported into the diagnose router.
        import innovation_factory.backend.projects.yard_pro.routers.diagnose as diag_router

        monkeypatch.setattr(diag_router, "classify", fake_classify)

        upload = {"file": ("x.jpg", BytesIO(b"\xff\xd8\xff\xd9"), "image/jpeg")}
        resp = client.post(
            "/api/projects/yard-pro/diagnose",
            headers=MARTIN_HEADERS,
            files=upload,
        )
        assert resp.status_code == 200, resp.text
        body = resp.json()
        assert body["unsure"] is True

        queued = list(
            session.exec(
                select(YpDiagnoseQueue).where(
                    YpDiagnoseQueue.diagnosis_id == body["id"]
                )
            ).all()
        )
        assert len(queued) == 1
        assert queued[0].status == "queued"
        assert "unsure" in queued[0].reason

    def test_confident_diagnosis_does_not_enqueue(self, client, session, monkeypatch):
        from sqlmodel import select

        from innovation_factory.backend.projects.yard_pro.models import YpDiagnoseQueue
        import innovation_factory.backend.projects.yard_pro.services.diagnose_service as svc
        from innovation_factory.backend.projects.yard_pro.services.diagnose_service import (
            DiagnoseResult,
            _SECOND_OPINION_CTA,
        )

        _seed_yard(session, user_key="vision-conf-martin@yard-pro.local")

        def fake_classify(ws, image_bytes, **kwargs):
            return DiagnoseResult(
                predictions=[],
                top_label="apple_scab",
                top_confidence=0.75,
                unsure=False,
                second_opinion_cta=_SECOND_OPINION_CTA,
                model_version="mock-vision-confident",
                response_id="fake-resp-456",
            )

        monkeypatch.setattr(svc, "VISION_ENDPOINT", "fake-endpoint")
        import innovation_factory.backend.projects.yard_pro.routers.diagnose as diag_router

        monkeypatch.setattr(diag_router, "classify", fake_classify)

        before = len(
            list(session.exec(select(YpDiagnoseQueue)).all())
        )

        upload = {"file": ("x.jpg", BytesIO(b"\xff\xd8\xff\xd9"), "image/jpeg")}
        resp = client.post(
            "/api/projects/yard-pro/diagnose",
            headers={"X-Forwarded-User": "vision-conf-martin@yard-pro.local"},
            files=upload,
        )
        assert resp.status_code == 200, resp.text
        assert resp.json()["unsure"] is False

        after = len(list(session.exec(select(YpDiagnoseQueue)).all()))
        assert after == before, (
            "Confident diagnoses must NOT be enqueued for Tier-2 review"
        )

    def test_list_queue_endpoint_returns_caller_rows_only(
        self, client, session, monkeypatch
    ):
        """RLS regression: GET /diagnose/queue returns only the caller's
        yard's queue rows."""
        from innovation_factory.backend.projects.yard_pro.models import YpDiagnoseQueue

        own = _seed_yard(session, user_key="vision-queue-owner@yard-pro.local")
        stranger = _seed_yard(session, user_key="vision-queue-stranger@yard-pro.local")
        session.add(
            YpDiagnoseQueue(
                yard_id=own.id, diagnosis_id=None, reason="mine", status="queued"
            )
        )
        session.add(
            YpDiagnoseQueue(
                yard_id=stranger.id,
                diagnosis_id=None,
                reason="stranger",
                status="queued",
            )
        )
        session.commit()

        resp = client.get(
            "/api/projects/yard-pro/diagnose-queue",
            headers={"X-Forwarded-User": "vision-queue-owner@yard-pro.local"},
        )
        assert resp.status_code == 200, resp.text
        rows = resp.json()
        assert all(r["yard_id"] == own.id for r in rows)
        assert any(r["reason"] == "mine" for r in rows)
        assert not any(r["reason"] == "stranger" for r in rows)


# ---------------------------------------------------------------------------
# 3. kbqa_agent contract — extract_agent_text against the live yard-pro
#    KA response shape (captured 2026-05-13 against ka-7598e04d-endpoint)
# ---------------------------------------------------------------------------


class TestKbqaAgentContract:
    """The yard-pro KA endpoint returns model "kbqa_agent" with an
    output[] of message objects. coach_service routes through the
    shared extract_agent_text helper — these tests pin the contract
    so a future SDK or KA response-shape change is caught immediately.
    """

    def test_extract_handles_kbqa_agent_message_shape(self):
        """The live yard-pro KA shape observed during the 2026-05-13
        deploy verification."""
        from innovation_factory.backend.services.databricks_agents import (
            extract_agent_text,
        )

        resp = {
            "model": "kbqa_agent",
            "output": [
                {
                    "type": "message",
                    "id": "abc-123",
                    "role": "assistant",
                    "content": [
                        {
                            "type": "output_text",
                            "text": "May is the busiest month in the Stuttgart garden calendar.",
                            "annotations": [],
                            "logprobs": [],
                        }
                    ],
                }
            ],
            "custom_outputs": {"sources_used": True},
        }
        assert (
            extract_agent_text(resp)
            == "May is the busiest month in the Stuttgart garden calendar."
        )

    def test_extract_handles_kbqa_agent_with_no_output(self):
        """Defensive: KA returns no output at all (edge case observed
        for unanswerable prompts). extract_agent_text returns a
        non-empty string so the caller doesn't crash on .strip().
        """
        from innovation_factory.backend.services.databricks_agents import (
            extract_agent_text,
        )

        resp = {"model": "kbqa_agent"}
        # The shared helper falls back to str(response) — non-empty.
        result = extract_agent_text(resp)
        assert isinstance(result, str)
