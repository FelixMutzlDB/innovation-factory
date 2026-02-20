"""Chat / AI assistant endpoints.

Provides two chat modes:
- /chat/sessions/... — Simple session-based chat (legacy)
- /mas-chat          — Multi-Agent Supervisor style streaming chat backed by
                       a Databricks foundation model
"""

from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import StreamingResponse
from sqlmodel import Session, select

from ....dependencies import SessionDep, get_session, get_runtime
from ....runtime import Runtime
from ..models import (
    HbChatMessage,
    HbChatMessageIn,
    HbChatMessageOut,
    HbChatSession,
    HbChatSessionCreate,
    HbChatSessionOut,
)
from ..services.chat_service import HbChatService

router = APIRouter(prefix="/chat", tags=["hb-product-center"])

_chat_service = HbChatService()


# ---- MAS-style streaming endpoint ----


@router.post("/mas-chat", operation_id="hb_sendMasChatMessage")
async def send_mas_chat_message(
    message: HbChatMessageIn,
    db: Annotated[Session, Depends(get_session)],
    runtime: Annotated[Runtime, Depends(get_runtime)],
):
    """Send a message to the Product Center Intelligence Agent (streaming)."""

    async def event_generator():
        async for chunk in _chat_service.stream_response(
            ws=runtime.ws,
            db=db,
            user_message=message.content,
            session_id=message.session_id,
        ):
            yield f"data: {chunk}\n\n"

    return StreamingResponse(
        event_generator(),
        media_type="text/event-stream",
        headers={"Cache-Control": "no-cache", "Connection": "keep-alive"},
    )


# ---- Legacy session-based endpoints ----


@router.post("/sessions", response_model=HbChatSessionOut, operation_id="hb_createChatSession")
def create_chat_session(data: HbChatSessionCreate, session: SessionDep):
    chat_session = HbChatSession(**data.model_dump())
    session.add(chat_session)
    session.commit()
    session.refresh(chat_session)
    return chat_session


@router.get("/sessions/{session_id}/messages", response_model=list[HbChatMessageOut], operation_id="hb_getChatMessages")
def get_chat_messages(session_id: int, session: SessionDep):
    chat_session = session.get(HbChatSession, session_id)
    if not chat_session:
        raise HTTPException(status_code=404, detail="Chat session not found")
    stmt = select(HbChatMessage).where(HbChatMessage.session_id == session_id).order_by(HbChatMessage.created_at.asc())  # type: ignore[union-attr]
    return list(session.exec(stmt).all())


@router.post("/sessions/{session_id}/messages", response_model=HbChatMessageOut, operation_id="hb_sendChatMessage")
def send_chat_message(session_id: int, data: HbChatMessageIn, session: SessionDep):
    chat_session = session.get(HbChatSession, session_id)
    if not chat_session:
        raise HTTPException(status_code=404, detail="Chat session not found")

    user_msg = HbChatMessage(session_id=session_id, role="user", content=data.content)
    session.add(user_msg)
    session.flush()

    assistant_msg = HbChatMessage(session_id=session_id, role="assistant", content="Processing your request...")
    session.add(assistant_msg)
    session.commit()
    session.refresh(assistant_msg)
    return assistant_msg
