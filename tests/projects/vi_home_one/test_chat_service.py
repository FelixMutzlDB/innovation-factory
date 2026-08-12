"""Unit tests for the ChatService mock response dispatch and stream logic.

Tests _generate_mock_response() keyword routing and stream_chat_response()
error handling (missing ticket). The actual streaming tokens are tested with
an async helper since pytest-asyncio is not required — we drain the async
generator via asyncio.run().
"""
from __future__ import annotations

import asyncio
import pytest

import innovation_factory.backend.projects.vi_home_one.models  # noqa: F401


class TestMockResponseKeywords:
    """_generate_mock_response dispatches on keywords in user_message."""

    def _service(self):
        from innovation_factory.backend.projects.vi_home_one.services.chat_service import ChatService
        return ChatService()

    def test_heat_not_warm_triggers_heat_pump_response(self):
        svc = self._service()
        response = svc._generate_mock_response("My heat pump is not warm", "", device=None)
        assert "heat pump" in response.lower() or "heating" in response.lower()
        assert "Source:" in response

    def test_not_heating_also_triggers_heat_pump_response(self):
        svc = self._service()
        response = svc._generate_mock_response("The system is not heating", "", device=None)
        # 'not' + 'heat' keyword path
        assert "filter" in response.lower() or "thermostat" in response.lower()

    def test_pv_keyword_triggers_solar_response(self):
        svc = self._service()
        response = svc._generate_mock_response("My PV output is low", "", device=None)
        assert "pv" in response.lower() or "solar" in response.lower()
        assert "Source:" in response

    def test_solar_keyword_triggers_solar_response(self):
        svc = self._service()
        response = svc._generate_mock_response("Solar panels not generating", "", device=None)
        assert "Solar Panel" in response or "solar" in response.lower()

    def test_panel_keyword_triggers_solar_response(self):
        svc = self._service()
        response = svc._generate_mock_response("Panel output dropped", "", device=None)
        assert "Source:" in response

    def test_battery_not_charging_triggers_battery_response(self):
        svc = self._service()
        response = svc._generate_mock_response("Battery is not charging", "", device=None)
        assert "battery" in response.lower()
        assert "Source:" in response

    def test_battery_charg_triggers_battery_response(self):
        svc = self._service()
        response = svc._generate_mock_response("How does battery charging work?", "", device=None)
        assert "battery" in response.lower()

    def test_cost_keyword_triggers_cost_response(self):
        svc = self._service()
        response = svc._generate_mock_response("How can I reduce my cost?", "", device=None)
        assert "Night Tariff" in response or "cost" in response.lower()
        assert "Source:" in response

    def test_save_keyword_triggers_cost_response(self):
        svc = self._service()
        response = svc._generate_mock_response("How do I save money on energy?", "", device=None)
        assert "Night Tariff" in response or "save" in response.lower()

    def test_money_keyword_triggers_cost_response(self):
        svc = self._service()
        response = svc._generate_mock_response("I want to save money", "", device=None)
        assert "Source:" in response

    def test_unknown_message_returns_fallback(self):
        svc = self._service()
        response = svc._generate_mock_response("Hello, I need help", "", device=None)
        assert "ViDistrictOne Knowledge Base" in response or "I'm here to help" in response

    def test_fallback_includes_device_info_when_device_present(self):
        """Fallback path includes brand/model when device is not None."""
        svc = self._service()

        class FakeDevice:
            brand = "Viessmann"
            model = "Vitocal 250-A"

        response = svc._generate_mock_response("Random question", "", device=FakeDevice())
        assert "Viessmann" in response
        assert "Vitocal 250-A" in response

    def test_fallback_handles_none_device(self):
        """Fallback path must not raise when device=None."""
        svc = self._service()
        response = svc._generate_mock_response("Random question", "", device=None)
        assert isinstance(response, str)
        assert len(response) > 0

    def test_all_responses_include_source_citation(self):
        """S4 guardrail: every response must cite a source."""
        svc = self._service()
        messages = [
            "not warm",
            "my pv is down",
            "battery not charging",
            "reduce cost",
        ]
        for msg in messages:
            resp = svc._generate_mock_response(msg, "", device=None)
            assert "Source:" in resp, f"Missing source citation for message: {msg!r}"


class TestStreamChatMissingTicket:
    """stream_chat_response yields error string for unknown ticket IDs."""

    def test_missing_ticket_yields_error(self, session):
        from innovation_factory.backend.projects.vi_home_one.services.chat_service import ChatService

        svc = ChatService()

        async def drain():
            chunks = []
            async for chunk in svc.stream_chat_response(99999, "help", session):
                chunks.append(chunk)
            return "".join(chunks)

        result = asyncio.run(drain())
        assert "Error" in result or "not found" in result.lower()

    def test_valid_ticket_streams_tokens(self, session):
        """With a real ticket, the generator yields at least one token."""
        from innovation_factory.backend.projects.vi_home_one.models import (
            VhNeighborhood, VhHousehold, VhTicket,
        )
        from innovation_factory.backend.projects.vi_home_one.services.chat_service import ChatService

        n = VhNeighborhood(name="Chat Test Hood", location="Berlin", total_households=1)
        session.add(n)
        session.flush()
        h = VhHousehold(neighborhood_id=n.id, owner_name="Chat User", address="Test Str. 1")
        session.add(h)
        session.flush()
        t = VhTicket(household_id=h.id, title="Test issue", description="Details here")
        session.add(t)
        session.commit()
        assert t.id is not None
        ticket_id: int = t.id

        svc = ChatService()

        async def drain():
            chunks = []
            async for chunk in svc.stream_chat_response(ticket_id, "I need help", session):
                chunks.append(chunk)
            return "".join(chunks)

        result = asyncio.run(drain())
        assert len(result) > 0


class TestChatServiceSystemPrompt:
    def test_s4_guardrail_in_system_prompt(self):
        from innovation_factory.backend.projects.vi_home_one.services.chat_service import ChatService
        svc = ChatService()
        prompt = svc.system_prompt
        assert "safety-critical" in prompt.lower() or "Safety" in prompt
        assert "source" in prompt.lower()

    def test_temperature_is_low(self):
        from innovation_factory.backend.projects.vi_home_one.services.chat_service import ChatService
        svc = ChatService()
        assert svc.temperature <= 0.2, "Temperature should be low for deterministic demo responses"
