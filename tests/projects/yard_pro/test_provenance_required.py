"""Provenance enforcement on coach recommendation turns (plan §8).

The diagnostic-honesty rail is enforced at the response-shape level, not
the prompt level. These tests assert that:

1. When ``is_recommendation=True`` and KA returns 0 chunks, the service
   substitutes the safe fallback text — it does NOT pass through the
   model's ungrounded text.
2. When KA returns ≥1 chunk, the response carries those citations and
   ``is_recommendation`` stays True.
3. When the FM/KA endpoint raises, the service falls back gracefully
   (no 500, no leaking of internals).

The recommendation heuristic itself is tested separately — any prompt
with imperative verbs / product names should trigger the rail.

The test name references the bug symptom rather than the fix:
"ungrounded recommendations leak the model's text" — see
:func:`test_ungrounded_recommendation_returns_safe_fallback` below.
"""
from __future__ import annotations

from unittest.mock import patch

import pytest

from innovation_factory.backend.projects.yard_pro.services import coach_service
from innovation_factory.backend.projects.yard_pro.services.coach_service import (
    KaChunkRef,
    is_recommendation_turn,
    synthesize,
)
from innovation_factory.backend.projects.yard_pro.services.yard_context_service import (
    YardContext,
    YardSummary,
    WeatherWindow,
)


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------


@pytest.fixture
def yard_context() -> YardContext:
    """A minimal YardContext that satisfies the typed shape — enough
    fields to render the prompt without exercising the DB."""
    return YardContext(
        yard=YardSummary(
            id=1,
            display_name="Test Yard",
            region_code="DE-BW",
            lat=48.7,
            lng=9.1,
            size_m2=900.0,
            yard_metadata={},
        ),
        plants=[],
        tools=[],
        consumables=[],
        recent_actions=[],
        upcoming_calendar=[],
        overdue_calendar=[],
        weather=WeatherWindow(),
    )


# ---------------------------------------------------------------------------
# Heuristic
# ---------------------------------------------------------------------------


class TestRecommendationHeuristic:
    @pytest.mark.parametrize(
        "prompt",
        [
            "should I fertilize the lawn?",
            "what should I do this weekend",
            "apply copper fungicide?",
            "prune the cherry tree now",
            "spray boxwood for moth",
            "should I remove the deadwood",
            "buy more fertilizer?",
            "use a fungicide on the apple",
            "treat the lawn for fusarium",
            "next action on the hedge",
            "Can I apply slow-release fertilizer now?",
        ],
    )
    def test_imperative_prompts_flagged_as_recommendation(self, prompt):
        assert is_recommendation_turn(prompt) is True, prompt

    @pytest.mark.parametrize(
        "prompt",
        [
            "tell me about my apple tree",
            "what is fusarium blight",
            "is it sunny today",
            "hello",
        ],
    )
    def test_neutral_prompts_not_flagged(self, prompt):
        assert is_recommendation_turn(prompt) is False, prompt


# ---------------------------------------------------------------------------
# Provenance enforcement (the load-bearing rail)
# ---------------------------------------------------------------------------


class TestProvenanceRail:
    def test_ungrounded_recommendation_returns_safe_fallback(self, yard_context):
        """Symptom: a recommendation turn returns the model's text without
        any KA citations behind it — that's a hallucinated recommendation
        (plan §8). Fix: substitute the safe fallback string."""
        # KA endpoint returns text but no citations.
        with patch.object(coach_service, "COACH_KA_ENDPOINT", "fake-ka"), patch(
            "innovation_factory.backend.projects.yard_pro.services.coach_service.query_agent_endpoint",
            return_value={
                "output": [
                    {
                        "type": "message",
                        "role": "assistant",
                        "content": [
                            {
                                "type": "output_text",
                                "text": "Sure — apply 30 g/m² of NPK 20-5-8 right now.",
                            }
                        ],
                    }
                ],
                # No citations / sources / retrieved_chunks key.
            },
        ):
            response = synthesize(
                ws=None,  # type: ignore[arg-type]
                yard_context=yard_context,
                prompt="should I fertilize the lawn?",
                is_recommendation=True,
            )

        # Must NOT pass through the ungrounded text.
        assert "NPK 20-5-8" not in response.text
        # MUST contain the canonical safe-fallback phrase.
        assert "I don't have a grounded answer" in response.text
        # Provenance rail flips this off — the fallback isn't itself a
        # recommendation.
        assert response.is_recommendation is False
        assert response.citations == []
        assert response.model_version == "fallback-no-ka"
        # Advisory chip still applies (Art. 50).
        assert response.advisory is True

    def test_grounded_recommendation_passes_through(self, yard_context):
        """With ≥1 KA chunk, the model's text passes through and the
        citations populate the response."""
        with patch.object(coach_service, "COACH_KA_ENDPOINT", "fake-ka"), patch(
            "innovation_factory.backend.projects.yard_pro.services.coach_service.query_agent_endpoint",
            return_value={
                "output": [
                    {
                        "type": "message",
                        "role": "assistant",
                        "content": [
                            {
                                "type": "output_text",
                                "text": "Apply slow-release NPK 20-5-8 at 30 g/m².",
                            }
                        ],
                    }
                ],
                "citations": [
                    {
                        "doc_path": "ka_docs/regional_almanac/stuttgart_may.md",
                        "chunk_id": "c-stuttgart-may-fertilize",
                        "score": 0.91,
                        "snippet": "May is peak window for slow-release NPK in the Stuttgart kettle.",
                    },
                    {
                        "doc_path": "ka_docs/consumables/fertilizer_npk.md",
                        "chunk_id": "c-npk-005",
                        "score": 0.83,
                    },
                ],
            },
        ):
            response = synthesize(
                ws=None,  # type: ignore[arg-type]
                yard_context=yard_context,
                prompt="should I fertilize the lawn?",
                is_recommendation=True,
            )
        assert "NPK 20-5-8" in response.text
        assert response.is_recommendation is True
        assert len(response.citations) >= 1
        assert all(isinstance(c, KaChunkRef) for c in response.citations)
        assert response.citations[0].doc_path

    def test_fm_api_exception_falls_back_gracefully(self, yard_context):
        """A raise from the KA/FM API path must NOT propagate as a 500 —
        the service substitutes a "coach unavailable" message instead."""
        with patch.object(coach_service, "COACH_KA_ENDPOINT", "fake-ka"), patch(
            "innovation_factory.backend.projects.yard_pro.services.coach_service.query_agent_endpoint",
            side_effect=RuntimeError("upstream 500"),
        ):
            response = synthesize(
                ws=None,  # type: ignore[arg-type]
                yard_context=yard_context,
                prompt="should I fertilize?",
                is_recommendation=True,
            )
        # The synthesize layer absorbs the error; the user sees a friendly
        # message, the advisory chip stays on.
        assert response.advisory is True
        assert "unavailable" in response.text.lower() or "moment" in response.text.lower()
        # Critically: not a hallucinated recommendation.
        assert response.is_recommendation is False
        assert response.citations == []

    def test_not_configured_path_does_not_500(self, yard_context):
        """``COACH_KA_ENDPOINT`` unset (lessons §18) — synthesize must
        return the "not configured" response, never raise."""
        with patch.object(coach_service, "COACH_KA_ENDPOINT", ""):
            response = synthesize(
                ws=None,  # type: ignore[arg-type]
                yard_context=yard_context,
                prompt="should I fertilize?",
                is_recommendation=True,
            )
        assert response.is_recommendation is False  # safe default
        assert response.model_version == "not-configured"
        assert "not configured" in response.text.lower()
        assert response.advisory is True

    def test_non_recommendation_with_no_citations_passes_through(self, yard_context):
        """For a *non-*recommendation prompt (e.g. "tell me about my apple
        tree"), ungrounded model text is allowed — the rail only fires
        on recommendation turns."""
        with patch.object(coach_service, "COACH_KA_ENDPOINT", "fake-ka"), patch(
            "innovation_factory.backend.projects.yard_pro.services.coach_service.query_agent_endpoint",
            return_value={
                "output": [
                    {
                        "type": "message",
                        "role": "assistant",
                        "content": [
                            {"type": "output_text", "text": "Your apple tree is a Boskoop variety."}
                        ],
                    }
                ],
            },
        ):
            response = synthesize(
                ws=None,  # type: ignore[arg-type]
                yard_context=yard_context,
                prompt="tell me about my apple tree",
                is_recommendation=False,
            )
        assert "Boskoop" in response.text
        assert response.is_recommendation is False
