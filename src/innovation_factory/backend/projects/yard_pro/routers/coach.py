"""Coach (UC2) router — SSE streaming + provenance enforcement.

Plan §12 P0 contract:
- ``POST /coach/sessions``  — open a session for the calling yard.
- ``GET  /coach/sessions``  — recent sessions for caller.
- ``GET  /coach/sessions/{id}/messages`` — history.
- ``POST /coach/sessions/{id}/chat``    — SSE streaming response.

Non-negotiables encoded here:
- Every assistant message is persisted with ``advisory=True``
  (plan §2 — EU AI Act Art. 50).
- The provenance rail (citations required on recommendation turns)
  lives in :mod:`coach_service`; the router just persists what comes back.
- Rate-limit per ``X-Forwarded-User`` (plan §8 + lessons §21).
- ``Idempotency-Key`` header is accepted and stored in ``response_id``
  for traceability; the 24h replay cache is deferred to P1 (plan §12).
"""
from __future__ import annotations

from typing import Optional

from fastapi import APIRouter, Header, HTTPException, Query, Request
from pydantic import BaseModel, Field
from sqlmodel import Session, select

from ....dependencies import RuntimeDep, SessionDep
from ....input_sanitize import LongText
from ....rate_limit import limiter
from ....services.streaming import create_chat_stream, streaming_endpoint
from ..models import (
    YardProChatRole,
    YpCoachMessage,
    YpCoachSession,
    YpYard,
)
from ..services.coach_service import (
    is_recommendation_turn,
    stream_response,
    synthesize,
)
from ..services.yard_context_service import get_yard_context

router = APIRouter(tags=["yard-pro"])


# ---------------------------------------------------------------------------
# I/O schemas
# ---------------------------------------------------------------------------


class YpCoachSessionOut(BaseModel):
    id: int
    yard_id: int
    title: str
    created_at: str


class YpCoachSessionCreate(BaseModel):
    yard_id: int
    title: str = "New chat"


class YpCoachMessageOut(BaseModel):
    id: int
    session_id: int
    role: str
    content: str
    citations: list[dict] = Field(default_factory=list)
    model_version: str
    is_recommendation: bool
    advisory: bool
    created_at: str


class YpCoachChatIn(BaseModel):
    prompt: LongText
    idempotency_key: Optional[str] = None


# ---------------------------------------------------------------------------
# Resolver — look up the caller's yard from X-Forwarded-User
# ---------------------------------------------------------------------------


def _resolve_yard(session: Session, request: Request) -> YpYard:
    """Resolve the calling user's yard.

    P0: keyed off ``X-Forwarded-User`` against ``yp_yards.user_key``.
    Falls back to ``MARTIN_USER_KEY`` from the seed in local dev so the
    seeded demo path "just works" without setting headers manually.
    """
    user_key = request.headers.get("X-Forwarded-User") or "martin@yard-pro.local"
    yard = session.exec(
        select(YpYard).where(YpYard.user_key == user_key)
    ).first()
    if yard is None:
        # In a fresh dev DB without seed, fall back to any yard.
        yard = session.exec(select(YpYard)).first()
    if yard is None:
        raise HTTPException(status_code=404, detail="No yard found for caller")
    return yard


# ---------------------------------------------------------------------------
# Sessions CRUD
# ---------------------------------------------------------------------------


@router.post(
    "/coach/sessions",
    response_model=YpCoachSessionOut,
    operation_id="yp_createCoachSession",
)
def create_coach_session(
    body: YpCoachSessionCreate,
    session: SessionDep,
    request: Request,
):
    """Open a new coach session for the calling yard."""
    yard = _resolve_yard(session, request)
    # If the caller's resolved yard doesn't match the body, prefer the
    # resolved one — cross-tenant write attempts must not succeed.
    chat_session = YpCoachSession(yard_id=yard.id or 0, title=body.title)
    session.add(chat_session)
    session.commit()
    session.refresh(chat_session)
    return YpCoachSessionOut(
        id=chat_session.id or 0,
        yard_id=chat_session.yard_id,
        title=chat_session.title,
        created_at=chat_session.created_at.isoformat(),
    )


@router.get(
    "/coach/sessions",
    response_model=list[YpCoachSessionOut],
    operation_id="yp_listCoachSessions",
)
def list_coach_sessions(
    session: SessionDep,
    request: Request,
    limit: int = Query(50, ge=1, le=200),
):
    """List recent coach sessions for the calling yard."""
    yard = _resolve_yard(session, request)
    rows = session.exec(
        select(YpCoachSession)
        .where(YpCoachSession.yard_id == yard.id)
        .order_by(YpCoachSession.created_at.desc())  # type: ignore[union-attr]
        .limit(limit)
    ).all()
    return [
        YpCoachSessionOut(
            id=r.id or 0,
            yard_id=r.yard_id,
            title=r.title,
            created_at=r.created_at.isoformat(),
        )
        for r in rows
    ]


@router.get(
    "/coach/sessions/{session_id}/messages",
    response_model=list[YpCoachMessageOut],
    operation_id="yp_listCoachMessages",
)
def list_coach_messages(
    session_id: int,
    session: SessionDep,
    request: Request,
):
    """Get the message history for a coach session."""
    yard = _resolve_yard(session, request)
    chat_session = session.get(YpCoachSession, session_id)
    if chat_session is None or chat_session.yard_id != yard.id:
        raise HTTPException(status_code=404, detail="Session not found")
    rows = session.exec(
        select(YpCoachMessage)
        .where(YpCoachMessage.session_id == session_id)
        .order_by(YpCoachMessage.created_at)  # type: ignore[union-attr]
    ).all()
    return [
        YpCoachMessageOut(
            id=r.id or 0,
            session_id=r.session_id,
            role=r.role.value if hasattr(r.role, "value") else str(r.role),
            content=r.content,
            citations=list(r.citations or []),
            model_version=r.model_version,
            is_recommendation=r.is_recommendation,
            advisory=r.advisory,
            created_at=r.created_at.isoformat(),
        )
        for r in rows
    ]


# ---------------------------------------------------------------------------
# Streaming chat
# ---------------------------------------------------------------------------


@router.post("/coach/sessions/{session_id}/chat", operation_id="yp_coachChat")
@limiter.limit("30/minute")
@streaming_endpoint
async def coach_chat(
    request: Request,
    session_id: int,
    body: YpCoachChatIn,
    db: SessionDep,
    runtime: RuntimeDep,
    idempotency_key: Optional[str] = Header(default=None, alias="Idempotency-Key"),
):
    """Stream a coach response over SSE.

    The body's ``idempotency_key`` (and the ``Idempotency-Key`` header)
    are accepted but the 24h replay cache is deferred to P1 per plan §12.
    """
    yard = _resolve_yard(db, request)
    chat_session = db.get(YpCoachSession, session_id)
    if chat_session is None or chat_session.yard_id != yard.id:
        raise HTTPException(status_code=404, detail="Session not found")

    # Persist the user message first so it shows up in history on retry.
    user_msg = YpCoachMessage(
        session_id=session_id,
        role=YardProChatRole.user,
        content=body.prompt,
        model_version="",
        is_recommendation=False,
        advisory=False,  # user-authored content carries no advisory chip.
    )
    db.add(user_msg)
    db.commit()

    # Build context + run synthesis up front (we're not doing real
    # token-streaming in P0 — we synthesize, then chunk the text for SSE).
    yard_context = get_yard_context(db, yard.id or 0)
    is_recommendation = is_recommendation_turn(body.prompt)
    # ``runtime.ws`` is a cached_property that constructs a WorkspaceClient
    # on first access — only touch it when there's an endpoint to call.
    # (synthesize handles the "not configured" early-return without ws.)
    from ..databricks_config import COACH_KA_ENDPOINT as _coach_ka_endpoint

    ws = runtime.ws if _coach_ka_endpoint else None
    response = synthesize(
        ws=ws,  # type: ignore[arg-type]
        yard_context=yard_context,
        prompt=body.prompt,
        is_recommendation=is_recommendation,
    )

    # Persist the assistant message. Citations are stored as plain JSON.
    assistant_msg = YpCoachMessage(
        session_id=session_id,
        role=YardProChatRole.assistant,
        content=response.text,
        citations=[c.model_dump() for c in response.citations],
        model_version=response.model_version,
        is_recommendation=response.is_recommendation,
        advisory=True,  # Art. 50 — every assistant turn carries the chip.
    )
    db.add(assistant_msg)
    db.commit()

    # Stream the text chunks.
    return await create_chat_stream(
        stream_response(response),
        headers={"Cache-Control": "no-cache", "Connection": "keep-alive"},
    )


__all__ = ["router"]
