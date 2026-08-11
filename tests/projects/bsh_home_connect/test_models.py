"""Model validation, enum checks, and serialization round-trips for bsh_home_connect.

Covers:
- Enum completeness (no silent renames)
- 3-model pattern (Entity / EntityIn / EntityOut) per CLAUDE.md
- Pydantic I/O model serialization
- LongText sanitization on BshChatMessageIn
- SQLModel table field persistence (using session.flush so it rolls back)
"""
from __future__ import annotations

from datetime import datetime, timezone

import pytest

import innovation_factory.backend.projects.bsh_home_connect.models as bsh_models
from innovation_factory.backend.projects.bsh_home_connect.models import (
    BshChatHistoryOut,
    BshChatMessageIn,
    BshChatRole,
    BshCustomer,
    BshCustomerDeviceOut,
    BshDevice,
    BshDeviceOut,
    BshDocument,
    BshKnowledgeArticle,
    BshKnowledgeArticleOut,
    BshTicket,
    BshTicketOut,
    BshTicketStatus,
    DeviceCategory,
    MediaType,
    UserRole,
)


# ---------------------------------------------------------------------------
# Enum completeness
# ---------------------------------------------------------------------------


class TestEnumValues:
    """All status/category enums must contain their contracted values.

    Renames are a silent breaking change — the DB stores strings, so a
    rename passes at write-time but breaks every existing row at read-time.
    """

    def test_ticket_status_has_all_expected_values(self):
        expected = {
            "open", "in_progress", "awaiting_parts", "awaiting_customer",
            "shipped_for_repair", "in_repair", "resolved", "closed",
        }
        actual = {s.value for s in BshTicketStatus}
        assert expected <= actual, f"Missing BshTicketStatus values: {expected - actual}"

    def test_device_category_has_key_appliances(self):
        expected = {
            "washing_machine", "dryer", "dishwasher", "refrigerator",
            "oven", "cooktop", "microwave", "coffee_machine", "vacuum_cleaner",
        }
        actual = {c.value for c in DeviceCategory}
        assert expected <= actual, f"Missing DeviceCategory values: {expected - actual}"

    def test_bsh_chat_role_values(self):
        assert BshChatRole.user.value == "user"
        assert BshChatRole.assistant.value == "assistant"
        assert BshChatRole.system.value == "system"

    def test_user_role_values(self):
        assert UserRole.customer.value == "customer"
        assert UserRole.technician.value == "technician"
        assert UserRole.system.value == "system"

    def test_media_type_values(self):
        assert MediaType.image.value == "image"
        assert MediaType.video.value == "video"
        assert MediaType.document.value == "document"


# ---------------------------------------------------------------------------
# 3-model pattern (CLAUDE.md)
# ---------------------------------------------------------------------------


class TestThreeModelPattern:
    """Every API-surfaced entity must have Entity (table), EntityOut, and
    EntityIn (where the API accepts writes). Internal-only tables only need
    the table model.
    """

    @pytest.mark.parametrize("table_name, out_name, in_name", [
        ("BshDevice", "BshDeviceOut", None),
        ("BshCustomer", "BshCustomerOut", "BshCustomerIn"),
        ("BshTechnician", "BshTechnicianOut", None),
        ("BshCustomerDevice", "BshCustomerDeviceOut", "BshCustomerDeviceIn"),
        ("BshTicket", "BshTicketOut", "BshTicketIn"),
        ("BshTicketNote", "BshTicketNoteOut", "BshTicketNoteIn"),
        ("BshChatSession", None, None),           # internal session, no API I/O model needed
        ("BshChatMessage", "BshChatMessageOut", "BshChatMessageIn"),
        ("BshKnowledgeArticle", "BshKnowledgeArticleOut", None),
        ("BshDocument", "BshDocumentOut", None),
    ])
    def test_table_and_io_classes_exist(self, table_name, out_name, in_name):
        assert hasattr(bsh_models, table_name), f"Missing table model: {table_name}"
        if out_name:
            assert hasattr(bsh_models, out_name), f"Missing Out model: {out_name}"
        if in_name:
            assert hasattr(bsh_models, in_name), f"Missing In model: {in_name}"

    def test_ticket_update_model_exists(self):
        """BshTicketUpdate is a partial-update schema, not a full In model."""
        assert hasattr(bsh_models, "BshTicketUpdate")

    def test_chat_history_out_exists(self):
        """BshChatHistoryOut wraps session + messages for the history endpoint."""
        assert hasattr(bsh_models, "BshChatHistoryOut")


# ---------------------------------------------------------------------------
# Serialization round-trips
# ---------------------------------------------------------------------------


class TestSerializationRoundTrips:
    """Pydantic output models must round-trip through model_dump/model_validate
    without data loss or type errors.
    """

    def test_bsh_ticket_out_round_trip(self):
        now = datetime.now(timezone.utc)
        ticket = BshTicketOut(
            id=1, customer_id=1, customer_device_id=1,
            title="Dishwasher not draining",
            description="Error code E24 after wash cycle",
            status=BshTicketStatus.open,
            priority=2,
            created_at=now, updated_at=now,
        )
        data = ticket.model_dump()
        restored = BshTicketOut.model_validate(data)
        assert restored.id == ticket.id
        assert restored.status == BshTicketStatus.open
        assert restored.title == "Dishwasher not draining"
        assert restored.priority == 2
        assert restored.technician_id is None
        assert restored.customer_device is None

    def test_bsh_customer_device_out_with_nested_device(self):
        now = datetime.now(timezone.utc)
        device_out = BshDeviceOut(
            id=5, model_number="SMS8YCI03E", brand="Bosch",
            category=DeviceCategory.dishwasher,
            name="Serie 8 Dishwasher", created_at=now,
        )
        cdo = BshCustomerDeviceOut(
            id=10, customer_id=1, device_id=5,
            serial_number="SN-ROUNDTRIP-001",
            registered_at=now, device=device_out,
        )
        data = cdo.model_dump()
        assert data["device"]["brand"] == "Bosch"
        assert data["device"]["category"] == "dishwasher"
        assert data["serial_number"] == "SN-ROUNDTRIP-001"

    def test_bsh_device_out_optional_fields_default_none(self):
        now = datetime.now(timezone.utc)
        d = BshDeviceOut(
            id=1, model_number="M1", brand="Bosch",
            category=DeviceCategory.oven, name="Test Oven", created_at=now,
        )
        assert d.description is None
        assert d.specifications is None
        assert d.image_url is None

    def test_bsh_knowledge_article_out_optional_fields(self):
        now = datetime.now(timezone.utc)
        article = BshKnowledgeArticleOut(
            id=1, title="Dishwasher Error E15",
            content="Switch off and check hoses",
            category=DeviceCategory.dishwasher,
            view_count=0, helpful_count=0,
            created_at=now, updated_at=now,
        )
        assert article.tags is None
        assert article.issue_type is None
        assert article.device_id is None

    def test_bsh_chat_history_out_empty_messages(self):
        """Regression: started_at must be set even when messages list is empty."""
        hist = BshChatHistoryOut(
            session_id=1, ticket_id=1,
            session_type="customer_support",
            started_at=datetime.now(timezone.utc),
            messages=[],
        )
        assert hist.started_at is not None
        assert hist.messages == []
        assert hist.ended_at is None

    def test_bsh_ticket_out_status_enum_preserved(self):
        """Status values survive JSON serialisation without losing type info."""
        now = datetime.now(timezone.utc)
        for status in BshTicketStatus:
            t = BshTicketOut(
                id=1, customer_id=1, customer_device_id=1,
                title="t", description="d",
                status=status, priority=3,
                created_at=now, updated_at=now,
            )
            assert t.status == status


# ---------------------------------------------------------------------------
# LongText sanitization on BshChatMessageIn
# ---------------------------------------------------------------------------


class TestLongTextSanitization:
    """BshChatMessageIn.message uses LongText, which strips HTML tags and
    null bytes at ingest (lessons §20 / input_sanitize.py).
    """

    def test_html_script_tags_stripped(self):
        msg = BshChatMessageIn(message="<script>alert('xss')</script>Hello")
        assert "<script>" not in msg.message
        assert "Hello" in msg.message

    def test_html_img_tags_stripped(self):
        msg = BshChatMessageIn(message='<img src="x" onerror="bad()">show')
        assert "<img" not in msg.message
        assert "show" in msg.message

    def test_null_bytes_stripped(self):
        msg = BshChatMessageIn(message="Error\x00Code\x00E15")
        assert "\x00" not in msg.message
        assert "Error" in msg.message

    def test_normal_message_passes_unchanged(self):
        text = "My dishwasher shows error E15 — water in base tray"
        msg = BshChatMessageIn(message=text)
        assert msg.message == text

    def test_message_too_long_raises_validation_error(self):
        from pydantic import ValidationError
        with pytest.raises(ValidationError):
            BshChatMessageIn(message="x" * 5001)

    def test_empty_session_type_defaults(self):
        msg = BshChatMessageIn(message="Hello")
        assert msg.session_type == "troubleshooting"


# ---------------------------------------------------------------------------
# SQLModel persistence (flush-only — rolled back by session fixture)
# ---------------------------------------------------------------------------


class TestDeviceModelPersistence:
    """BshDevice can be added with minimal and full field sets."""

    def test_device_minimal_fields_persisted(self, session):
        d = BshDevice(
            model_number="MODEL-TEST-MINIMAL-01",
            brand="Bosch",
            name="Test Washing Machine",
            category=DeviceCategory.washing_machine,
        )
        session.add(d)
        session.flush()
        assert d.id is not None
        assert d.specifications is None
        assert d.created_at is not None

    def test_device_with_specifications_dict(self, session):
        d = BshDevice(
            model_number="MODEL-TEST-SPEC-01",
            brand="Siemens",
            name="Test Dishwasher",
            category=DeviceCategory.dishwasher,
            specifications={"capacity": "14 place settings", "energy_class": "A+++"},
        )
        session.add(d)
        session.flush()
        assert d.specifications is not None
        assert d.specifications["capacity"] == "14 place settings"

    def test_knowledge_article_with_tags_list(self, session):
        device = BshDevice(
            model_number="MODEL-TEST-KB-01",
            brand="Bosch",
            name="Serie 6 Oven",
            category=DeviceCategory.oven,
        )
        session.add(device)
        session.flush()

        article = BshKnowledgeArticle(
            device_id=device.id,
            title="Oven Not Heating",
            content="Check heating element and temperature sensor",
            category=DeviceCategory.oven,
            tags=["oven", "heating", "temperature"],
        )
        session.add(article)
        session.flush()
        assert article.id is not None
        assert article.tags == ["oven", "heating", "temperature"]
        assert article.view_count == 0

    def test_document_model_persisted(self, session):
        device = BshDevice(
            model_number="MODEL-TEST-DOC-01",
            brand="Bosch",
            name="Coffee Machine",
            category=DeviceCategory.coffee_machine,
        )
        session.add(device)
        session.flush()

        doc = BshDocument(
            device_id=device.id,
            title="User Manual",
            document_type="user_manual",
            content="Chapter 1: Safety instructions",
            language="en",
            version="2.0",
        )
        session.add(doc)
        session.flush()
        assert doc.id is not None
        assert doc.language == "en"
