"""Diagnose (UC3) router — snap-and-diagnose endpoint.

Plan §8 security rails enforced here (defense-in-depth at the HTTP edge):
- 10 MB file size cap → 413.
- MIME allowlist (image/jpeg, image/png, image/heic) → 415 otherwise.
- EXIF strip on every upload → no GPS coordinates leave the pipeline.
- Rate-limit per ``X-Forwarded-User`` (lessons §21).
- ``Idempotency-Key`` header is accepted but the 24h replay cache is
  deferred to P1 (plan §12).
- ``VISION_ENDPOINT`` unset → structured 503 with ``configured: false``
  (lessons §18).
"""
from __future__ import annotations

from datetime import datetime, timedelta, timezone
from typing import Optional

from fastapi import (
    APIRouter,
    File,
    Header,
    HTTPException,
    Query,
    Request,
    Response,
    UploadFile,
)
from pydantic import BaseModel
from sqlmodel import Session, select

from ....dependencies import RuntimeDep, SessionDep
from ....rate_limit import limiter
from ..models import (
    YardProDiagnosisStatus,
    YpDiagnoseQueue,
    YpDiagnoseQueueOut,
    YpDiagnosis,
    YpDiagnosisOut,
    YpYard,
)
from ..services.diagnose_service import (
    DiagnoseNotConfiguredError,
    classify,
    strip_exif,
)

router = APIRouter(tags=["yard-pro"])


_MAX_BYTES = 10 * 1024 * 1024  # 10 MB
_ALLOWED_MIME = {"image/jpeg", "image/png", "image/heic"}

# Same Idempotency-Key + same yard within this window returns the cached
# response instead of re-running the vision endpoint. Plan §9 + §12 P1.
_IDEMPOTENCY_WINDOW = timedelta(hours=24)


def _diagnosis_to_post_out(
    d: YpDiagnosis, second_opinion_cta: str = "Get a second opinion (free dealer chat)"
) -> "YpDiagnosePostOut":
    """Project a persisted diagnosis row into the POST response shape.

    Used both on first-write and on idempotency-replay. The replay path
    can't recover the original ``response_id`` (it's not stored), so we
    derive a stable one from the row id; the ``unsure`` flag is recovered
    from the persisted ``top_label`` (the classify service sets it to
    "unsure" when below the 0.6 confidence floor).
    """
    return YpDiagnosePostOut(
        id=d.id or 0,
        yard_id=d.yard_id,
        photo_uri=d.photo_uri,
        model_version=d.model_version,
        predictions=d.predictions,
        top_label=d.top_label,
        top_confidence=d.top_confidence,
        accepted_label=d.accepted_label,
        status=d.status,
        created_at=d.created_at,
        advisory=True,
        second_opinion_cta=second_opinion_cta,
        unsure=(d.top_label == "unsure"),
        response_id=f"replay-{d.id}" if d.id is not None else "replay-0",
    )


# ---------------------------------------------------------------------------
# Response models
# ---------------------------------------------------------------------------


class YpDiagnosePostOut(YpDiagnosisOut):
    """Diagnose POST response — extends ``YpDiagnosisOut`` with the
    co-equal second-opinion CTA (plan §8). The base model already carries
    ``advisory=True`` (plan §2 Art. 50)."""

    second_opinion_cta: str
    unsure: bool
    response_id: str


# ---------------------------------------------------------------------------
# Yard resolver (X-Forwarded-User → yp_yards.user_key)
# ---------------------------------------------------------------------------


def _resolve_yard(session: Session, request: Request) -> YpYard:
    user_key = request.headers.get("X-Forwarded-User") or "martin@yard-pro.local"
    yard = session.exec(
        select(YpYard).where(YpYard.user_key == user_key)
    ).first()
    if yard is None:
        yard = session.exec(select(YpYard)).first()
    if yard is None:
        raise HTTPException(status_code=404, detail="No yard found for caller")
    return yard


# ---------------------------------------------------------------------------
# POST /diagnose — multipart upload
# ---------------------------------------------------------------------------


@router.post(
    "/diagnose",
    response_model=YpDiagnosePostOut,
    operation_id="yp_diagnose",
)
@limiter.limit("10/minute")
async def diagnose(
    request: Request,
    db: SessionDep,
    runtime: RuntimeDep,
    response: Response,
    file: UploadFile = File(...),
    idempotency_key: Optional[str] = Header(default=None, alias="Idempotency-Key"),
):
    """Diagnose a yard photo via the vision endpoint.

    Security rails (plan §8 RT-005):
    - Reject ``Content-Type`` outside the MIME allowlist with 415.
    - Reject files larger than 10 MB with 413.
    - Strip EXIF before persisting or sending to the model.

    "Not configured" (lessons §18): when ``VISION_ENDPOINT`` is unset,
    returns a structured 503 with ``configured: false`` so the UI renders
    a "requires configuration" card instead of a hard error.
    """
    # 1. MIME allowlist check.
    content_type = (file.content_type or "").lower()
    if content_type not in _ALLOWED_MIME:
        raise HTTPException(
            status_code=415,
            detail={
                "message": "Unsupported image type",
                "allowed": sorted(_ALLOWED_MIME),
                "received": content_type,
            },
        )

    # 2. Size cap — read bytes once with a hard ceiling.
    raw = await file.read(_MAX_BYTES + 1)
    if len(raw) > _MAX_BYTES:
        raise HTTPException(
            status_code=413,
            detail={
                "message": "Image too large",
                "max_bytes": _MAX_BYTES,
            },
        )

    # 3. EXIF strip — runs before bytes touch the vision endpoint.
    safe_bytes = strip_exif(raw, content_type)

    # 4. Resolve yard before running inference so a bad caller fails fast.
    yard = _resolve_yard(db, request)

    # 4b. Idempotency-Key 24h cache-replay (plan §9, plan §12 P1).
    # Skips both the vision-endpoint call AND the DB write when the
    # caller is retrying a recent request with the same key.
    if idempotency_key:
        replay_cutoff = datetime.now(timezone.utc) - _IDEMPOTENCY_WINDOW
        existing = db.exec(
            select(YpDiagnosis)
            .where(YpDiagnosis.yard_id == yard.id)
            .where(YpDiagnosis.idempotency_key == idempotency_key)
            .where(YpDiagnosis.created_at >= replay_cutoff)
            .order_by(YpDiagnosis.created_at.desc())  # type: ignore[union-attr]
            .limit(1)
        ).first()
        if existing is not None:
            response.status_code = 200
            return _diagnosis_to_post_out(existing)

    # 5. Run classification, mapping "not configured" to a structured 503.
    # ``runtime.ws`` constructs a WorkspaceClient on first access — only
    # touch it when we're going to call the vision endpoint. The
    # ``classify`` service raises ``DiagnoseNotConfiguredError`` early
    # when VISION_ENDPOINT is unset, before touching ws.
    from ..databricks_config import VISION_ENDPOINT as _vision_endpoint

    ws = runtime.ws if _vision_endpoint else None
    try:
        result = classify(ws, safe_bytes)  # type: ignore[arg-type]
    except DiagnoseNotConfiguredError as exc:
        raise HTTPException(
            status_code=503,
            detail={
                "detail": "Snap-and-diagnose requires configuration",
                "configured": False,
                "message": str(exc),
            },
        )

    # 6. Persist diagnosis. ``photo_uri`` is intentionally a placeholder
    # in P0 — the UC Volume upload step is wired by B4. The Idempotency-
    # Key is stored on the row so replay logic can land in P1 without a
    # schema migration.
    diagnosis = YpDiagnosis(
        yard_id=yard.id or 0,
        photo_uri=f"yard_pro/photos/{yard.id}/{result.response_id}.bin",
        model_version=result.model_version,
        predictions={"predictions": [p.model_dump() for p in result.predictions]},
        top_label=result.top_label,
        top_confidence=result.top_confidence,
        status=YardProDiagnosisStatus.pending,
        idempotency_key=idempotency_key,
        created_at=datetime.now(timezone.utc),
    )
    db.add(diagnosis)
    db.commit()
    db.refresh(diagnosis)

    # Tier-2 enqueue (plan §9 resilience): if the result is unsure
    # (either by the confidence floor or by the ensemble plausibility
    # downgrade), append a queue row so a human reviewer / batched
    # second pass can revisit. Append-only; the actual review UI is P3.
    if result.unsure:
        db.add(
            YpDiagnoseQueue(
                yard_id=yard.id or 0,
                diagnosis_id=diagnosis.id,
                reason=(
                    "Vision endpoint downgrade — top_label='unsure'. "
                    f"model_version={result.model_version}."
                ),
                status="queued",
            )
        )
        db.commit()

    return YpDiagnosePostOut(
        id=diagnosis.id or 0,
        yard_id=diagnosis.yard_id,
        photo_uri=diagnosis.photo_uri,
        model_version=diagnosis.model_version,
        predictions=diagnosis.predictions,
        top_label=diagnosis.top_label,
        top_confidence=diagnosis.top_confidence,
        accepted_label=diagnosis.accepted_label,
        status=diagnosis.status,
        created_at=diagnosis.created_at,
        advisory=True,  # Art. 50 — diagnose results are advisory.
        second_opinion_cta=result.second_opinion_cta,
        unsure=result.unsure,
        response_id=result.response_id,
    )


# ---------------------------------------------------------------------------
# GET /diagnose/{id}
# ---------------------------------------------------------------------------


@router.get(
    "/diagnose/{diagnosis_id}",
    response_model=YpDiagnosisOut,
    operation_id="yp_getDiagnosis",
)
def get_diagnosis(
    diagnosis_id: int,
    db: SessionDep,
    request: Request,
):
    """Fetch a single diagnosis by id, scoped to the calling yard."""
    yard = _resolve_yard(db, request)
    diag = db.get(YpDiagnosis, diagnosis_id)
    if diag is None or diag.yard_id != yard.id:
        raise HTTPException(status_code=404, detail="Diagnosis not found")
    return YpDiagnosisOut(
        id=diag.id or 0,
        yard_id=diag.yard_id,
        photo_uri=diag.photo_uri,
        model_version=diag.model_version,
        predictions=diag.predictions,
        top_label=diag.top_label,
        top_confidence=diag.top_confidence,
        accepted_label=diag.accepted_label,
        status=diag.status,
        created_at=diag.created_at,
        advisory=True,
    )


# ---------------------------------------------------------------------------
# GET /diagnose — paginated list
# ---------------------------------------------------------------------------


@router.get(
    "/diagnose",
    response_model=list[YpDiagnosisOut],
    operation_id="yp_listDiagnoses",
)
def list_diagnoses(
    db: SessionDep,
    request: Request,
    limit: int = Query(50, ge=1, le=200),
    offset: int = Query(0, ge=0),
):
    """List recent diagnoses for the calling yard."""
    yard = _resolve_yard(db, request)
    rows = db.exec(
        select(YpDiagnosis)
        .where(YpDiagnosis.yard_id == yard.id)
        .order_by(YpDiagnosis.created_at.desc())  # type: ignore[union-attr]
        .offset(offset)
        .limit(limit)
    ).all()
    return [
        YpDiagnosisOut(
            id=r.id or 0,
            yard_id=r.yard_id,
            photo_uri=r.photo_uri,
            model_version=r.model_version,
            predictions=r.predictions,
            top_label=r.top_label,
            top_confidence=r.top_confidence,
            accepted_label=r.accepted_label,
            status=r.status,
            created_at=r.created_at,
            advisory=True,
        )
        for r in rows
    ]


@router.get(
    "/diagnose-queue",
    response_model=list[YpDiagnoseQueueOut],
    operation_id="yp_listDiagnoseQueue",
)
def list_diagnose_queue(
    db: SessionDep,
    request: Request,
    status: Optional[str] = Query(default=None, description="Filter by status"),
    limit: int = Query(50, ge=1, le=200),
    offset: int = Query(0, ge=0),
) -> list[YpDiagnoseQueueOut]:
    """List Tier-2 diagnose queue rows for the caller's yard.

    Plan §9 resilience: vision-down + ensemble-downgrade + unsure-floor
    results enqueue here for a manual / batched second pass. Ops surface
    rather than a consumer one — the cockpit doesn't render this list
    in P1.
    """
    yard = _resolve_yard(db, request)
    stmt = select(YpDiagnoseQueue).where(YpDiagnoseQueue.yard_id == yard.id)
    if status is not None:
        stmt = stmt.where(YpDiagnoseQueue.status == status)
    rows = db.exec(
        stmt.order_by(YpDiagnoseQueue.created_at.desc())  # type: ignore[union-attr]
        .offset(offset)
        .limit(limit)
    ).all()
    return [
        YpDiagnoseQueueOut(
            id=r.id or 0,
            yard_id=r.yard_id,
            diagnosis_id=r.diagnosis_id,
            reason=r.reason,
            status=r.status,
            created_at=r.created_at,
        )
        for r in rows
    ]


__all__ = ["router"]
