"""Chat / AI assistant endpoints using Unity Catalog.

Provides two chat modes:
- /chat/sessions/... — Simple session-based chat
- /mas-chat          — Multi-Agent Supervisor style streaming chat backed by
                       a Databricks foundation model
"""

from typing import Annotated

from databricks.sdk import WorkspaceClient
from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import StreamingResponse

from ....dependencies import RuntimeDep
from ..models import (
    HbChatMessageIn,
    HbChatMessageOut,
    HbChatSessionCreate,
    HbChatSessionOut,
)
from ..services.chat_service import HbChatService
from ..services.uc_query_service import select_all, select_by_id, insert_row

router = APIRouter(prefix="/chat", tags=["hb-product-center"])

_chat_service = HbChatService()


def get_ws(runtime: RuntimeDep) -> WorkspaceClient:
    """Get WorkspaceClient from runtime (uses app SP identity)."""
    return runtime.ws


WsDep = Annotated[WorkspaceClient, Depends(get_ws)]


# ---- MAS-style streaming endpoint ----


@router.post("/mas-chat", operation_id="hb_sendMasChatMessage")
async def send_mas_chat_message(
    message: HbChatMessageIn,
    ws: WsDep,
):
    """Send a message to the Product Center Intelligence Agent (streaming)."""

    async def event_generator():
        async for chunk in _chat_service.stream_response_uc(
            ws=ws,
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
def create_chat_session(data: HbChatSessionCreate, ws: WsDep):
    """Create a new chat session.

    Note: Chat sessions are not persisted in UC tables - we return a mock session.
    The actual chat state is managed by the MAS endpoint.
    """
    from datetime import datetime, timezone
    from ..models import ChatContext, UserRole

    # Return a mock session since hb_chat_sessions table doesn't exist in UC
    user_role = UserRole(data.user_role) if data.user_role else None
    context = ChatContext(data.context)
    return HbChatSessionOut(
        id=1,
        user_role=user_role,
        context=context,
        created_at=datetime.now(timezone.utc),
    )


@router.get("/sessions/{session_id}/messages", response_model=list[HbChatMessageOut], operation_id="hb_getChatMessages")
def get_chat_messages(session_id: int, ws: WsDep):
    """Get chat messages for a session.

    Note: Messages are not persisted in UC - return empty list.
    Use the MAS chat endpoint for stateful conversations.
    """
    # Chat messages table doesn't exist in UC - return empty
    return []


@router.post("/sessions/{session_id}/messages", response_model=HbChatMessageOut, operation_id="hb_sendChatMessage")
def send_chat_message(session_id: int, data: HbChatMessageIn, ws: WsDep):
    """Send a chat message (legacy endpoint).

    Note: For full chat functionality, use the /mas-chat endpoint instead.
    """
    from datetime import datetime, timezone

    # Return a mock response since chat tables don't exist in UC
    return HbChatMessageOut(
        id=1,
        session_id=session_id,
        role="assistant",
        content="Please use the AI chat interface for full assistant functionality.",
        created_at=datetime.now(timezone.utc),
    )
