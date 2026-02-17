"""Chat / Agent proxy endpoints for the ASM Cockpit.

Proxies user messages to the Multi-Agent Supervisor (MAS) serving endpoint.
"""
from typing import Optional

from fastapi import APIRouter, HTTPException, Query, Request
from sqlmodel import select

from ....dependencies import SessionDep
from ..models import (
    MacChatSession,
    MacChatMessage,
    MacChatRole,
    MacChatMessageIn,
    MacChatMessageOut,
    MacChatHistoryOut,
)
from ..services.chat_service import send_message

router = APIRouter(prefix="/chat", tags=["mac-chat"])


@router.post("/send", response_model=MacChatMessageOut, operation_id="mac_sendChatMessage")
def send_chat_message(
    body: MacChatMessageIn,
    session: SessionDep,
    request: Request,
    session_id: Optional[int] = Query(None),
):
    """Send a message to the Issue Resolution Agent and get a response."""
    # Get or create session
    if session_id:
        chat_session = session.get(MacChatSession, session_id)
        if not chat_session:
            raise HTTPException(status_code=404, detail="Chat session not found")
    else:
        chat_session = MacChatSession(session_type=body.session_type)
        session.add(chat_session)
        session.flush()

    # Save user message
    user_msg = MacChatMessage(
        session_id=chat_session.id,
        role=MacChatRole.user,
        content=body.message,
    )
    session.add(user_msg)
    session.flush()

    # Call MAS endpoint (or mock if not available)
    runtime = request.app.state.runtime
    response_content = send_message(runtime.ws, body.message)

    # Save assistant response
    assistant_msg = MacChatMessage(
        session_id=chat_session.id,
        role=MacChatRole.assistant,
        content=response_content,
    )
    session.add(assistant_msg)
    session.commit()
    session.refresh(assistant_msg)

    return assistant_msg


@router.get("/history/{session_id}", response_model=MacChatHistoryOut, operation_id="mac_getChatHistory")
def get_chat_history(session_id: int, session: SessionDep):
    """Get chat history for a session."""
    chat_session = session.get(MacChatSession, session_id)
    if not chat_session:
        raise HTTPException(status_code=404, detail="Chat session not found")

    messages = session.exec(
        select(MacChatMessage)
        .where(MacChatMessage.session_id == session_id)
        .order_by(MacChatMessage.created_at)  # type: ignore[invalid-argument-type]
    ).all()

    return MacChatHistoryOut(
        session_id=chat_session.id,  # type: ignore[invalid-argument-type]
        session_type=chat_session.session_type,
        started_at=chat_session.started_at,
        ended_at=chat_session.ended_at,
        messages=[MacChatMessageOut.model_validate(m) for m in messages],
    )
