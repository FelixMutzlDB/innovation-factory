"""Unit tests for ChatService business logic (no live Databricks calls).

Covers:
- _generate_mock_response heuristics (pure function — no DB needed)
- _build_system_prompt guardrails
- get_chat_history (session fixture)
- stream_chat_response: missing ticket raises RuntimeError
- stream_chat_response: valid path persists user + assistant messages
- Session reuse across multiple messages on the same ticket
"""
from __future__ import annotations

import asyncio
from unittest.mock import MagicMock

import pytest

from innovation_factory.backend.projects.bsh_home_connect.models import (
    BshChatMessage,
    BshChatRole,
    BshChatSession,
    BshCustomer,
    BshCustomerDevice,
    BshDevice,
    BshTicket,
    BshTicketStatus,
    DeviceCategory,
)
from innovation_factory.backend.projects.bsh_home_connect.services.chat_service import (
    ChatService,
)


# ---------------------------------------------------------------------------
# Helpers — flush-only so the session fixture rolls back
# ---------------------------------------------------------------------------


def _device(session, model_number: str) -> BshDevice:
    d = BshDevice(
        model_number=model_number,
        brand="Bosch",
        name="Serie 8 Test Dishwasher",
        category=DeviceCategory.dishwasher,
    )
    session.add(d)
    session.flush()
    return d


def _customer(session, user_id: str) -> BshCustomer:
    c = BshCustomer(
        databricks_user_id=user_id,
        email=f"{user_id}@test.example",
        first_name="Test",
        last_name="User",
    )
    session.add(c)
    session.flush()
    return c


def _customer_device(session, customer: BshCustomer, device: BshDevice, serial: str) -> BshCustomerDevice:
    cd = BshCustomerDevice(
        customer_id=customer.id,
        device_id=device.id,
        serial_number=serial,
    )
    session.add(cd)
    session.flush()
    return cd


def _ticket(session, customer: BshCustomer, cd: BshCustomerDevice) -> BshTicket:
    t = BshTicket(
        customer_id=customer.id,
        customer_device_id=cd.id,
        title="Dishwasher error",
        description="Error E24 on drain cycle",
        status=BshTicketStatus.open,
    )
    session.add(t)
    session.flush()
    return t


def _collect(agen) -> list[str]:
    """Run an async generator synchronously and return all yielded chunks."""
    async def _inner():
        return [c async for c in agen]
    return asyncio.run(_inner())


# ---------------------------------------------------------------------------
# _generate_mock_response — pure heuristic, no DB
# ---------------------------------------------------------------------------


class TestMockResponseGeneration:
    """The heuristic branches on keywords in user_message."""

    def setup_method(self):
        self.svc = ChatService()
        self.device = MagicMock()
        self.device.brand = "Bosch"
        self.device.name = "Serie 8 Dishwasher"

    def test_error_keyword_triggers_error_guide(self):
        resp = self.svc._generate_mock_response("My device shows an error code", self.device, [])
        assert "Error Code" in resp
        assert "Bosch" in resp

    def test_e15_code_triggers_error_guide(self):
        resp = self.svc._generate_mock_response("I see E15 on the display", self.device, [])
        assert "Error Code" in resp

    def test_e24_code_triggers_error_guide(self):
        resp = self.svc._generate_mock_response("Getting E24 after every cycle", self.device, [])
        assert "Error Code" in resp

    def test_error_guide_includes_unplug_step(self):
        resp = self.svc._generate_mock_response("error", self.device, [])
        # Must tell user to disconnect power before anything else
        assert "unplug" in resp.lower() or "switch off" in resp.lower()

    def test_not_working_triggers_step_guide(self):
        resp = self.svc._generate_mock_response("my appliance is not working", self.device, [])
        assert "power" in resp.lower()
        assert "Bosch" in resp

    def test_broken_keyword_triggers_step_guide(self):
        resp = self.svc._generate_mock_response("The machine is broken", self.device, [])
        assert "power" in resp.lower() or "reset" in resp.lower()

    def test_general_query_returns_capability_summary(self):
        resp = self.svc._generate_mock_response("What can you help me with?", self.device, [])
        assert "Bosch" in resp
        # General response must list at least some capability
        assert any(kw in resp.lower() for kw in ("error code", "troubleshoot", "warranty", "maintenance"))

    def test_all_branches_include_source_citation(self):
        for msg in ("error E15", "not working", "help please"):
            resp = self.svc._generate_mock_response(msg, self.device, [])
            assert "**Source:**" in resp, f"No source citation for message: {msg!r}"

    def test_brand_name_always_present_in_response(self):
        device = MagicMock()
        device.brand = "Siemens"
        device.name = "iQ700 Dishwasher"
        for msg in ("error", "not working", "help"):
            resp = self.svc._generate_mock_response(msg, device, [])
            assert "Siemens" in resp


# ---------------------------------------------------------------------------
# _build_system_prompt
# ---------------------------------------------------------------------------


class TestSystemPrompt:
    def test_prompt_contains_critical_guardrails(self):
        svc = ChatService()
        prompt = svc._build_system_prompt()
        assert "CRITICAL GUARDRAILS" in prompt

    def test_prompt_requires_source_citation(self):
        svc = ChatService()
        prompt = svc._build_system_prompt()
        assert "cite" in prompt.lower() or "ALWAYS cite" in prompt

    def test_prompt_mentions_safety_critical_escalation(self):
        svc = ChatService()
        prompt = svc._build_system_prompt()
        assert "technician" in prompt.lower()

    def test_prompt_prohibits_made_up_specs(self):
        svc = ChatService()
        prompt = svc._build_system_prompt()
        assert "DO NOT make up" in prompt or "do not make up" in prompt.lower()

    def test_prompt_covers_bsh_brands(self):
        svc = ChatService()
        prompt = svc._build_system_prompt()
        assert "Bosch" in prompt or "BSH" in prompt
        assert "Siemens" in prompt


# ---------------------------------------------------------------------------
# get_chat_history
# ---------------------------------------------------------------------------


class TestGetChatHistory:
    def test_empty_for_nonexistent_ticket(self, session):
        svc = ChatService()
        result = svc.get_chat_history(session, 999_999, "customer_support")
        assert result == []

    def test_empty_when_session_type_mismatches(self, session):
        svc = ChatService()
        dev = _device(session, "HIST-MISMATCH-01")
        cust = _customer(session, "hist-mismatch-user")
        cd = _customer_device(session, cust, dev, "HIST-MM-SN-001")
        ticket = _ticket(session, cust, cd)
        assert ticket.id is not None

        chat_sess = BshChatSession(ticket_id=ticket.id, session_type="customer_support")
        session.add(chat_sess)
        session.flush()

        session.add(BshChatMessage(
            session_id=chat_sess.id, role=BshChatRole.user, content="Hello"
        ))
        session.flush()

        # Asking for a different type returns empty
        result = svc.get_chat_history(session, ticket.id, "technician_assist")
        assert result == []

    def test_returns_messages_in_ascending_order(self, session):
        svc = ChatService()
        dev = _device(session, "HIST-ORDER-01")
        cust = _customer(session, "hist-order-user")
        cd = _customer_device(session, cust, dev, "HIST-ORD-SN-001")
        ticket = _ticket(session, cust, cd)
        assert ticket.id is not None

        chat_sess = BshChatSession(ticket_id=ticket.id, session_type="customer_support")
        session.add(chat_sess)
        session.flush()

        msg1 = BshChatMessage(
            session_id=chat_sess.id, role=BshChatRole.user, content="First"
        )
        msg2 = BshChatMessage(
            session_id=chat_sess.id, role=BshChatRole.assistant, content="Second"
        )
        session.add(msg1)
        session.flush()
        session.add(msg2)
        session.flush()

        msgs = svc.get_chat_history(session, ticket.id, "customer_support")
        assert len(msgs) == 2
        assert msgs[0].content == "First"
        assert msgs[1].content == "Second"
        assert msgs[0].role == BshChatRole.user
        assert msgs[1].role == BshChatRole.assistant


# ---------------------------------------------------------------------------
# stream_chat_response
# ---------------------------------------------------------------------------


class TestStreamChatResponse:
    """Tests that exercise the async generator path of the service."""

    def test_raises_runtime_error_for_missing_ticket(self, session):
        svc = ChatService()

        with pytest.raises(RuntimeError, match="999999"):
            _collect(svc.stream_chat_response(
                db=session, ticket_id=999_999, user_message="help",
            ))

    def test_yields_non_empty_response_for_valid_ticket(self, session):
        svc = ChatService()
        dev = _device(session, "STREAM-VALID-01")
        cust = _customer(session, "stream-valid-user-01")
        cd = _customer_device(session, cust, dev, "STREAM-V-SN-001")
        ticket = _ticket(session, cust, cd)
        assert ticket.id is not None

        chunks = _collect(svc.stream_chat_response(
            db=session, ticket_id=ticket.id,
            user_message="error E15", session_type="customer_support",
        ))

        assert len(chunks) >= 1
        full = "".join(chunks)
        assert len(full) > 0

    def test_persists_user_and_assistant_messages(self, session):
        svc = ChatService()
        dev = _device(session, "STREAM-PERSIST-01")
        cust = _customer(session, "stream-persist-user-01")
        cd = _customer_device(session, cust, dev, "STREAM-P-SN-001")
        ticket = _ticket(session, cust, cd)
        assert ticket.id is not None

        _collect(svc.stream_chat_response(
            db=session, ticket_id=ticket.id,
            user_message="not working at all", session_type="customer_support",
        ))

        msgs = svc.get_chat_history(session, ticket.id, "customer_support")
        assert len(msgs) >= 2
        user_msgs = [m for m in msgs if m.role == BshChatRole.user]
        asst_msgs = [m for m in msgs if m.role == BshChatRole.assistant]
        assert len(user_msgs) >= 1
        assert len(asst_msgs) >= 1
        assert any(m.content == "not working at all" for m in user_msgs)

    def test_assistant_message_includes_sources(self, session):
        svc = ChatService()
        dev = _device(session, "STREAM-SRC-01")
        cust = _customer(session, "stream-src-user-01")
        cd = _customer_device(session, cust, dev, "STREAM-SRC-SN-001")
        ticket = _ticket(session, cust, cd)
        assert ticket.id is not None

        _collect(svc.stream_chat_response(
            db=session, ticket_id=ticket.id,
            user_message="error code",
        ))

        msgs = svc.get_chat_history(session, ticket.id, "customer_support")
        asst_msgs = [m for m in msgs if m.role == BshChatRole.assistant]
        assert len(asst_msgs) >= 1
        # Sources should be a list (may be empty if no context articles matched)
        assert isinstance(asst_msgs[0].sources, list)

    def test_second_message_reuses_existing_session(self, session):
        """Two calls on the same ticket + session_type must reuse one BshChatSession."""
        from sqlmodel import select
        svc = ChatService()
        dev = _device(session, "STREAM-REUSE-01")
        cust = _customer(session, "stream-reuse-user-01")
        cd = _customer_device(session, cust, dev, "STREAM-REUSE-SN-001")
        ticket = _ticket(session, cust, cd)
        assert ticket.id is not None

        _collect(svc.stream_chat_response(
            db=session, ticket_id=ticket.id,
            user_message="first question", session_type="customer_support",
        ))
        _collect(svc.stream_chat_response(
            db=session, ticket_id=ticket.id,
            user_message="follow-up", session_type="customer_support",
        ))

        sessions = list(session.exec(
            select(BshChatSession).where(
                BshChatSession.ticket_id == ticket.id,
                BshChatSession.session_type == "customer_support",
            )
        ).all())
        assert len(sessions) == 1, (
            f"Expected one reused session, got {len(sessions)}"
        )

    def test_different_session_types_create_separate_sessions(self, session):
        """customer_support and technician_assist are independent sessions."""
        from sqlmodel import select
        svc = ChatService()
        dev = _device(session, "STREAM-DUAL-01")
        cust = _customer(session, "stream-dual-user-01")
        cd = _customer_device(session, cust, dev, "STREAM-DUAL-SN-001")
        ticket = _ticket(session, cust, cd)
        assert ticket.id is not None

        _collect(svc.stream_chat_response(
            db=session, ticket_id=ticket.id,
            user_message="customer question", session_type="customer_support",
        ))
        _collect(svc.stream_chat_response(
            db=session, ticket_id=ticket.id,
            user_message="technician note", session_type="technician_assist",
        ))

        sessions = list(session.exec(
            select(BshChatSession).where(BshChatSession.ticket_id == ticket.id)
        ).all())
        types = {s.session_type for s in sessions}
        assert "customer_support" in types
        assert "technician_assist" in types
