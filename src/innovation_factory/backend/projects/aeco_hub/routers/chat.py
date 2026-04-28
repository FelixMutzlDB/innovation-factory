"""Chat router for AECO Hub agents.

Two endpoints:
- ``/chat``     — Multi-Agent Supervisor (default for the agent page)
- ``/ka-chat``  — Standards & Compliance Knowledge Assistant (for
                  scoped questions about IFC, COBie, regulations, BAS)

Both use SSE streaming via the shared ``services.streaming`` utility.
History endpoints return persisted ``DtChatSession`` + ``DtChatMessage``
rows so the frontend can hydrate previous conversations.
"""
from typing import Annotated, Optional

from fastapi import APIRouter, Depends, HTTPException, Request
from sqlmodel import select

from ....dependencies import RuntimeDep, SessionDep
from ....rate_limit import limiter
from ....services.streaming import create_chat_stream
from ..models import (
    DtChatHistoryOut,
    DtChatMessage,
    DtChatMessageIn,
    DtChatMessageOut,
    DtChatSession,
    DtChatSessionOut,
)
from ..services.chat_service import ChatService

router = APIRouter(tags=["aeco-hub"])

_chat_service = ChatService()


@router.post("/chat", operation_id="aeco_sendChatMessage")
@limiter.limit("30/minute")
async def send_chat_message(
    request: Request,
    message: DtChatMessageIn,
    db: SessionDep,
    runtime: RuntimeDep,
):
    """Stream a response from the AECO Hub Supervisor."""
    stream = _chat_service.stream_mas_response(
        ws=runtime.ws,
        db=db,
        user_message=message.message,
        session_id=message.session_id,
        project_id=message.project_id,
    )
    return await create_chat_stream(
        stream,
        headers={"Cache-Control": "no-cache", "Connection": "keep-alive"},
    )


@router.post("/ka-chat", operation_id="aeco_sendKaChatMessage")
@limiter.limit("30/minute")
async def send_ka_chat_message(
    request: Request,
    message: DtChatMessageIn,
    db: SessionDep,
    runtime: RuntimeDep,
):
    """Stream a response from the Standards & Compliance KA."""
    stream = _chat_service.stream_ka_response(
        ws=runtime.ws,
        db=db,
        user_message=message.message,
        session_id=message.session_id,
        project_id=message.project_id,
    )
    return await create_chat_stream(
        stream,
        headers={"Cache-Control": "no-cache", "Connection": "keep-alive"},
    )


@router.get(
    "/chat/sessions",
    response_model=list[DtChatSessionOut],
    operation_id="aeco_listChatSessions",
)
def list_chat_sessions(
    db: SessionDep,
    project_id: Optional[int] = None,
    agent_kind: Optional[str] = None,
):
    stmt = select(DtChatSession).order_by(DtChatSession.created_at.desc())  # type: ignore[unresolved-attribute]
    if project_id is not None:
        stmt = stmt.where(DtChatSession.project_id == project_id)
    if agent_kind is not None:
        stmt = stmt.where(DtChatSession.agent_kind == agent_kind)
    return db.exec(stmt.limit(50)).all()


@router.get(
    "/chat/sessions/{session_id}",
    response_model=DtChatHistoryOut,
    operation_id="aeco_getChatSession",
)
def get_chat_session(session_id: int, db: SessionDep):
    session = db.get(DtChatSession, session_id)
    if not session:
        raise HTTPException(404, detail="Chat session not found")
    msgs = list(db.exec(
        select(DtChatMessage)
        .where(DtChatMessage.session_id == session_id)
        .order_by(DtChatMessage.created_at)  # type: ignore[invalid-argument-type]
    ).all())
    return DtChatHistoryOut(
        session=DtChatSessionOut(
            id=session.id or 0,
            project_id=session.project_id,
            agent_kind=session.agent_kind,
            created_at=session.created_at,
        ),
        messages=[DtChatMessageOut(
            id=m.id or 0,
            session_id=m.session_id,
            role=m.role,
            content=m.content,
            sources_json=m.sources_json,
            created_at=m.created_at,
        ) for m in msgs],
    )
