"""Chat service for the HB Product Center agent.

Routes chat messages to a Databricks foundation model that orchestrates
between Genie spaces (supply chain, quality/auth) and the product
identification UC function.
"""

import json
import logging
from typing import Any, AsyncIterator, Optional

from databricks.sdk import WorkspaceClient
from sqlmodel import Session, select

from ..databricks_config import MAS_ENDPOINT_NAME
from ..models import HbChatMessage, HbChatSession

logger = logging.getLogger(__name__)

SYSTEM_PROMPT = """You are the Hugo Boss Product Center Intelligence Assistant.
You help employees and partners gain insights into products, supply chain,
quality control, and authenticity verification.

When asked about supply chain, logistics, sustainability, carbon footprint,
manufacturing partners, or product journeys, provide relevant analysis.

When asked about quality inspections, defects, quality scores, or
manufacturing partner quality, provide relevant insights.

When asked about authenticity verification, counterfeit detection, or
brand protection, provide relevant information.

When asked to identify a product from a description or image,
help match it against the Hugo Boss product catalog.

Always be professional, concise, and helpful. Use data-driven language."""


class HbChatService:
    """Service for AI-powered chat via Databricks serving endpoints."""

    async def stream_response(
        self,
        ws: WorkspaceClient,
        db: Session,
        user_message: str,
        session_id: Optional[int] = None,
    ) -> AsyncIterator[str]:
        """Stream a response from the agent endpoint."""
        session = self._get_or_create_session(db, session_id)
        assert session.id is not None
        self._save_user_message(db, session.id, user_message)

        history = self._get_message_history(db, session.id, limit=10)
        messages = [{"role": "system", "content": SYSTEM_PROMPT}]
        messages.extend({"role": m["role"], "content": m["content"]} for m in history)

        try:
            result = ws.api_client.do(
                "POST",
                f"/serving-endpoints/{MAS_ENDPOINT_NAME}/invocations",
                body={"messages": messages, "max_tokens": 1024},
            )
            content = self._extract_text(result)
            sources = [{"type": "agent", "source": "HB Product Center Intelligence"}]
        except Exception as e:
            logger.error(f"Agent endpoint error: {type(e).__name__}: {e}", exc_info=True)
            content = (
                "I'm sorry, I couldn't reach the Product Center Intelligence Agent right now. "
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

    def _extract_text(self, response: Any) -> str:
        if isinstance(response, dict):
            resp: dict[str, Any] = response
            choices = resp.get("choices", [])
            if choices:
                return choices[0].get("message", {}).get("content", "")
            output = resp.get("output")
            if isinstance(output, str):
                return output
        return str(response)

    def _get_or_create_session(self, db: Session, session_id: Optional[int]) -> HbChatSession:
        if session_id:
            session = db.get(HbChatSession, session_id)
            if session:
                return session
        session = HbChatSession(context="general")
        db.add(session)
        db.commit()
        db.refresh(session)
        return session

    def _save_user_message(self, db: Session, session_id: int, content: str) -> None:
        msg = HbChatMessage(session_id=session_id, role="user", content=content)
        db.add(msg)
        db.commit()

    def _save_assistant_message(
        self, db: Session, session_id: int, content: str, sources: list[dict]
    ) -> None:
        msg = HbChatMessage(session_id=session_id, role="assistant", content=content)
        db.add(msg)
        db.commit()

    def _get_message_history(self, db: Session, session_id: int, limit: int = 10) -> list[dict]:
        messages = db.exec(
            select(HbChatMessage)
            .where(HbChatMessage.session_id == session_id)
            .order_by(HbChatMessage.created_at.asc())  # type: ignore[union-attr]
        ).all()
        recent = messages[-limit:] if len(messages) > limit else messages
        return [{"role": m.role, "content": m.content} for m in recent]

    async def stream_response_uc(
        self,
        ws: WorkspaceClient,
        user_message: str,
        session_id: Optional[int] = None,
    ) -> AsyncIterator[str]:
        """Stream a response from the agent endpoint without database persistence.

        This version doesn't store chat history in the database, making it
        compatible with Unity Catalog-only deployments.
        """
        messages = [
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": user_message},
        ]

        try:
            result = ws.api_client.do(
                "POST",
                f"/serving-endpoints/{MAS_ENDPOINT_NAME}/invocations",
                body={"messages": messages, "max_tokens": 1024},
            )
            content = self._extract_text(result)
            sources = [{"type": "agent", "source": "HB Product Center Intelligence"}]
        except Exception as e:
            logger.error(f"Agent endpoint error: {type(e).__name__}: {e}", exc_info=True)
            content = (
                "I'm sorry, I couldn't reach the Product Center Intelligence Agent right now. "
                "Please check that the serving endpoint is online and try again."
            )
            sources = [{"type": "error", "source": "System"}]

        yield json.dumps({
            "session_id": session_id or 1,
            "content": content,
            "sources": sources,
            "done": False,
        })
        yield json.dumps({"content": "", "done": True})
