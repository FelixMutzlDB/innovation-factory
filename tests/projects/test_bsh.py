"""BSH Home Connect specific tests."""
import pytest
from datetime import datetime, timezone

from innovation_factory.backend.projects.bsh_home_connect.models import (
    BshDevice,
    BshChatHistoryOut,
    DeviceCategory,
)


class TestBshModels:
    def test_device_creation(self, session):
        d = BshDevice(
            model_number="WM14",
            brand="Bosch",
            name="Serie 6 Washing Machine",
            category=DeviceCategory.washing_machine,
            specifications={"capacity": "9kg"},
        )
        session.add(d)
        session.flush()
        assert d.id is not None

    def test_chat_history_out_with_empty_messages(self):
        """Regression: started_at should not be None when messages is empty."""
        hist = BshChatHistoryOut(
            session_id=1,
            ticket_id=1,
            session_type="customer_support",
            started_at=datetime.now(timezone.utc),
            messages=[],
        )
        assert hist.started_at is not None


class TestBshAPI:
    def test_devices_list(self, client):
        resp = client.get("/api/projects/bsh-home-connect/devices")
        assert resp.status_code == 200

    def test_knowledge_search(self, client):
        resp = client.get(
            "/api/projects/bsh-home-connect/knowledge/search?query=dishwasher"
        )
        assert resp.status_code == 200
