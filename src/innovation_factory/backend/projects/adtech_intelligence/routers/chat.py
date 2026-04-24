"""Chat router for the AdTech Intelligence agents.

Provides two chat endpoints:
- /chat       — Issue Resolution KA (Knowledge Assistant) for the issues page
- /mas-chat   — Multi-Agent Supervisor for the overview page
"""
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Request
from sqlmodel import Session, select

from ....dependencies import SessionDep, get_runtime, get_session
from ....pagination import Pagination
from ....rate_limit import limiter
from ....runtime import Runtime
from ....services.streaming import create_chat_stream
from ..models import (
    AtChatHistoryOut,
    AtChatMessage,
    AtChatMessageIn,
    AtChatMessageOut,
    AtChatSession,
)
from ..services.chat_service import ChatService

router = APIRouter(tags=["adtech-chat"])

chat_service = ChatService()


@router.post("/chat", operation_id="at_sendChatMessage")
@limiter.limit("30/minute")
async def send_chat_message(
    request: Request,
    message: AtChatMessageIn,
    db: SessionDep,
    runtime: Annotated[Runtime, Depends(get_runtime)],
):
    """Send a message to the issue-resolution KA and get a streaming response."""
    stream = chat_service.stream_ka_response(
        ws=runtime.ws,
        db=db,
        user_message=message.message,
        session_id=message.session_id,
    )
    return await create_chat_stream(
        stream,
        headers={"Cache-Control": "no-cache", "Connection": "keep-alive"},
    )


@router.post("/mas-chat", operation_id="at_sendMasChatMessage")
@limiter.limit("30/minute")
async def send_mas_chat_message(
    request: Request,
    message: AtChatMessageIn,
    db: SessionDep,
    runtime: Annotated[Runtime, Depends(get_runtime)],
):
    """Send a message to the Multi-Agent Supervisor and get a streaming response."""
    stream = chat_service.stream_mas_response(
        ws=runtime.ws,
        db=db,
        user_message=message.message,
        session_id=message.session_id,
    )
    return await create_chat_stream(
        stream,
        headers={"Cache-Control": "no-cache", "Connection": "keep-alive"},
    )


@router.get(
    "/chat/sessions",
    response_model=list[AtChatHistoryOut],
    operation_id="at_listChatSessions",
)
def list_chat_sessions(
    db: SessionDep,
    page: Pagination,
):
    """List recent chat sessions, newest first."""
    sessions = db.exec(
        select(AtChatSession)
        .order_by(AtChatSession.started_at.desc())  # type: ignore[unresolved-attribute]
        .offset(page.skip)
        .limit(page.limit)
    ).all()
    result = []
    for s in sessions:
        if s.id is None:
            raise HTTPException(status_code=500, detail="Chat session has no ID")
        messages = db.exec(
            select(AtChatMessage)
            .where(AtChatMessage.session_id == s.id)
            .order_by(AtChatMessage.created_at.asc())  # type: ignore[unresolved-attribute]
        ).all()
        result.append(
            AtChatHistoryOut(
                session_id=s.id,
                session_type=s.session_type,
                started_at=s.started_at,
                ended_at=s.ended_at,
                messages=[AtChatMessageOut.model_validate(m) for m in messages],
            )
        )
    return result


@router.get(
    "/chat/sessions/{session_id}",
    response_model=AtChatHistoryOut,
    operation_id="at_getChatSession",
)
def get_chat_session(
    session_id: int,
    db: SessionDep,
):
    """Get a specific chat session with all messages."""
    session = db.get(AtChatSession, session_id)
    if not session:
        raise HTTPException(status_code=404, detail="Chat session not found")
    if session.id is None:
        raise HTTPException(status_code=500, detail="Chat session has no ID")

    messages = db.exec(
        select(AtChatMessage)
        .where(AtChatMessage.session_id == session.id)
        .order_by(AtChatMessage.created_at.asc())  # type: ignore[unresolved-attribute]
    ).all()

    return AtChatHistoryOut(
        session_id=session.id,
        session_type=session.session_type,
        started_at=session.started_at,
        ended_at=session.ended_at,
        messages=[AtChatMessageOut.model_validate(m) for m in messages],
    )
