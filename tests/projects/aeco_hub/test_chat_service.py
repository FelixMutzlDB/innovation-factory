"""Unit tests for AECO Hub ChatService.

Tests the service layer in isolation — no live Databricks connection.
``query_agent_endpoint`` and ``extract_agent_text`` are patched out;
the session fixture provides an in-memory SQLite DB.

Covers:
- Session get-or-create logic (new, existing, stale ID → new).
- User/assistant message persistence.
- Message history retrieval (chronological order, limit cap).
- MAS + KA streaming with mocked agent (success path).
- Unavailable-endpoint fallback (empty endpoint name).
"""
from __future__ import annotations

import json
from datetime import datetime, timezone
from unittest.mock import MagicMock, patch

import pytest
from sqlmodel import select

from innovation_factory.backend.projects.aeco_hub.models import (
    AecoChatRole,
    DtChatMessage,
    DtChatSession,
)
from innovation_factory.backend.projects.aeco_hub.services.chat_service import ChatService


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _make_service() -> ChatService:
    return ChatService()


def _fake_ws() -> MagicMock:
    """Return a minimal mock WorkspaceClient (never actually called in unit tests)."""
    return MagicMock()


# ---------------------------------------------------------------------------
# Session management
# ---------------------------------------------------------------------------


class TestGetOrCreateSession:
    def test_creates_new_session_when_no_session_id(self, session):
        svc = _make_service()
        chat_session = svc._get_or_create_session(session, None, "mas", None)
        assert chat_session.id is not None
        assert chat_session.agent_kind == "mas"
        assert chat_session.project_id is None

    def test_creates_new_session_with_project_id(self, session):
        """project_id is optional (FK); None is valid."""
        svc = _make_service()
        chat_session = svc._get_or_create_session(session, None, "ka", project_id=None)
        assert chat_session.project_id is None
        assert chat_session.agent_kind == "ka"

    def test_returns_existing_session_when_found(self, session):
        existing = DtChatSession(agent_kind="mas", project_id=None)
        session.add(existing)
        session.commit()
        session.refresh(existing)

        svc = _make_service()
        retrieved = svc._get_or_create_session(session, existing.id, "mas", 1)
        assert retrieved.id == existing.id

    def test_creates_new_session_when_stale_id_not_found(self, session):
        svc = _make_service()
        # ID 99999 does not exist — should silently create a fresh session
        new_session = svc._get_or_create_session(session, 99999, "mas", None)
        assert new_session.id is not None
        assert new_session.id != 99999

    def test_different_agent_kinds_stored_independently(self, session):
        svc = _make_service()
        mas_session = svc._get_or_create_session(session, None, "mas", None)
        ka_session = svc._get_or_create_session(session, None, "ka", None)
        assert mas_session.id != ka_session.id
        assert mas_session.agent_kind == "mas"
        assert ka_session.agent_kind == "ka"


# ---------------------------------------------------------------------------
# Message persistence
# ---------------------------------------------------------------------------


class TestSaveMessages:
    def test_save_user_message_persists_with_user_role(self, session):
        chat_session = DtChatSession(agent_kind="mas")
        session.add(chat_session)
        session.commit()
        session.refresh(chat_session)
        assert chat_session.id is not None

        svc = _make_service()
        svc._save_user_message(session, chat_session.id, "What is the energy consumption?")

        msgs = list(session.exec(
            select(DtChatMessage).where(DtChatMessage.session_id == chat_session.id)
        ).all())
        assert len(msgs) == 1
        assert msgs[0].role == AecoChatRole.user
        assert "energy consumption" in msgs[0].content

    def test_save_assistant_message_persists_with_sources(self, session):
        chat_session = DtChatSession(agent_kind="ka")
        session.add(chat_session)
        session.commit()
        session.refresh(chat_session)
        assert chat_session.id is not None

        svc = _make_service()
        sources = [{"type": "ka", "source": "AECO Standards & Compliance"}]
        svc._save_assistant_message(session, chat_session.id, "IFC is a standard.", sources)

        msgs = list(session.exec(
            select(DtChatMessage).where(DtChatMessage.session_id == chat_session.id)
        ).all())
        assert len(msgs) == 1
        assert msgs[0].role == AecoChatRole.assistant
        assert msgs[0].sources_json == {"sources": sources}

    def test_save_assistant_message_no_sources_stores_none(self, session):
        chat_session = DtChatSession(agent_kind="mas")
        session.add(chat_session)
        session.commit()
        session.refresh(chat_session)
        assert chat_session.id is not None

        svc = _make_service()
        svc._save_assistant_message(session, chat_session.id, "No sources.", [])

        msg = session.exec(
            select(DtChatMessage).where(DtChatMessage.session_id == chat_session.id)
        ).first()
        assert msg is not None
        # Empty sources list → no sources_json stored
        assert msg.sources_json is None

    def test_save_user_and_assistant_messages_in_sequence(self, session):
        chat_session = DtChatSession(agent_kind="mas")
        session.add(chat_session)
        session.commit()
        session.refresh(chat_session)
        assert chat_session.id is not None

        svc = _make_service()
        svc._save_user_message(session, chat_session.id, "Hello")
        svc._save_assistant_message(session, chat_session.id, "Hi there!", [])

        msgs = list(session.exec(
            select(DtChatMessage)
            .where(DtChatMessage.session_id == chat_session.id)
            .order_by(DtChatMessage.id)  # type: ignore[invalid-argument-type]
        ).all())
        assert len(msgs) == 2
        assert msgs[0].role == AecoChatRole.user
        assert msgs[1].role == AecoChatRole.assistant


# ---------------------------------------------------------------------------
# Message history
# ---------------------------------------------------------------------------


class TestGetMessageHistory:
    def test_empty_history_returns_empty_list(self, session):
        chat_session = DtChatSession(agent_kind="mas")
        session.add(chat_session)
        session.commit()
        session.refresh(chat_session)
        assert chat_session.id is not None

        svc = _make_service()
        history = svc._get_message_history(session, chat_session.id)
        assert history == []

    def test_history_returns_chronological_order(self, session):
        chat_session = DtChatSession(agent_kind="mas")
        session.add(chat_session)
        session.commit()
        session.refresh(chat_session)
        assert chat_session.id is not None

        svc = _make_service()
        for i in range(5):
            role = AecoChatRole.user if i % 2 == 0 else AecoChatRole.assistant
            session.add(DtChatMessage(
                session_id=chat_session.id,
                role=role,
                content=f"Message {i}",
            ))
        session.commit()

        history = svc._get_message_history(session, chat_session.id)
        contents = [h["content"] for h in history]
        # Must be in ascending creation order
        assert contents == [f"Message {i}" for i in range(5)]

    def test_history_capped_at_limit(self, session):
        chat_session = DtChatSession(agent_kind="mas")
        session.add(chat_session)
        session.commit()
        session.refresh(chat_session)
        assert chat_session.id is not None

        svc = _make_service()
        for i in range(15):
            session.add(DtChatMessage(
                session_id=chat_session.id,
                role=AecoChatRole.user,
                content=f"Turn {i}",
            ))
        session.commit()

        # Default limit is 10
        history = svc._get_message_history(session, chat_session.id, limit=10)
        assert len(history) <= 10

    def test_history_role_key_is_plain_string(self, session):
        """Role in the history dict must be the plain string value (not enum),
        because it's passed directly to the Databricks API payload."""
        chat_session = DtChatSession(agent_kind="mas")
        session.add(chat_session)
        session.commit()
        session.refresh(chat_session)
        assert chat_session.id is not None

        svc = _make_service()
        svc._save_user_message(session, chat_session.id, "Test")

        history = svc._get_message_history(session, chat_session.id)
        assert history[0]["role"] == "user"
        assert isinstance(history[0]["role"], str)

    def test_history_from_different_session_not_mixed(self, session):
        s1 = DtChatSession(agent_kind="mas")
        s2 = DtChatSession(agent_kind="ka")
        session.add(s1)
        session.add(s2)
        session.commit()
        session.refresh(s1)
        session.refresh(s2)
        assert s1.id is not None
        assert s2.id is not None

        svc = _make_service()
        svc._save_user_message(session, s1.id, "Session 1 message")
        svc._save_user_message(session, s2.id, "Session 2 message")

        h1 = svc._get_message_history(session, s1.id)
        h2 = svc._get_message_history(session, s2.id)

        assert len(h1) == 1
        assert h1[0]["content"] == "Session 1 message"
        assert len(h2) == 1
        assert h2[0]["content"] == "Session 2 message"


# ---------------------------------------------------------------------------
# Streaming helpers (async)
# ---------------------------------------------------------------------------


_MOCK_AGENT_RESPONSE = {
    "output": [
        {
            "type": "message",
            "role": "assistant",
            "content": [{"type": "output_text", "text": "Energy usage is 500 kWh today."}],
        }
    ]
}


class TestStreamMasResponse:
    async def _collect_chunks(self, svc, ws, db, user_msg, session_id=None, project_id=None):
        """Drain the async generator and return list of JSON-decoded chunks."""
        chunks = []
        async for chunk in svc.stream_mas_response(
            ws=ws, db=db, user_message=user_msg,
            session_id=session_id, project_id=project_id,
        ):
            chunks.append(json.loads(chunk))
        return chunks

    @patch(
        "innovation_factory.backend.projects.aeco_hub.services.chat_service.query_agent_endpoint",
        return_value=_MOCK_AGENT_RESPONSE,
    )
    @patch(
        "innovation_factory.backend.projects.aeco_hub.services.chat_service.MAS_ENDPOINT_NAME",
        "test-mas-endpoint",
    )
    async def test_mas_yields_content_and_done(self, mock_query, session):
        svc = _make_service()
        chunks = await self._collect_chunks(svc, _fake_ws(), session, "How much energy?")
        assert len(chunks) == 2
        content_chunk = chunks[0]
        done_chunk = chunks[1]
        assert "session_id" in content_chunk
        assert "Energy usage" in content_chunk["content"]
        assert content_chunk["done"] is False
        assert done_chunk["done"] is True

    @patch(
        "innovation_factory.backend.projects.aeco_hub.services.chat_service.MAS_ENDPOINT_NAME",
        "",  # empty → triggers unavailable branch
    )
    async def test_mas_missing_endpoint_yields_unavailable_message(self, session):
        svc = _make_service()
        chunks = await self._collect_chunks(svc, _fake_ws(), session, "Hello?")
        content_chunk = chunks[0]
        # Should contain the fallback message, not raise
        assert "endpoint" in content_chunk["content"].lower() or "AECO" in content_chunk["content"]
        assert chunks[-1]["done"] is True

    @patch(
        "innovation_factory.backend.projects.aeco_hub.services.chat_service.query_agent_endpoint",
        side_effect=RuntimeError("Simulated network error"),
    )
    @patch(
        "innovation_factory.backend.projects.aeco_hub.services.chat_service.MAS_ENDPOINT_NAME",
        "test-mas-endpoint",
    )
    async def test_mas_endpoint_error_yields_fallback_not_raises(self, mock_query, session):
        svc = _make_service()
        chunks = await self._collect_chunks(svc, _fake_ws(), session, "Any question?")
        # Even on error the service must not propagate — yields fallback content
        assert len(chunks) == 2
        assert chunks[-1]["done"] is True
        sources = chunks[0].get("sources", [])
        assert any(s.get("type") == "error" for s in sources)

    @patch(
        "innovation_factory.backend.projects.aeco_hub.services.chat_service.query_agent_endpoint",
        return_value=_MOCK_AGENT_RESPONSE,
    )
    @patch(
        "innovation_factory.backend.projects.aeco_hub.services.chat_service.MAS_ENDPOINT_NAME",
        "test-mas-endpoint",
    )
    async def test_mas_persists_messages_to_db(self, mock_query, session):
        svc = _make_service()
        await self._collect_chunks(svc, _fake_ws(), session, "Persist me")

        msgs = list(session.exec(select(DtChatMessage)).all())
        roles = {m.role for m in msgs}
        assert AecoChatRole.user in roles
        assert AecoChatRole.assistant in roles

    @patch(
        "innovation_factory.backend.projects.aeco_hub.services.chat_service.query_agent_endpoint",
        return_value=_MOCK_AGENT_RESPONSE,
    )
    @patch(
        "innovation_factory.backend.projects.aeco_hub.services.chat_service.MAS_ENDPOINT_NAME",
        "test-mas-endpoint",
    )
    async def test_mas_reuses_existing_session_id(self, mock_query, session):
        """When session_id is provided and found, no new DtChatSession is created."""
        existing = DtChatSession(agent_kind="mas")
        session.add(existing)
        session.commit()
        session.refresh(existing)
        original_id = existing.id

        svc = _make_service()
        chunks = await self._collect_chunks(
            svc, _fake_ws(), session, "Reuse session", session_id=original_id
        )
        content_chunk = chunks[0]
        assert content_chunk["session_id"] == original_id


class TestStreamKaResponse:
    @patch(
        "innovation_factory.backend.projects.aeco_hub.services.chat_service.query_agent_endpoint",
        return_value={
            "choices": [{"message": {"content": "IFC stands for Industry Foundation Classes."}}]
        },
    )
    @patch(
        "innovation_factory.backend.projects.aeco_hub.services.chat_service.STANDARDS_COMPLIANCE_KA_ENDPOINT",
        "test-ka-endpoint",
    )
    async def test_ka_yields_content(self, mock_query, session):
        svc = _make_service()
        chunks = []
        async for chunk in svc.stream_ka_response(
            ws=_fake_ws(), db=session, user_message="What is IFC?",
        ):
            chunks.append(json.loads(chunk))
        assert any("IFC" in c.get("content", "") for c in chunks)
        assert chunks[-1]["done"] is True

    @patch(
        "innovation_factory.backend.projects.aeco_hub.services.chat_service.STANDARDS_COMPLIANCE_KA_ENDPOINT",
        "",  # missing → unavailable
    )
    async def test_ka_missing_endpoint_yields_unavailable(self, session):
        svc = _make_service()
        chunks = []
        async for chunk in svc.stream_ka_response(
            ws=_fake_ws(), db=session, user_message="Regulations?",
        ):
            chunks.append(json.loads(chunk))
        # At least the done sentinel must arrive
        assert chunks[-1]["done"] is True
        # Content must mention unavailability (not empty string)
        first_content = chunks[0].get("content", "")
        assert first_content  # non-empty fallback
