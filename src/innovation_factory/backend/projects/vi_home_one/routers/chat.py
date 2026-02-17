"""API router for chat with streaming support."""
from fastapi import APIRouter, HTTPException
from fastapi.responses import StreamingResponse
from sqlmodel import select

from ....dependencies import SessionDep
from ..models import (
    VhTicket,
    VhChatSession,
    VhChatMessage,
    VhChatRole,
    VhChatMessageIn,
    VhChatMessageOut,
    VhChatHistoryOut,
)
from ..services.chat_service import ChatService

router = APIRouter(prefix="/chat", tags=["vh-chat"])

chat_service = ChatService()


@router.post("/tickets/{ticket_id}/chat", operation_id="vh_send_chat_message")
async def send_chat_message(ticket_id: int, message: VhChatMessageIn, db: SessionDep):
    """Send a chat message and get streaming AI response."""
    ticket = db.get(VhTicket, ticket_id)
    if not ticket:
        raise HTTPException(status_code=404, detail="Ticket not found")

    session_query = select(VhChatSession).where(
        VhChatSession.ticket_id == ticket_id,
        VhChatSession.ended_at.is_(None)  # type: ignore[unresolved-attribute]
    )
    chat_session = db.exec(session_query).first()

    if not chat_session:
        chat_session = VhChatSession(ticket_id=ticket_id, session_type="support")
        db.add(chat_session)
        db.commit()
        db.refresh(chat_session)

    user_msg = VhChatMessage(
        session_id=chat_session.id,
        role=VhChatRole.user,
        content=message.content,
    )
    db.add(user_msg)
    db.commit()

    async def event_generator():
        full_response = ""
        async for chunk in chat_service.stream_chat_response(ticket_id, message.content, db):
            full_response += chunk
            yield f"data: {chunk}\n\n"

        assistant_msg = VhChatMessage(
            session_id=chat_session.id,
            role=VhChatRole.assistant,
            content=full_response,
            sources="Knowledge Base",
        )
        db.add(assistant_msg)
        db.commit()

        yield "data: [DONE]\n\n"

    return StreamingResponse(event_generator(), media_type="text/event-stream")


@router.get("/tickets/{ticket_id}/history", response_model=VhChatHistoryOut, operation_id="vh_get_chat_history")
def get_chat_history(ticket_id: int, db: SessionDep):
    """Get chat history for a ticket."""
    ticket = db.get(VhTicket, ticket_id)
    if not ticket:
        raise HTTPException(status_code=404, detail="Ticket not found")

    session_query = select(VhChatSession).where(VhChatSession.ticket_id == ticket_id)
    chat_session = db.exec(session_query).first()

    if not chat_session:
        return VhChatHistoryOut(session_id=0, messages=[])

    messages_query = select(VhChatMessage).where(
        VhChatMessage.session_id == chat_session.id
    ).order_by(VhChatMessage.created_at)  # type: ignore[invalid-argument-type]
    messages = db.exec(messages_query).all()

    message_outs = [
        VhChatMessageOut(
            id=msg.id,  # type: ignore[invalid-argument-type]
            role=msg.role, content=msg.content,
            sources=msg.sources, created_at=msg.created_at,
        )
        for msg in messages
    ]

    return VhChatHistoryOut(session_id=chat_session.id, messages=message_outs)  # type: ignore[invalid-argument-type]
