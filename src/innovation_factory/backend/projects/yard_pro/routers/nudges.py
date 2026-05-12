"""Nudges router — UC4 surface for tool-readiness notifications.

Plan §2 UC4: "tool-readiness nudges" with simulated telemetry in P1-P3.
This router is the consumer-app rail; the dealer-side Genie panel (UC6)
is a separate path that reads aggregated telemetry from Delta Gold.

**Art. 22 boundary.** Nudges are notifications, not auto-actions. The
``POST /nudges/{nudge_id}/dismiss`` endpoint records the dismissal but
NEVER writes into ``yp_action_log``. To convert a nudge into a
confirmed action the user clicks the ``<MarkAsDone>`` UI affordance,
which calls ``POST /actions`` with ``source='telemetry_nudge' +
human_confirmed_at``. The contract is enforced by the existing Art. 22
invariant test plus an explicit regression test here that the dismiss
endpoint produces zero ``yp_action_log`` rows.
"""
from __future__ import annotations

from fastapi import APIRouter, HTTPException, Request

from ....dependencies import SessionDep
from ....rate_limit import limiter
from ..models import YpNudgeOut, YpSynthesisResult
from ..services.telemetry_service import (
    dismiss_nudge,
    list_nudges_for_yard,
    synthesize_for_yard,
)
from .yards import get_caller_yard

router = APIRouter(tags=["yard-pro"])


@router.get(
    "/nudges",
    response_model=list[YpNudgeOut],
    operation_id="yp_listNudges",
)
def list_nudges(request: Request, db: SessionDep) -> list[YpNudgeOut]:
    """Return active nudges for the calling yard.

    Derived from ``YpToolReadiness`` (a snapshot — see services/
    telemetry_service.py). Suppresses any nudge_id that has a prior
    ``YpNudgeDismissal`` row; a new nudge_id is generated when the
    underlying readiness state changes.
    """
    yard = get_caller_yard(request, db)
    return list_nudges_for_yard(db, yard.id or 0)


@router.post(
    "/nudges/{nudge_id}/dismiss",
    response_model=dict,
    operation_id="yp_dismissNudge",
)
def dismiss_nudge_endpoint(
    nudge_id: str, request: Request, db: SessionDep
) -> dict:
    """Soft-dismiss a nudge. Idempotent — second call is a no-op.

    Does NOT write a ``yp_action_log`` row. The mark-as-done affordance
    is a separate UI path that calls ``POST /actions`` with ``source=
    'telemetry_nudge' + human_confirmed_at``. Plan §2 invariant.
    """
    yard = get_caller_yard(request, db)
    if not nudge_id:
        raise HTTPException(status_code=400, detail="nudge_id required")
    created = dismiss_nudge(db, yard.id or 0, nudge_id)
    return {"nudge_id": nudge_id, "dismissed": True, "created": created}


@router.post(
    "/nudges/synthesize",
    response_model=YpSynthesisResult,
    operation_id="yp_synthesizeTelemetry",
)
@limiter.limit("12/minute")
def synthesize_telemetry(
    request: Request, db: SessionDep
) -> YpSynthesisResult:
    """Manual synthesizer trigger — for the demo + the cron equivalent.

    In production this runs on a schedule; the manual endpoint exists so
    a demo can force-refresh readiness state. Rate-limited per
    ``X-Forwarded-User`` (lessons §21) since it walks every tool the
    caller owns and upserts readiness rows.
    """
    yard = get_caller_yard(request, db)
    return synthesize_for_yard(db, yard.id or 0)


__all__ = ["router"]
