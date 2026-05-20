"""diagnose_service — Mosaic AI Vision endpoint client + safety rails.

Plan §8 security rows applied here:
- **Confidence floor** — ``top_confidence < 0.6`` collapses to
  ``top_label='unsure'`` + ``unsure=True``. The co-equal "second opinion"
  CTA is returned on every response (per plan §12 P0 row), regardless
  of the confidence level — the frontend always shows it.
- **No ensemble plausibility check in P0** (that's P1 per plan §12).
- **EXIF strip happens at the router boundary** (``routers/diagnose.py``)
  before bytes reach this service — defense-in-depth.

The "not configured" path returns a structured 503 by raising
``DiagnoseNotConfiguredError`` (caught at the router layer and converted
to ``HTTPException(503)``) — lessons §18.
"""
from __future__ import annotations

import logging
import uuid
from typing import Any, Optional, cast

from databricks.sdk import WorkspaceClient
from pydantic import BaseModel, Field

from ..databricks_config import VISION_ENDPOINT

logger = logging.getLogger(__name__)


# Plan §8 + UC3 success criterion #3.
_CONFIDENCE_FLOOR = 0.6
_SECOND_OPINION_CTA = "Get a second opinion (free dealer chat)"
_UNSURE_LABEL = "unsure"


class DiagnoseNotConfiguredError(RuntimeError):
    """Raised when ``VISION_ENDPOINT`` is unset. Mapped to 503 at HTTP layer."""


class DiagnosePrediction(BaseModel):
    name: str
    confidence: float = 0.0


class DiagnoseResult(BaseModel):
    """Output of :func:`classify`. The HTTP-layer response wraps this in
    ``YpDiagnosisOut`` after persisting to ``yp_diagnoses``."""

    predictions: list[DiagnosePrediction] = Field(default_factory=list)
    top_label: str
    top_confidence: float
    unsure: bool
    second_opinion_cta: str = _SECOND_OPINION_CTA
    model_version: str
    response_id: str


def _parse_predictions(raw: Any) -> list[DiagnosePrediction]:
    """Pull a list of ``{name, confidence}`` shapes out of an endpoint
    response. Handles several common output shapes:

    - ``{"predictions": [{"label": "...", "score": ...}, ...]}``
    - ``{"output": [{"name": "...", "confidence": ...}, ...]}``
    - ``{"labels": [{"name": ..., "confidence": ...}, ...]}``
    - ``{"predictions": [{"name": ..., "confidence": ...}, ...]}``
    """

    def _harvest(items: object) -> list[DiagnosePrediction]:
        result: list[DiagnosePrediction] = []
        if not isinstance(items, list):
            return result
        for item in items:
            if not isinstance(item, dict):
                continue
            it = cast(dict[str, Any], item)
            name = it.get("name") or it.get("label") or it.get("class") or ""
            conf_raw = (
                it.get("confidence")
                or it.get("score")
                or it.get("probability")
                or 0.0
            )
            try:
                conf = float(conf_raw) if conf_raw is not None else 0.0
            except (TypeError, ValueError):
                conf = 0.0
            if name:
                result.append(DiagnosePrediction(name=str(name), confidence=conf))
        return result

    if isinstance(raw, dict):
        rd = cast(dict[str, Any], raw)
        for key in ("predictions", "labels", "output", "results"):
            harvested = _harvest(rd.get(key))
            if harvested:
                return harvested
        # Some endpoints return a single ``{label, score}`` dict.
        if "label" in rd or "name" in rd:
            return _harvest([rd])
    elif isinstance(raw, list):
        return _harvest(raw)

    return []


def _apply_confidence_floor(predictions: list[DiagnosePrediction]) -> tuple[str, float, bool]:
    """Apply the plan §8 confidence floor.

    Returns ``(top_label, top_confidence, unsure)``.
    """
    if not predictions:
        return _UNSURE_LABEL, 0.0, True
    predictions_sorted = sorted(predictions, key=lambda p: p.confidence, reverse=True)
    top = predictions_sorted[0]
    if top.confidence < _CONFIDENCE_FLOOR:
        return _UNSURE_LABEL, float(top.confidence), True
    return top.name, float(top.confidence), False


#: Confidence at or above which the ensemble plausibility check fires
#: (plan §8 RT-002: "On confidence ≥ 0.8 responses, run an ensemble
#: plausibility check"). Below this we trust the vision endpoint's
#: confidence; above it, we cross-check with the FM API.
_ENSEMBLE_PLAUSIBILITY_THRESHOLD = 0.8


def ensemble_plausibility_check(
    fm_caller: Optional["FmPlausibilityCaller"],
    label: str,
    context_text: str,
) -> Optional[bool]:
    """Cross-check a high-confidence vision label with the FM API.

    Plan §8 RT-002 (Critical re-rated 2026-05-12): "confidence floor
    alone is insufficient — a 0.85-confidence wrong answer is the
    actual failure mode." Mitigation: on top_confidence ≥ 0.8, rephrase
    the label into a yes/no plausibility prompt ("is fusarium blight
    plausible on apple bark in May Stuttgart?") and ask the coach FM
    API. If FM disagrees, the vision result is downgraded to "unsure".

    Returns:
    - ``True`` if FM says the label is plausible
    - ``False`` if FM says it's implausible
    - ``None`` if ``fm_caller`` is unavailable (skip the check; we
      trust the vision endpoint's confidence in that case rather than
      hard-failing)
    """
    if fm_caller is None:
        return None
    prompt = (
        f"Plausibility check. Vision model says: '{label}'. "
        f"Yard context: {context_text}. "
        f"Reply with one word — YES if this diagnosis is plausible for the "
        f"given context, NO if it is not."
    )
    try:
        reply = fm_caller(prompt)
    except Exception as exc:
        logger.warning(
            "Plausibility check failed (%s: %s) — skipping",
            type(exc).__name__,
            exc,
        )
        return None
    if not reply:
        return None
    head = reply.strip().split()[0].upper().rstrip(".,!?:;")
    if head == "YES":
        return True
    if head == "NO":
        return False
    return None


#: Type alias for the FM plausibility caller — any callable that takes a
#: prompt and returns the model's reply. The diagnose router wires this
#: to ``coach_service.synthesize`` (or a stub in tests).
FmPlausibilityCaller = Any  # callable: (str) -> str


def classify(
    ws: WorkspaceClient,
    image_bytes: bytes,
    *,
    fm_plausibility_caller: Optional[FmPlausibilityCaller] = None,
    yard_context_text: str = "",
) -> DiagnoseResult:
    """Run a vision classification against ``VISION_ENDPOINT``.

    Raises :class:`DiagnoseNotConfiguredError` when the endpoint is unset
    so the router can return a structured 503 (lessons §18). Any other
    exception is logged and surfaces as an "unsure" result so the demo
    never sees a hard 500 — the second-opinion CTA is the user-visible
    safety rail.

    Plan §8 RT-002: when the vision model returns ``top_confidence ≥
    0.8``, the ensemble plausibility check runs (if ``fm_plausibility_
    caller`` is provided) — FM-API yes/no on the label given the yard
    context. If FM disagrees, the result is downgraded to "unsure"
    with ``model_version`` annotated to surface the downgrade.
    """
    response_id = uuid.uuid4().hex

    if not VISION_ENDPOINT:
        raise DiagnoseNotConfiguredError(
            "Snap-and-diagnose requires configuration (YARD_PRO_VISION_ENDPOINT unset)"
        )

    try:
        # Mosaic AI Model Serving accepts base64-encoded image bytes
        # under a ``dataframe_records`` or raw ``inputs`` payload; we use
        # the input-array shape consistent with our other endpoint calls.
        import base64

        body = {
            "inputs": [
                {
                    "image_b64": base64.b64encode(image_bytes).decode("ascii"),
                }
            ]
        }
        raw = ws.api_client.do(
            "POST",
            f"/serving-endpoints/{VISION_ENDPOINT}/invocations",
            body=body,
        )
    except Exception as exc:  # pragma: no cover — exercised via tests w/ mocks
        logger.error(
            "Vision endpoint error: %s: %s",
            type(exc).__name__,
            exc,
            exc_info=True,
        )
        return DiagnoseResult(
            predictions=[],
            top_label=_UNSURE_LABEL,
            top_confidence=0.0,
            unsure=True,
            second_opinion_cta=_SECOND_OPINION_CTA,
            model_version=f"{VISION_ENDPOINT}-error",
            response_id=response_id,
        )

    predictions = _parse_predictions(raw)
    top_label, top_confidence, unsure = _apply_confidence_floor(predictions)

    # Ensemble plausibility check on high-confidence answers (RT-002).
    # Only fires when the vision model is already sure and a caller was
    # provided. Disagreement → downgrade to "unsure" + annotate the
    # model_version so the downgrade is visible to the cockpit.
    model_version_out = VISION_ENDPOINT
    if (
        not unsure
        and top_confidence >= _ENSEMBLE_PLAUSIBILITY_THRESHOLD
    ):
        plausibility = ensemble_plausibility_check(
            fm_plausibility_caller, top_label, yard_context_text
        )
        if plausibility is False:
            logger.info(
                "Vision %s @ %.2f downgraded to 'unsure' by ensemble "
                "plausibility check (response_id=%s)",
                top_label,
                top_confidence,
                response_id,
            )
            top_label = _UNSURE_LABEL
            unsure = True
            model_version_out = f"{VISION_ENDPOINT}-plausibility-downgrade"

    return DiagnoseResult(
        predictions=predictions,
        top_label=top_label,
        top_confidence=top_confidence,
        unsure=unsure,
        second_opinion_cta=_SECOND_OPINION_CTA,
        model_version=model_version_out,
        response_id=response_id,
    )


# ---------------------------------------------------------------------------
# EXIF strip — runs at the router boundary on every upload
# ---------------------------------------------------------------------------


def strip_exif(image_bytes: bytes, content_type: str) -> bytes:
    """Strip EXIF metadata from an uploaded image so GPS coordinates never
    leave the upload pipeline (plan §8 RT-005).

    Uses Pillow if available; otherwise returns the bytes unchanged with
    a warning. Pillow is a widely-available transitive dep but we don't
    want to require it for the entire backend — the "no torch import"
    invariant in plan §8 / §14 keeps the dep surface tight.
    """
    try:
        from io import BytesIO

        from PIL import Image  # type: ignore[import-not-found]
    except ImportError:
        logger.warning(
            "Pillow not installed; EXIF strip is a no-op. "
            "Install Pillow to enforce the RT-005 mitigation."
        )
        return image_bytes

    try:
        with Image.open(BytesIO(image_bytes)) as img:
            # Force RGB to drop alpha + any non-standard color profiles.
            stripped = Image.new(img.mode if img.mode in ("RGB", "L") else "RGB", img.size)
            stripped.putdata(list(img.getdata()))  # type: ignore[arg-type]
            out = BytesIO()
            # Map a few common content types to PIL format names.
            if content_type == "image/png":
                fmt = "PNG"
            elif content_type in ("image/jpeg", "image/jpg"):
                fmt = "JPEG"
            elif content_type == "image/heic":
                # Pillow needs pillow-heif for HEIC; fall back to JPEG so
                # bytes still round-trip without EXIF.
                fmt = "JPEG"
            else:
                fmt = "JPEG"
            stripped.save(out, format=fmt)
            return out.getvalue()
    except Exception as exc:
        logger.warning(
            "EXIF strip failed (%s: %s); passing original bytes",
            type(exc).__name__,
            exc,
        )
        return image_bytes


__all__ = [
    "DiagnoseNotConfiguredError",
    "DiagnosePrediction",
    "DiagnoseResult",
    "classify",
    "strip_exif",
]
