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
        if session.id is None:
            raise RuntimeError("Chat session was created but has no ID")
        self._save_user_message(db, session.id, user_message)

        history = self._get_message_history(db, session.id, limit=10)
        messages = [{"role": "system", "content": SYSTEM_PROMPT}]
        messages.extend({"role": m["role"], "content": m["content"]} for m in history)

        try:
            result = ws.api_client.do(
                "POST",
                f"/serving-endpoints/{MAS_ENDPOINT_NAME}/invocations",
                body={"input": messages},
            )
            content, sources = self._extract_mas_response(result)
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

    def _extract_mas_response(self, response: Any) -> tuple[str, list[dict[str, str]]]:
        """Extract content and sources from a MAS supervisor response.

        Returns (content_text, sources) where content_text is the final
        assistant summary and sources lists which agents contributed.
        """
        if not isinstance(response, dict):
            return str(response), []

        resp: dict[str, Any] = response
        output = resp.get("output")

        # Plain string output
        if isinstance(output, str):
            return output, [{"type": "agent", "source": "HB Product Center Intelligence"}]

        # Standard chat completion fallback
        if output is None:
            choices = resp.get("choices", [])
            if choices:
                text = choices[0].get("message", {}).get("content", "")
                return text, [{"type": "agent", "source": "HB Product Center Intelligence"}]
            return str(response), []

        # MAS list-of-items format
        if not isinstance(output, list):
            return str(output), []

        parts: list[str] = []
        sources: list[dict[str, str]] = []
        seen_agents: set[str] = set()

        for item in output:
            item_type = item.get("type")

            if item_type == "function_call":
                agent_name = item.get("name", "")
                if agent_name and agent_name not in seen_agents:
                    seen_agents.add(agent_name)
                    label = agent_name.replace("agent-", "").replace("hb-", "").replace("-", " ").title()
                    sources.append({"type": "agent", "source": label})

            elif item_type == "message":
                content_blocks = item.get("content", [])
                for block in content_blocks:
                    text = block.get("text", "")
                    if not text:
                        continue
                    # Skip agent name tags like <name>...</name>
                    if text.startswith("<name>") and text.endswith("</name>"):
                        continue
                    parts.append(text)

        if not sources:
            sources.append({"type": "agent", "source": "HB Product Center Intelligence"})

        return "\n\n".join(parts), sources

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
            {"role": "user", "content": user_message},
        ]

        try:
            result = ws.api_client.do(
                "POST",
                f"/serving-endpoints/{MAS_ENDPOINT_NAME}/invocations",
                body={"input": messages},
            )
            content, sources = self._extract_mas_response(result)
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
