"""Chat endpoints for HB Product Center.

Simplified to only expose the MAS streaming endpoint, which is backed by
a Databricks Multi-Agent Supervisor. Legacy session-based CRUD endpoints
were removed because chat sessions/messages are not persisted in Unity
Catalog tables — the MAS endpoint manages conversation state internally.
"""

from typing import Annotated

from databricks.sdk import WorkspaceClient
from fastapi import APIRouter, Depends, Request

from ....dependencies import RuntimeDep
from ....rate_limit import limiter
from ....services.streaming import create_chat_stream
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
    """Send a message to the Product Center Intelligence Agent (streaming).

    Uses the shared create_chat_stream helper so the SSE envelope,
    error handling, and [DONE] sentinel match every other chat endpoint
    in the app (D1 normalization).
    """
    stream = _chat_service.stream_response_uc(
        ws=ws,
        user_message=message.content,
        session_id=message.session_id,
    )
    return await create_chat_stream(
        stream,
        headers={"Cache-Control": "no-cache", "Connection": "keep-alive"},
    )
