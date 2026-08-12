"""Unit tests for the AdTech Intelligence ChatService.

Tests the service directly (no HTTP layer) using mocked Databricks endpoints.
No live Databricks calls are made.

Covers:
- Session creation and reuse (_get_or_create_session)
- Message persistence helpers (_save_user_message, _save_assistant_message)
- Message history limiting (_get_message_history)
- stream_mas_response: mocked success path (yields correct JSON chunks)
- stream_mas_response: endpoint failure path (yields fallback message)
- stream_ka_response: mocked success path
- stream_ka_response: endpoint failure path
- Messages are persisted to DB after streaming
"""
from __future__ import annotations

import json
from unittest.mock import MagicMock, patch

import pytest

from innovation_factory.backend.projects.adtech_intelligence.services.chat_service import (
    ChatService,
)
from innovation_factory.backend.projects.adtech_intelligence.models import (
    AtChatMessage,
    AtChatRole,
    AtChatSession,
)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

_MAS_PATCH = (
    "innovation_factory.backend.projects.adtech_intelligence.services.chat_service"
    ".query_agent_endpoint"
)


def _mock_ws():
    """Return a minimal mock WorkspaceClient."""
    return MagicMock()


# ---------------------------------------------------------------------------
# Session creation and reuse
# ---------------------------------------------------------------------------


class TestGetOrCreateSession:
    def test_creates_new_session_when_no_id(self, session):
        svc = ChatService()
        s = svc._get_or_create_session(session, None, "issue_resolution")
        assert s.id is not None
        assert s.session_type == "issue_resolution"

    def test_creates_mas_session_with_correct_type(self, session):
        svc = ChatService()
        s = svc._get_or_create_session(session, None, "mas")
        assert s.session_type == "mas"

    def test_reuses_existing_session_by_id(self, session):
        existing = AtChatSession(session_type="issue_resolution")
        session.add(existing)
        session.commit()
        session.refresh(existing)

        svc = ChatService()
        fetched = svc._get_or_create_session(session, existing.id, "issue_resolution")
        assert fetched.id == existing.id

    def test_creates_new_when_id_not_found(self, session):
        svc = ChatService()
        s = svc._get_or_create_session(session, 99999, "issue_resolution")
        # 99999 doesn't exist — a new session should be created
        assert s.id is not None
        assert s.id != 99999


# ---------------------------------------------------------------------------
# Message persistence helpers
# ---------------------------------------------------------------------------


class TestMessagePersistence:
    def test_save_user_message_creates_record(self, session):
        chat_session = AtChatSession(session_type="issue_resolution")
        session.add(chat_session)
        session.commit()
        session.refresh(chat_session)
        assert chat_session.id is not None

        svc = ChatService()
        svc._save_user_message(session, chat_session.id, "Hello, what happened?")

        from sqlmodel import select

        msgs = session.exec(
            select(AtChatMessage).where(AtChatMessage.session_id == chat_session.id)
        ).all()
        assert len(msgs) == 1
        assert msgs[0].role == AtChatRole.user
        assert msgs[0].content == "Hello, what happened?"

    def test_save_assistant_message_stores_sources(self, session):
        chat_session = AtChatSession(session_type="issue_resolution")
        session.add(chat_session)
        session.commit()
        session.refresh(chat_session)
        assert chat_session.id is not None

        svc = ChatService()
        sources = [{"type": "knowledge_base", "source": "Runbook #12"}]
        svc._save_assistant_message(session, chat_session.id, "Fix your pipeline.", sources)

        from sqlmodel import select

        msgs = session.exec(
            select(AtChatMessage).where(AtChatMessage.session_id == chat_session.id)
        ).all()
        assert len(msgs) == 1
        assert msgs[0].role == AtChatRole.assistant
        assert msgs[0].sources == sources


# ---------------------------------------------------------------------------
# Message history limit
# ---------------------------------------------------------------------------


class TestMessageHistoryLimit:
    def test_history_returns_all_when_under_limit(self, session):
        chat_session = AtChatSession(session_type="mas")
        session.add(chat_session)
        session.commit()
        session.refresh(chat_session)
        assert chat_session.id is not None

        svc = ChatService()
        for i in range(3):
            svc._save_user_message(session, chat_session.id, f"msg {i}")

        history = svc._get_message_history(session, chat_session.id, limit=10)
        assert len(history) == 3

    def test_history_truncates_to_limit(self, session):
        chat_session = AtChatSession(session_type="mas")
        session.add(chat_session)
        session.commit()
        session.refresh(chat_session)
        assert chat_session.id is not None

        svc = ChatService()
        for i in range(15):
            svc._save_user_message(session, chat_session.id, f"msg {i}")

        history = svc._get_message_history(session, chat_session.id, limit=10)
        assert len(history) == 10

    def test_history_returns_most_recent_messages(self, session):
        """When truncated to limit, the LAST N messages are returned (recency window)."""
        chat_session = AtChatSession(session_type="mas")
        session.add(chat_session)
        session.commit()
        session.refresh(chat_session)
        assert chat_session.id is not None

        svc = ChatService()
        for i in range(5):
            svc._save_user_message(session, chat_session.id, f"early msg {i}")
        svc._save_user_message(session, chat_session.id, "recent final message")

        history = svc._get_message_history(session, chat_session.id, limit=3)
        # The last message must be in the window
        contents = [h["content"] for h in history]
        assert "recent final message" in contents


# ---------------------------------------------------------------------------
# stream_mas_response — mocked Databricks endpoint
# ---------------------------------------------------------------------------


class TestStreamMasResponse:
    async def test_success_path_yields_two_chunks(self, session):
        """On a successful endpoint call, the generator yields exactly 2 JSON chunks:
        one with content + done=False, one with done=True."""
        mock_ws = _mock_ws()
        mock_response = {"choices": [{"message": {"content": "Campaign analysis complete."}}]}

        with patch(_MAS_PATCH, return_value=mock_response):
            svc = ChatService()
            chunks = []
            async for chunk in svc.stream_mas_response(
                mock_ws, session, "Analyse my campaigns"
            ):
                chunks.append(chunk)

        assert len(chunks) == 2

    async def test_success_path_first_chunk_has_content(self, session):
        mock_ws = _mock_ws()
        mock_response = {"choices": [{"message": {"content": "All campaigns are healthy."}}]}

        with patch(_MAS_PATCH, return_value=mock_response):
            svc = ChatService()
            chunks = []
            async for chunk in svc.stream_mas_response(
                mock_ws, session, "Health check"
            ):
                chunks.append(chunk)

        first = json.loads(chunks[0])
        assert "content" in first
        assert "All campaigns are healthy." in first["content"]
        assert first["done"] is False
        assert "session_id" in first
        assert first["session_id"] is not None

    async def test_success_path_second_chunk_is_done_sentinel(self, session):
        mock_ws = _mock_ws()
        mock_response = {"choices": [{"message": {"content": "OK"}}]}

        with patch(_MAS_PATCH, return_value=mock_response):
            svc = ChatService()
            chunks = []
            async for chunk in svc.stream_mas_response(
                mock_ws, session, "ping"
            ):
                chunks.append(chunk)

        second = json.loads(chunks[1])
        assert second["done"] is True
        assert second.get("content") == ""

    async def test_endpoint_error_yields_fallback_message(self, session):
        """When the endpoint raises, the service must yield a user-friendly fallback
        (not propagate the exception)."""
        mock_ws = _mock_ws()

        with patch(_MAS_PATCH, side_effect=RuntimeError("endpoint offline")):
            svc = ChatService()
            chunks = []
            async for chunk in svc.stream_mas_response(
                mock_ws, session, "analyse campaigns"
            ):
                chunks.append(chunk)

        assert len(chunks) == 2
        first = json.loads(chunks[0])
        # Fallback message should mention the agent being unreachable
        assert "couldn't reach" in first["content"].lower() or "sorry" in first["content"].lower()
        assert first["done"] is False

    async def test_endpoint_error_sources_type_is_error(self, session):
        mock_ws = _mock_ws()

        with patch(_MAS_PATCH, side_effect=ConnectionError("timeout")):
            svc = ChatService()
            chunks = []
            async for chunk in svc.stream_mas_response(mock_ws, session, "test"):
                chunks.append(chunk)

        first = json.loads(chunks[0])
        sources = first.get("sources", [])
        assert any(s.get("type") == "error" for s in sources)

    async def test_messages_persisted_after_success(self, session):
        """After streaming completes, both the user message and assistant response
        must be in the database."""
        from sqlmodel import select

        mock_ws = _mock_ws()
        mock_response = {"choices": [{"message": {"content": "Report ready."}}]}

        chat_session_before = list(session.exec(select(AtChatSession)).all())
        n_sessions_before = len(chat_session_before)

        with patch(_MAS_PATCH, return_value=mock_response):
            svc = ChatService()
            async for _ in svc.stream_mas_response(
                mock_ws, session, "Generate performance report"
            ):
                pass

        # A new session was created
        all_sessions = session.exec(select(AtChatSession)).all()
        assert len(all_sessions) == n_sessions_before + 1
        new_session = all_sessions[-1]

        # Both user and assistant messages were saved
        msgs = session.exec(
            select(AtChatMessage)
            .where(AtChatMessage.session_id == new_session.id)
        ).all()
        roles = {m.role for m in msgs}
        assert AtChatRole.user in roles
        assert AtChatRole.assistant in roles

    async def test_user_message_content_saved(self, session):
        mock_ws = _mock_ws()
        mock_response = {"choices": [{"message": {"content": "Got it."}}]}

        with patch(_MAS_PATCH, return_value=mock_response):
            svc = ChatService()
            chat_session = svc._get_or_create_session(session, None, "mas")
            async for _ in svc.stream_mas_response(
                mock_ws, session, "unique-test-query-xyz", session_id=chat_session.id
            ):
                pass

        from sqlmodel import select

        msgs = session.exec(
            select(AtChatMessage)
            .where(AtChatMessage.session_id == chat_session.id)
            .where(AtChatMessage.role == AtChatRole.user)
        ).all()
        assert any("unique-test-query-xyz" in m.content for m in msgs)


# ---------------------------------------------------------------------------
# stream_ka_response — mocked Databricks endpoint
# ---------------------------------------------------------------------------


class TestStreamKaResponse:
    async def test_success_path_yields_two_chunks(self, session):
        mock_ws = _mock_ws()
        mock_response = {
            "output": [
                {
                    "type": "message",
                    "role": "assistant",
                    "content": [{"type": "output_text", "text": "Here is the resolution runbook."}],
                }
            ]
        }

        with patch(_MAS_PATCH, return_value=mock_response):
            svc = ChatService()
            chunks = []
            async for chunk in svc.stream_ka_response(
                mock_ws, session, "How do I fix a delivery issue?"
            ):
                chunks.append(chunk)

        assert len(chunks) == 2
        first = json.loads(chunks[0])
        assert "Here is the resolution runbook." in first["content"]
        assert first["done"] is False

    async def test_sources_type_is_knowledge_base_on_success(self, session):
        mock_ws = _mock_ws()
        mock_response = {"choices": [{"message": {"content": "Check the runbook."}}]}

        with patch(_MAS_PATCH, return_value=mock_response):
            svc = ChatService()
            chunks = []
            async for chunk in svc.stream_ka_response(mock_ws, session, "question"):
                chunks.append(chunk)

        first = json.loads(chunks[0])
        sources = first.get("sources", [])
        assert any(s.get("type") == "knowledge_base" for s in sources)

    async def test_endpoint_error_yields_fallback(self, session):
        mock_ws = _mock_ws()

        with patch(_MAS_PATCH, side_effect=ValueError("KA endpoint not found")):
            svc = ChatService()
            chunks = []
            async for chunk in svc.stream_ka_response(mock_ws, session, "any question"):
                chunks.append(chunk)

        assert len(chunks) == 2
        first = json.loads(chunks[0])
        assert first["done"] is False
        # Fallback sources should signal error
        sources = first.get("sources", [])
        assert any(s.get("type") == "error" for s in sources)

    async def test_session_id_returned_in_first_chunk(self, session):
        mock_ws = _mock_ws()
        mock_response = {"choices": [{"message": {"content": "Sure."}}]}

        with patch(_MAS_PATCH, return_value=mock_response):
            svc = ChatService()
            chunks = []
            async for chunk in svc.stream_ka_response(mock_ws, session, "test"):
                chunks.append(chunk)

        first = json.loads(chunks[0])
        assert isinstance(first.get("session_id"), int)
        assert first["session_id"] > 0

    async def test_reuses_provided_session_id(self, session):
        """When session_id is provided and exists, the response must carry the same session_id."""
        existing = AtChatSession(session_type="issue_resolution")
        session.add(existing)
        session.commit()
        session.refresh(existing)

        mock_ws = _mock_ws()
        mock_response = {"choices": [{"message": {"content": "Acknowledged."}}]}

        with patch(_MAS_PATCH, return_value=mock_response):
            svc = ChatService()
            chunks = []
            async for chunk in svc.stream_ka_response(
                mock_ws, session, "follow-up", session_id=existing.id
            ):
                chunks.append(chunk)

        first = json.loads(chunks[0])
        assert first["session_id"] == existing.id


# ---------------------------------------------------------------------------
# Chat sessions list endpoint
# ---------------------------------------------------------------------------


class TestChatSessionsEndpoint:
    def test_endpoint_exists_and_is_routed(self, client):
        """Regression (fixed): GET /chat/sessions returns 200 even when messages
        exist. chat.py previously passed a SQLModel instance to
        AtChatMessageOut.model_validate() → 500; fixed via m.model_dump()."""
        resp = client.get("/api/projects/adtech-intelligence/chat/sessions")
        assert resp.status_code == 200
        assert isinstance(resp.json(), list)

    def test_get_nonexistent_session_returns_404(self, client):
        resp = client.get("/api/projects/adtech-intelligence/chat/sessions/999999")
        assert resp.status_code == 404

    def test_created_session_retrievable(self, session, client):
        chat_session = AtChatSession(session_type="issue_resolution")
        session.add(chat_session)
        session.commit()
        session.refresh(chat_session)

        resp = client.get(
            f"/api/projects/adtech-intelligence/chat/sessions/{chat_session.id}"
        )
        assert resp.status_code == 200
        data = resp.json()
        assert data["session_id"] == chat_session.id
        assert data["session_type"] == "issue_resolution"
        assert data["messages"] == []

    def test_session_with_messages_returns_correct_session_id(self, session, client):
        """Regression (fixed): /chat/sessions/{id} returns 200 with its messages.
        The endpoint calls AtChatMessageOut.model_validate(m) on a SQLModel
        AtChatMessage instance, which Pydantic v2 rejected → 500; fixed via
        m.model_dump(). This exercises the non-empty message path directly."""
        chat_session = AtChatSession(session_type="mas")
        session.add(chat_session)
        session.commit()
        session.refresh(chat_session)
        session_id = chat_session.id

        session.add(
            AtChatMessage(session_id=session_id, role=AtChatRole.user, content="Hello")
        )
        session.commit()

        resp = client.get(
            f"/api/projects/adtech-intelligence/chat/sessions/{session_id}"
        )
        assert resp.status_code == 200
        data = resp.json()
        assert data["session_id"] == session_id
        assert len(data["messages"]) == 1
        assert data["messages"][0]["content"] == "Hello"
        assert data["messages"][0]["role"] == "user"
