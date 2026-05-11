"""Chat router for BSH Home Connect."""
from datetime import datetime, timezone
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Request
from sqlmodel import Session, select
from databricks.sdk import WorkspaceClient

from ....dependencies import SessionDep, get_obo_ws, get_session
from ....rate_limit import limiter
from ....services.streaming import create_chat_stream, streaming_endpoint
from ..models import (
    BshTicket,
    BshChatMessageIn,
    BshChatMessageOut,
    BshChatHistoryOut,
    BshCustomer,
)
from ..services.chat_service import ChatService

router = APIRouter(tags=["bsh-chat"])

chat_service = ChatService()


@router.post("/tickets/{ticket_id}/chat", operation_id="bsh_sendChatMessage")
@limiter.limit("30/minute")
@streaming_endpoint
async def send_chat_message(
    request: Request,
    ticket_id: int,
    message: BshChatMessageIn,
    obo_ws: Annotated[WorkspaceClient, Depends(get_obo_ws)],
    db: SessionDep,
):
    """Send a message and get streaming AI response."""
    databricks_user = obo_ws.current_user.me()
    ticket = db.get(BshTicket, ticket_id)
    if not ticket:
        raise HTTPException(status_code=404, detail="Ticket not found")

    # Determine session type based on user role
    customer_statement = select(BshCustomer).where(BshCustomer.databricks_user_id == databricks_user.id)
    customer = db.exec(customer_statement).first()
    session_type = "customer_support" if customer and ticket.customer_id == customer.id else "technician_assist"

    stream = chat_service.stream_chat_response(
        db=db, ticket_id=ticket_id,
        user_message=message.message, session_type=session_type,
    )
    return await create_chat_stream(
        stream,
        headers={"Cache-Control": "no-cache", "Connection": "keep-alive"},
    )


@router.get("/tickets/{ticket_id}/chat/history", response_model=BshChatHistoryOut, operation_id="bsh_getChatHistory")
def get_chat_history(
    ticket_id: int,
    obo_ws: Annotated[WorkspaceClient, Depends(get_obo_ws)],
    db: SessionDep,
    session_type: str = "customer_support",
):
    """Get chat history for a ticket."""
    ticket = db.get(BshTicket, ticket_id)
    if not ticket:
        raise HTTPException(status_code=404, detail="Ticket not found")

    messages = chat_service.get_chat_history(db, ticket_id, session_type)
    session_id = messages[-1].session_id if messages else 0

    return BshChatHistoryOut(
        session_id=session_id,
        ticket_id=ticket_id,
        session_type=session_type,
        started_at=messages[0].created_at if messages else datetime.now(timezone.utc),
        messages=[BshChatMessageOut.model_validate(msg) for msg in messages],
    )
