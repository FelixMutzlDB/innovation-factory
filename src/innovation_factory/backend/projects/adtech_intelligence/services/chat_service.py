"""Chat service for the AdTech Intelligence agents.

Routes chat messages to Databricks serving endpoints:
- MAS (Multi-Agent Supervisor) for the overview page
- KA (Knowledge Assistant) for issue resolution on the issues page

Agent Bricks endpoints use the ``input`` field (not ``messages``).
"""

import json
import logging
from typing import AsyncIterator, Optional

from databricks.sdk import WorkspaceClient
from sqlmodel import Session, select

from ..databricks_config import (
    ISSUE_RESOLUTION_KA_ENDPOINT,
    MAS_ENDPOINT_NAME,
)
from ..models import (
    AtChatMessage,
    AtChatRole,
    AtChatSession,
)

logger = logging.getLogger(__name__)


def _query_serving_endpoint(
    ws: WorkspaceClient,
    endpoint_name: str,
    messages: list[dict],
) -> str:
    """Call an Agent Bricks serving endpoint using the ``input`` field format."""
    try:
        payload = [
            {"role": m["role"], "content": m["content"]}
            for m in messages
        ]
        logger.info(f"Querying serving endpoint '{endpoint_name}' with {len(payload)} messages")
        result = ws.api_client.do(
            "POST",
            f"/serving-endpoints/{endpoint_name}/invocations",
            body={"input": payload},
        )
        logger.info(f"Received response from '{endpoint_name}'")
        return _extract_text(result)
    except Exception as e:
        logger.error(f"Serving endpoint '{endpoint_name}' error: {type(e).__name__}: {e}", exc_info=True)
        raise


def _extract_text(result: dict | list | str) -> str:
    """Extract plain text from an Agent Bricks response.

    Agent Bricks endpoints return varied structures:
    - {"output": [{"type":"message","content":[{"type":"output_text","text":"..."}]}]}
    - {"output": "plain string"}
    - {"choices": [{"message": {"content": "..."}}]}

    Internal items (function_call, function_call_output) are skipped.
    """
    if isinstance(result, str):
        return result

    if isinstance(result, dict):
        output = result.get("output")
        if output is not None:
            return _extract_text(output)
        choices = result.get("choices")
        if choices and isinstance(choices, list):
            msg = choices[0].get("message", {})
            return msg.get("content", "")
        content = result.get("content")
        if isinstance(content, list):
            texts = []
            for block in content:
                if isinstance(block, dict) and block.get("type") == "output_text":
                    texts.append(block.get("text", ""))
            return "\n".join(texts) if texts else str(result)
        if isinstance(content, str):
            return content
        text = result.get("text")
        if isinstance(text, str):
            return text
        return str(result)

    if isinstance(result, list):
        texts = []
        for item in result:
            if isinstance(item, dict):
                item_type = item.get("type", "")
                # Skip internal agent-to-agent messages
                if item_type in ("function_call", "function_call_output"):
                    continue
                if item_type == "message" and item.get("role") == "assistant":
                    texts.append(_extract_text(item))
                elif item_type == "output_text":
                    texts.append(item.get("text", ""))
                elif item_type == "message":
                    # Non-assistant messages (e.g. tool output) — skip
                    continue
                else:
                    texts.append(_extract_text(item))
            elif isinstance(item, str):
                texts.append(item)
        return "\n".join(texts) if texts else str(result)

    return str(result)


class ChatService:
    """Service for AI-powered chat via Databricks serving endpoints."""

    async def stream_mas_response(
        self,
        ws: WorkspaceClient,
        db: Session,
        user_message: str,
        session_id: Optional[int] = None,
    ) -> AsyncIterator[str]:
        """Stream a response from the Multi-Agent Supervisor."""
        session = self._get_or_create_session(db, session_id, "mas")
        self._save_user_message(db, session.id, user_message)

        # Build messages for the MAS endpoint
        history = self._get_message_history(db, session.id, limit=10)
        messages = [{"role": m["role"], "content": m["content"]} for m in history]

        try:
            content = _query_serving_endpoint(ws, MAS_ENDPOINT_NAME, messages)
            sources = [{"type": "mas", "source": "AdTech Intelligence Agent"}]
        except Exception:
            content = (
                "I'm sorry, I couldn't reach the AdTech Intelligence Agent right now. "
                "Please check that the serving endpoint is online and try again."
            )
            sources = [{"type": "error", "source": "System"}]

        self._save_assistant_message(db, session.id, content, sources)

        yield json.dumps({
            "session_id": session.id,
            "content": content,
            "sources": sources,
            "done": False,
        })
        yield json.dumps({"content": "", "done": True})

    async def stream_ka_response(
        self,
        ws: WorkspaceClient,
        db: Session,
        user_message: str,
        session_id: Optional[int] = None,
    ) -> AsyncIterator[str]:
        """Stream a response from the Issue Resolution Knowledge Assistant."""
        session = self._get_or_create_session(db, session_id, "issue_resolution")
        self._save_user_message(db, session.id, user_message)

        # Build messages for the KA endpoint
        history = self._get_message_history(db, session.id, limit=10)
        messages = [{"role": m["role"], "content": m["content"]} for m in history]

        try:
            content = _query_serving_endpoint(ws, ISSUE_RESOLUTION_KA_ENDPOINT, messages)
            sources = [{"type": "knowledge_base", "source": "Issue Resolution Knowledge Base"}]
        except Exception:
            content = (
                "I'm sorry, I couldn't reach the Issue Resolution Knowledge Base right now. "
                "Please check that the serving endpoint is online and try again."
            )
            sources = [{"type": "error", "source": "System"}]

        self._save_assistant_message(db, session.id, content, sources)

        yield json.dumps({
            "session_id": session.id,
            "content": content,
            "sources": sources,
            "done": False,
        })
        yield json.dumps({"content": "", "done": True})

    # ---- helpers ----

    def _get_or_create_session(
        self, db: Session, session_id: Optional[int], session_type: str
    ) -> AtChatSession:
        if session_id:
            session = db.get(AtChatSession, session_id)
            if session:
                return session
        session = AtChatSession(session_type=session_type)
        db.add(session)
        db.commit()
        db.refresh(session)
        return session

    def _save_user_message(self, db: Session, session_id: int, content: str) -> None:
        msg = AtChatMessage(session_id=session_id, role=AtChatRole.user, content=content)
        db.add(msg)
        db.commit()

    def _save_assistant_message(
        self, db: Session, session_id: int, content: str, sources: list[dict]
    ) -> None:
        msg = AtChatMessage(
            session_id=session_id,
            role=AtChatRole.assistant,
            content=content,
            sources=sources,
        )
        db.add(msg)
        db.commit()

    def _get_message_history(self, db: Session, session_id: int, limit: int = 10) -> list[dict]:
        messages = db.exec(
            select(AtChatMessage)
            .where(AtChatMessage.session_id == session_id)
            .order_by(AtChatMessage.created_at.asc())
        ).all()
        # Return the last N messages
        recent = messages[-limit:] if len(messages) > limit else messages
        return [{"role": m.role, "content": m.content} for m in recent]
