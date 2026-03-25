"""Shared SSE streaming utility for chat endpoints.

Provides a reusable event generator that:
- Streams chunks as SSE events
- Handles errors gracefully (emits error event instead of dropping connection)
- Calls a completion callback to persist the full response
- Sends a [DONE] sentinel when complete
"""

import json
import logging
from collections.abc import AsyncIterator, Callable
from typing import Any

from fastapi.responses import StreamingResponse

logger = logging.getLogger(__name__)


async def create_chat_stream(
    stream: AsyncIterator[str],
    on_complete: Callable[[str], Any] | None = None,
    on_error: Callable[[Exception], Any] | None = None,
    headers: dict[str, str] | None = None,
) -> StreamingResponse:
    """Create an SSE StreamingResponse from an async chunk stream.

    Args:
        stream: Async iterator yielding text chunks
        on_complete: Called with the full concatenated response on success.
                     If None, no post-stream action is taken.
        on_error: Optional callback on stream failure
        headers: Optional extra headers for the SSE response
                 (e.g. Cache-Control, Connection)
    """

    async def event_generator():
        full_response = ""
        try:
            async for chunk in stream:
                full_response += chunk
                yield f"data: {chunk}\n\n"
        except Exception as e:
            logger.error(f"Chat stream error: {e}")
            yield f"data: {json.dumps({'error': str(e)})}\n\n"
            if on_error:
                try:
                    on_error(e)
                except Exception:
                    pass
            return

        if on_complete:
            try:
                on_complete(full_response)
            except Exception as e:
                logger.error(f"Failed to persist chat response: {e}")

        yield "data: [DONE]\n\n"

    return StreamingResponse(
        event_generator(),
        media_type="text/event-stream",
        headers=headers,
    )
