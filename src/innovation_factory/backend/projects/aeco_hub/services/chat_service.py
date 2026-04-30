"""Chat service for AECO Hub agents.

Routes chat messages either to:
- The Multi-Agent Supervisor (``MAS_ENDPOINT_NAME``) for general questions
  spanning project analytics, operations, and standards.
- The Standards & Compliance Knowledge Assistant
  (``STANDARDS_COMPLIANCE_KA_ENDPOINT``) for questions specifically scoped
  to IFC, COBie, building-regulation, or BAS-integration content.

Agent Bricks endpoints use the ``input`` field (not ``messages``) — see
``services/databricks_agents.query_agent_endpoint``.
"""
from __future__ import annotations

import json
import logging
from typing import AsyncIterator, Optional

from databricks.sdk import WorkspaceClient
from sqlmodel import Session, select

from ....services.databricks_agents import extract_agent_text, query_agent_endpoint
from ..databricks_config import (
    MAS_ENDPOINT_NAME,
    STANDARDS_COMPLIANCE_KA_ENDPOINT,
)
from ..models import (
    AecoChatRole,
    DtChatMessage,
    DtChatSession,
)

logger = logging.getLogger(__name__)


class ChatService:
    """AECO Hub chat orchestrator (MAS + KA)."""

    async def stream_mas_response(
        self,
        ws: WorkspaceClient,
        db: Session,
        user_message: str,
        session_id: Optional[int] = None,
        project_id: Optional[int] = None,
    ) -> AsyncIterator[str]:
        async for chunk in self._stream_endpoint_response(
            ws=ws,
            db=db,
            endpoint_name=MAS_ENDPOINT_NAME,
            agent_kind="mas",
            agent_label="AECO Hub Supervisor",
            user_message=user_message,
            session_id=session_id,
            project_id=project_id,
            unavailable_msg=(
                "I couldn't reach the AECO Hub Supervisor right now. The "
                "serving endpoint may be warming up — please try again in "
                "a moment."
            ),
        ):
            yield chunk

    async def stream_ka_response(
        self,
        ws: WorkspaceClient,
        db: Session,
        user_message: str,
        session_id: Optional[int] = None,
        project_id: Optional[int] = None,
    ) -> AsyncIterator[str]:
        async for chunk in self._stream_endpoint_response(
            ws=ws,
            db=db,
            endpoint_name=STANDARDS_COMPLIANCE_KA_ENDPOINT,
            agent_kind="ka",
            agent_label="AECO Standards & Compliance",
            user_message=user_message,
            session_id=session_id,
            project_id=project_id,
            unavailable_msg=(
                "The Standards & Compliance Knowledge Assistant is "
                "unavailable right now. The endpoint may still be "
                "indexing — please try again in a few minutes."
            ),
        ):
            yield chunk

    # -------------------------------------------------------------------
    # Internal helpers
    # -------------------------------------------------------------------

    async def _stream_endpoint_response(
        self,
        *,
        ws: WorkspaceClient,
        db: Session,
        endpoint_name: str,
        agent_kind: str,
        agent_label: str,
        user_message: str,
        session_id: Optional[int],
        project_id: Optional[int],
        unavailable_msg: str,
    ) -> AsyncIterator[str]:
        session = self._get_or_create_session(db, session_id, agent_kind, project_id)
        if session.id is None:
            raise RuntimeError("Chat session was created but has no ID")
        self._save_user_message(db, session.id, user_message)

        history = self._get_message_history(db, session.id, limit=10)
        messages = [{"role": m["role"], "content": m["content"]} for m in history]

        sources: list[dict]
        try:
            if not endpoint_name:
                raise RuntimeError(
                    f"{agent_kind.upper()} endpoint not configured "
                    f"(env var missing for {agent_label})"
                )
            result = query_agent_endpoint(ws, endpoint_name, messages)
            content = extract_agent_text(result)
            sources = [{"type": agent_kind, "source": agent_label}]
        except Exception as e:
            logger.error(
                f"{agent_label} endpoint error: {type(e).__name__}: {e}",
                exc_info=True,
            )
            content = unavailable_msg
            sources = [{"type": "error", "source": "System"}]

        self._save_assistant_message(db, session.id, content, sources)

        yield json.dumps({
            "session_id": session.id,
            "content": content,
            "sources": sources,
            "done": False,
        })
        yield json.dumps({"content": "", "done": True})

    def _get_or_create_session(
        self,
        db: Session,
        session_id: Optional[int],
        agent_kind: str,
        project_id: Optional[int],
    ) -> DtChatSession:
        if session_id is not None:
            session = db.get(DtChatSession, session_id)
            if session is not None:
                return session
        session = DtChatSession(agent_kind=agent_kind, project_id=project_id)
        db.add(session)
        db.commit()
        db.refresh(session)
        return session

    def _save_user_message(self, db: Session, session_id: int, content: str) -> None:
        db.add(DtChatMessage(
            session_id=session_id,
            role=AecoChatRole.user,
            content=content,
        ))
        db.commit()

    def _save_assistant_message(
        self,
        db: Session,
        session_id: int,
        content: str,
        sources: list[dict],
    ) -> None:
        db.add(DtChatMessage(
            session_id=session_id,
            role=AecoChatRole.assistant,
            content=content,
            sources_json={"sources": sources} if sources else None,
        ))
        db.commit()

    def _get_message_history(
        self,
        db: Session,
        session_id: int,
        limit: int = 10,
    ) -> list[dict]:
        stmt = (
            select(DtChatMessage)
            .where(DtChatMessage.session_id == session_id)
            .order_by(DtChatMessage.created_at.desc())  # type: ignore[unresolved-attribute]
            .limit(limit)
        )
        rows = list(db.exec(stmt).all())
        rows.reverse()
        return [{"role": m.role.value, "content": m.content} for m in rows]
