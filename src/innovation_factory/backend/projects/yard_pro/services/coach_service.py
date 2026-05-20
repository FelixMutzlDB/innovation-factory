"""coach_service — KA-grounded synthesis with provenance enforcement.

This is the load-bearing rail for plan §2 (diagnostic honesty) and
plan §8 (provenance enforcement on recommendation turns):

- Every assistant response carries ``advisory=True`` (EU AI Act Art. 50).
- **Recommendation turns** — turns where the user asked for a specific
  action ("should I fertilize", "what should I apply", "prune now?")
  MUST return citations: ``len(citations) >= 1``. If the KA layer
  returns 0 chunks, the service returns a **safe fallback string** —
  it does NOT pass through the model's ungrounded text.
- Non-recommendation turns (general chat, weather questions) may pass
  through ungrounded.

Recommendation detection heuristic (documented for §8 audit):
- Prompt is lowercased and stripped.
- Matches an imperative verb / question phrase associated with action:
  "should i", "what should", "apply", "fertilize", "prune", "spray",
  "remove", "buy", "use", "treat", "water".
- Or matches a product/consumable name ("fertilizer", "fungicide",
  "blade", "oil").
- This is intentionally a conservative heuristic — false positives
  (treating a non-recommendation as one) just trigger the citations
  check, which is the safe failure mode.

The FM API + KA call here is wrapped in a single ``query_agent_endpoint``
invocation against ``COACH_KA_ENDPOINT`` (the KA endpoint orchestrates
retrieval + synthesis). If the endpoint isn't configured we fall back to
a "not configured" response — never a 500 (lessons §18).
"""
from __future__ import annotations

import logging
import re
import uuid
from typing import Any, AsyncIterator, Optional, cast

from databricks.sdk import WorkspaceClient
from pydantic import BaseModel, Field

from ....services.databricks_agents import extract_agent_text, query_agent_endpoint
from ..databricks_config import COACH_KA_ENDPOINT, COACH_MODEL
from .yard_context_service import YardContext

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Public types
# ---------------------------------------------------------------------------


class KaChunkRef(BaseModel):
    """Reference to a KA chunk that grounded a coach response.

    Persisted into ``yp_coach_messages.citations`` as JSON. The provenance
    rail in plan §8 requires ``len(citations) >= 1`` on recommendation
    turns; the response_model rejects ungrounded recommendations at the
    response-shape level rather than the prompt level.
    """

    doc_path: str
    chunk_id: str
    score: float = 0.0
    snippet: str = ""


class CoachResponse(BaseModel):
    """Typed response from :func:`synthesize`."""

    text: str
    citations: list[KaChunkRef] = Field(default_factory=list)
    advisory: bool = True
    is_recommendation: bool
    model_version: str
    response_id: str


# ---------------------------------------------------------------------------
# Recommendation heuristic — documented above
# ---------------------------------------------------------------------------


_RECOMMENDATION_PATTERNS = [
    r"\bshould i\b",
    r"\bwhat should\b",
    r"\bdo i need to\b",
    r"\bcan i\b.*\b(apply|spray|prune|fertili[sz]e|treat|use|remove)\b",
    r"\bapply\b",
    r"\bfertili[sz]e\b",
    r"\bprune\b",
    r"\bspray\b",
    r"\bremove\b",
    r"\bbuy\b",
    r"\buse\b.*\b(fertili[sz]er|fungicide|oil|blade|spray|product)\b",
    r"\btreat\b",
    r"\bwater\b.*\b(now|today|this)\b",
    r"\b(fungicide|fertili[sz]er|oil|consumable|product)\b",
    r"\brecommend(ation)?\b",
    r"\bnext (step|action)\b",
]
_RECOMMENDATION_RE = re.compile("|".join(_RECOMMENDATION_PATTERNS), re.IGNORECASE)

# Safe fallback string for ungrounded recommendation turns. The exact
# substring "I don't have a grounded answer" is asserted by
# test_provenance_required.py — keep it stable.
_SAFE_FALLBACK_TEXT = (
    "I don't have a grounded answer for that. Consider checking with your "
    "local dealer or a trusted gardening source."
)

_FALLBACK_MODEL_VERSION = "fallback-no-ka"
_NOT_CONFIGURED_MODEL_VERSION = "not-configured"


def is_recommendation_turn(prompt: str) -> bool:
    """True when the prompt looks like a request for a specific action.

    Heuristic — see module docstring. The downstream provenance check is
    the actual safety rail; this just decides whether to apply it.
    """
    if not prompt:
        return False
    return bool(_RECOMMENDATION_RE.search(prompt))


# ---------------------------------------------------------------------------
# KA / FM API integration
# ---------------------------------------------------------------------------


def _build_coach_prompt(yard_context: YardContext, prompt: str) -> str:
    """Render the yard context + user prompt into a single string for the
    KA endpoint. The KA endpoint owns retrieval + synthesis; we pass yard
    context inline so retrieved chunks can be filtered by region/plant/etc.
    """
    plant_list = ", ".join(
        f"{p.species} ({p.variety})" if p.variety else p.species
        for p in yard_context.plants
    ) or "(no plants on file)"
    tool_list = ", ".join(t.display_name for t in yard_context.tools) or "(no tools on file)"
    recent = "; ".join(
        f"{a.action_type} {a.occurred_at.date().isoformat()}"
        for a in yard_context.recent_actions[:5]
    ) or "(no recent actions)"
    overdue = "; ".join(c.title for c in yard_context.overdue_calendar) or "(none)"
    weather = yard_context.weather.summary

    return (
        f"Yard: {yard_context.yard.display_name} "
        f"({yard_context.yard.region_code}, {yard_context.yard.size_m2:.0f} m²)\n"
        f"Plants: {plant_list}\n"
        f"Tools: {tool_list}\n"
        f"Recent actions (last 14d): {recent}\n"
        f"Overdue calendar: {overdue}\n"
        f"Weather: {weather}\n"
        f"\nUser question: {prompt}"
    )


def _extract_citations(raw_response: object) -> list[KaChunkRef]:
    """Pull citation refs from a KA endpoint response.

    KA endpoints under the input/output protocol return a variety of
    shapes; we look for ``citations``, ``sources``, ``retrieved_chunks``
    keys at the top level or nested under ``output``. Unknown shape ⇒
    empty list (the provenance rail will then trigger the safe fallback
    on recommendation turns).
    """
    citations: list[KaChunkRef] = []

    def _harvest(items: object) -> None:
        if not isinstance(items, list):
            return
        for c in items:
            if isinstance(c, dict):
                cd = cast(dict[str, Any], c)  # ty narrows isinstance dict to dict[Unknown,Unknown]; widen for .get()
                doc_path = cd.get("doc_path") or cd.get("source") or cd.get("uri") or ""
                chunk_id = cd.get("chunk_id") or cd.get("id") or ""
                score = cd.get("score") or cd.get("relevance") or 0.0
                text_field = cd.get("text", "")
                snippet = cd.get("snippet") or (
                    text_field[:200] if isinstance(text_field, str) else ""
                )
                if doc_path or chunk_id:
                    try:
                        citations.append(
                            KaChunkRef(
                                doc_path=str(doc_path),
                                chunk_id=str(chunk_id),
                                score=float(score) if score is not None else 0.0,
                                snippet=str(snippet)[:200],
                            )
                        )
                    except (TypeError, ValueError):
                        continue

    if isinstance(raw_response, dict):
        rd = cast(dict[str, Any], raw_response)
        for key in ("citations", "sources", "retrieved_chunks", "documents"):
            _harvest(rd.get(key))
        output = rd.get("output")
        if isinstance(output, dict):
            od = cast(dict[str, Any], output)
            for key in ("citations", "sources", "retrieved_chunks", "documents"):
                _harvest(od.get(key))
        elif isinstance(output, list):
            for item in output:
                if isinstance(item, dict):
                    id_ = cast(dict[str, Any], item)
                    for key in ("citations", "sources", "retrieved_chunks", "documents"):
                        _harvest(id_.get(key))

    return citations


def synthesize(
    ws: WorkspaceClient,
    yard_context: YardContext,
    prompt: str,
    is_recommendation: Optional[bool] = None,
) -> CoachResponse:
    """Synthesize a coach response, enforcing the provenance rail.

    ``is_recommendation`` may be passed explicitly (e.g. for tests); when
    ``None`` it's inferred from the prompt via :func:`is_recommendation_turn`.
    """
    if is_recommendation is None:
        is_recommendation = is_recommendation_turn(prompt)
    response_id = uuid.uuid4().hex

    # "Not configured" path — lessons §18: first-class, never a 500.
    if not COACH_KA_ENDPOINT:
        return CoachResponse(
            text=(
                "The seasonal coach is not configured for this workspace yet. "
                "Set YARD_PRO_COACH_KA_ENDPOINT to enable grounded answers."
            ),
            citations=[],
            advisory=True,
            is_recommendation=False,
            model_version=_NOT_CONFIGURED_MODEL_VERSION,
            response_id=response_id,
        )

    rendered_prompt = _build_coach_prompt(yard_context, prompt)

    try:
        raw = query_agent_endpoint(
            ws,
            COACH_KA_ENDPOINT,
            [{"role": "user", "content": rendered_prompt}],
        )
    except Exception as exc:
        logger.error(
            "Coach KA endpoint error: %s: %s",
            type(exc).__name__,
            exc,
            exc_info=True,
        )
        return CoachResponse(
            text=(
                "The seasonal coach is unavailable right now. Please try "
                "again in a moment."
            ),
            citations=[],
            advisory=True,
            is_recommendation=False,
            model_version=_FALLBACK_MODEL_VERSION,
            response_id=response_id,
        )

    text = extract_agent_text(raw) or ""
    citations = _extract_citations(raw)

    # Provenance rail (plan §8 + §2 diagnostic honesty NN).
    if is_recommendation and len(citations) == 0:
        logger.warning(
            "Coach recommendation turn returned 0 citations — substituting "
            "safe fallback (response_id=%s)",
            response_id,
        )
        return CoachResponse(
            text=_SAFE_FALLBACK_TEXT,
            citations=[],
            advisory=True,
            is_recommendation=False,
            model_version=_FALLBACK_MODEL_VERSION,
            response_id=response_id,
        )

    return CoachResponse(
        text=text,
        citations=citations,
        advisory=True,
        is_recommendation=is_recommendation,
        model_version=COACH_MODEL or COACH_KA_ENDPOINT,
        response_id=response_id,
    )


# ---------------------------------------------------------------------------
# SSE chunking helper
# ---------------------------------------------------------------------------


async def stream_response(response: CoachResponse) -> AsyncIterator[str]:
    """Yield the response text as plain-text chunks for SSE.

    The shared streaming protocol (lessons §12) is plain text chunks
    terminated by a ``[DONE]`` sentinel. We split on whitespace so a
    long answer feels streamed, then wrap up.
    """
    text = response.text or ""
    if not text:
        yield ""
        return
    # Naive chunking — split on ~32-char windows. Keeps it visibly
    # streamed without burning tokens on a real per-token loop in P0.
    chunk_size = 64
    for i in range(0, len(text), chunk_size):
        yield text[i : i + chunk_size]
