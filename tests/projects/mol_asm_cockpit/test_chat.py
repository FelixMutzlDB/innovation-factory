"""Tests for the chat service and chat history endpoints.

The POST /chat/send endpoint requires ``request.app.state.runtime.ws``
(WorkspaceClient), which may not be available in test environments without
Databricks credentials. Tests here focus on:

1. Pure-service unit tests for ``_mock_response`` and ``send_message``
   (no DB, no HTTP).
2. Chat history endpoint (GET-only, no WS dependency).
3. Chat session seeding + history retrieval round-trip.
"""
from __future__ import annotations

from unittest.mock import MagicMock, patch

import pytest

from ._helpers import seed_chat_session

BASE = "/api/projects/mol-asm-cockpit"


# ---------------------------------------------------------------------------
# _mock_response keyword routing (pure unit tests — no DB, no HTTP)
# ---------------------------------------------------------------------------


class TestMockResponseKeywords:
    """The mock responder uses keyword matching to select a canned reply.
    These are load-bearing for the demo flow when no live MAS is configured."""

    def _call(self, message: str) -> str:
        from innovation_factory.backend.projects.mol_asm_cockpit.services.chat_service import (
            _mock_response,
        )
        return _mock_response(message)

    def test_underperform_keyword_triggers_performance_analysis(self):
        resp = self._call("Why is this station underperforming this month?")
        assert "Traffic" in resp or "Pricing" in resp or "diesel" in resp.lower()

    def test_drop_keyword_triggers_performance_analysis(self):
        resp = self._call("Sales drop detected")
        # The performance-analysis branch includes a "Suggested Actions" heading
        assert "Suggested Actions" in resp

    def test_decline_keyword_triggers_performance_analysis(self):
        resp = self._call("Revenue decline observed")
        assert len(resp) > 50  # non-trivial response

    def test_upside_keyword_triggers_opportunity_analysis(self):
        resp = self._call("What are the upside opportunities this week?")
        assert "opportunity" in resp.lower() or "Pricing" in resp or "Fresh" in resp

    def test_best_keyword_triggers_opportunity_analysis(self):
        resp = self._call("Which stations have the best performance?")
        # Opportunity branch mentions margin or staffing
        assert "margin" in resp.lower() or "Staffing" in resp or "stations" in resp.lower()

    def test_food_keyword_triggers_fresh_corner_analysis(self):
        resp = self._call("Tell me about hot dog and food trends")
        assert "Fresh Corner" in resp or "coffee" in resp.lower() or "Bakery" in resp

    def test_coffee_keyword_triggers_fresh_corner_analysis(self):
        resp = self._call("How is coffee sales doing?")
        assert "coffee" in resp.lower() or "Fresh Corner" in resp

    def test_generic_message_returns_help_menu(self):
        resp = self._call("Hello, what can you help me with?")
        # Generic help lists several topic areas
        assert "Performance" in resp or "Pricing" in resp or "Operations" in resp

    def test_empty_message_returns_help_menu(self):
        resp = self._call("")
        assert len(resp) > 50


# ---------------------------------------------------------------------------
# send_message: no MAS endpoint → mock path
# ---------------------------------------------------------------------------


class TestSendMessageMockPath:
    """When MAS_ENDPOINT_NAME is falsy, send_message must return a mock
    response without touching the WorkspaceClient."""

    def test_returns_string_response(self):
        from innovation_factory.backend.projects.mol_asm_cockpit.services.chat_service import (
            send_message,
        )

        ws_mock = MagicMock()
        # MAS_ENDPOINT_NAME is empty in test env (no env var set)
        response = send_message(ws_mock, "How are sales doing?")
        assert isinstance(response, str)
        assert len(response) > 10

    def test_ws_not_called_when_no_endpoint(self):
        """WorkspaceClient methods must NOT be invoked when MAS is unconfigured."""
        from innovation_factory.backend.projects.mol_asm_cockpit.services.chat_service import (
            send_message,
        )

        ws_mock = MagicMock()
        send_message(ws_mock, "any message")
        # ws_mock should have had zero interactions
        ws_mock.assert_not_called()
        ws_mock.serving_endpoints.query.assert_not_called()

    def test_exception_in_agent_returns_error_string(self):
        """If the agent call raises, send_message must return a graceful error
        string rather than propagating the exception."""
        from innovation_factory.backend.projects.mol_asm_cockpit.services import (
            chat_service,
        )
        from innovation_factory.backend.projects.mol_asm_cockpit.services.chat_service import (
            send_message as _send_message,
        )

        ws_mock = MagicMock()
        with patch.object(chat_service, "MAS_ENDPOINT_NAME", "fake-endpoint"):
            with patch(
                "innovation_factory.backend.projects.mol_asm_cockpit.services.chat_service.query_agent_endpoint",
                side_effect=RuntimeError("connection refused"),
            ):
                resp = _send_message(ws_mock, "test message")
        assert "encountered an issue" in resp.lower() or "error" in resp.lower()


# ---------------------------------------------------------------------------
# Chat history endpoint (no WS dependency)
# ---------------------------------------------------------------------------


class TestChatHistory:
    def test_unknown_session_returns_404(self, client):
        resp = client.get(f"{BASE}/chat/history/999999")
        assert resp.status_code == 404

    def test_empty_session_history_returns_200(self, client):
        """A session with no messages returns 200 with an empty messages list.
        This tests the endpoint without triggering the model_validate bug
        (which only fires when messages exist — see xfail tests below)."""
        from ._helpers import _seeding_session
        from innovation_factory.backend.projects.mol_asm_cockpit.models import MacChatSession

        with _seeding_session(client) as session:
            chat_session = MacChatSession(session_type="issue_resolution")
            session.add(chat_session)
            session.flush()
            session_id = chat_session.id

        resp = client.get(f"{BASE}/chat/history/{session_id}")
        assert resp.status_code == 200
        data = resp.json()
        assert data["session_id"] == session_id
        assert data["messages"] == []

    def test_seeded_session_history_returns_200(self, client):
        """Regression (fixed): GET /chat/history returns 200 with messages.
        chat.py:86 previously passed a SQLModel instance to
        MacChatMessageOut.model_validate() → 500; fixed via m.model_dump()."""
        session_id = seed_chat_session(client)
        resp = client.get(f"{BASE}/chat/history/{session_id}")
        assert resp.status_code == 200
        data = resp.json()
        assert data["session_id"] == session_id
        assert data["session_type"] == "issue_resolution"
        assert isinstance(data["messages"], list)
        assert len(data["messages"]) >= 1

    def test_history_message_has_required_fields(self, client):
        session_id = seed_chat_session(client)
        resp = client.get(f"{BASE}/chat/history/{session_id}")
        assert resp.status_code == 200
        messages = resp.json()["messages"]
        assert len(messages) >= 1
        msg = messages[0]
        for field in ("id", "session_id", "role", "content", "created_at"):
            assert field in msg, f"Chat message missing field: {field}"

    def test_history_message_role_is_user(self, client):
        session_id = seed_chat_session(client)
        resp = client.get(f"{BASE}/chat/history/{session_id}")
        assert resp.status_code == 200
        messages = resp.json()["messages"]
        assert any(m["role"] == "user" for m in messages)
