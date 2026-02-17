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

from ....services.databricks_agents import extract_agent_text, query_agent_endpoint
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
        assert session.id is not None
        self._save_user_message(db, session.id, user_message)

        # Build messages for the MAS endpoint
        history = self._get_message_history(db, session.id, limit=10)
        messages = [{"role": m["role"], "content": m["content"]} for m in history]

        try:
            result = query_agent_endpoint(ws, MAS_ENDPOINT_NAME, messages)
            content = extract_agent_text(result)
            sources = [{"type": "mas", "source": "AdTech Intelligence Agent"}]
        except Exception as e:
            logger.error(f"MAS endpoint error: {type(e).__name__}: {e}", exc_info=True)
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
        assert session.id is not None
        self._save_user_message(db, session.id, user_message)

        # Build messages for the KA endpoint
        history = self._get_message_history(db, session.id, limit=10)
        messages = [{"role": m["role"], "content": m["content"]} for m in history]

        try:
            result = query_agent_endpoint(ws, ISSUE_RESOLUTION_KA_ENDPOINT, messages)
            content = extract_agent_text(result)
            sources = [{"type": "knowledge_base", "source": "Issue Resolution Knowledge Base"}]
        except Exception as e:
            logger.error(f"KA endpoint error: {type(e).__name__}: {e}", exc_info=True)
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
            .order_by(AtChatMessage.created_at.asc())  # type: ignore[unresolved-attribute]
        ).all()
        # Return the last N messages
        recent = messages[-limit:] if len(messages) > limit else messages
        return [{"role": m.role, "content": m.content} for m in recent]
