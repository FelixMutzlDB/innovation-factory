"""Chat endpoints for HB Product Center.

Simplified to only expose the MAS streaming endpoint, which is backed by
a Databricks Multi-Agent Supervisor. Legacy session-based CRUD endpoints
were removed because chat sessions/messages are not persisted in Unity
Catalog tables — the MAS endpoint manages conversation state internally.
"""

from typing import Annotated

from databricks.sdk import WorkspaceClient
from fastapi import APIRouter, Depends, Request
from fastapi.responses import StreamingResponse

from ....dependencies import RuntimeDep
from ....rate_limit import limiter
from ..models import HbChatMessageIn
from ..services.chat_service import HbChatService

router = APIRouter(prefix="/chat", tags=["hb-product-center"])

_chat_service = HbChatService()


def get_ws(runtime: RuntimeDep) -> WorkspaceClient:
    """Get WorkspaceClient from runtime (uses app SP identity)."""
    return runtime.ws


WsDep = Annotated[WorkspaceClient, Depends(get_ws)]


@router.post("/mas-chat", operation_id="hb_sendMasChatMessage")
@limiter.limit("30/minute")
async def send_mas_chat_message(
    request: Request,
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
