"""Chat router for the AdTech Intelligence agents.

Provides two chat endpoints:
- /chat       — Issue Resolution KA (Knowledge Assistant) for the issues page
- /mas-chat   — Multi-Agent Supervisor for the overview page
"""
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import StreamingResponse
from sqlmodel import Session, select

from ....dependencies import get_session, get_runtime
from ....runtime import Runtime
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
async def send_chat_message(
    message: AtChatMessageIn,
    db: Annotated[Session, Depends(get_session)],
    runtime: Annotated[Runtime, Depends(get_runtime)],
):
    """Send a message to the issue-resolution KA and get a streaming response."""

    async def event_generator():
        async for chunk in chat_service.stream_ka_response(
            ws=runtime.ws,
            db=db,
            user_message=message.message,
            session_id=message.session_id,
        ):
            yield f"data: {chunk}\n\n"

    return StreamingResponse(
        event_generator(),
        media_type="text/event-stream",
        headers={"Cache-Control": "no-cache", "Connection": "keep-alive"},
    )


@router.post("/mas-chat", operation_id="at_sendMasChatMessage")
async def send_mas_chat_message(
    message: AtChatMessageIn,
    db: Annotated[Session, Depends(get_session)],
    runtime: Annotated[Runtime, Depends(get_runtime)],
):
    """Send a message to the Multi-Agent Supervisor and get a streaming response."""

    async def event_generator():
        async for chunk in chat_service.stream_mas_response(
            ws=runtime.ws,
            db=db,
            user_message=message.message,
            session_id=message.session_id,
        ):
            yield f"data: {chunk}\n\n"

    return StreamingResponse(
        event_generator(),
        media_type="text/event-stream",
        headers={"Cache-Control": "no-cache", "Connection": "keep-alive"},
    )


@router.get(
    "/chat/sessions",
    response_model=list[AtChatHistoryOut],
    operation_id="at_listChatSessions",
)
def list_chat_sessions(
    db: Annotated[Session, Depends(get_session)],
):
    """List recent chat sessions."""
    sessions = db.exec(
        select(AtChatSession).order_by(AtChatSession.started_at.desc()).limit(20)  # type: ignore[unresolved-attribute]
    ).all()
    result = []
    for s in sessions:
        assert s.id is not None
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
    db: Annotated[Session, Depends(get_session)],
):
    """Get a specific chat session with all messages."""
    session = db.get(AtChatSession, session_id)
    if not session:
        raise HTTPException(404, detail="Chat session not found")
    assert session.id is not None

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
