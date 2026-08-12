"""Tests for MOL ASM Cockpit models, enums, and Pydantic schemas.

Covers:
- Enum prefix discipline (MacAlertSeverity not AlertSeverity)
- Enum string values (they back DB rows — must not drift)
- Default field values (status, priority, delivery_scheduled)
- Pydantic I/O model shapes and validation (MacStationKPI, MacAnomalyAlertUpdate)
- DB model creation via session fixture (flush + rollback, no persistent state)
"""
from __future__ import annotations

from datetime import date, datetime, timezone

import pytest
from pydantic import ValidationError

from innovation_factory.backend.projects.mol_asm_cockpit import models as mac_models
from innovation_factory.backend.projects.mol_asm_cockpit.models import (
    FuelType,
    LoyaltyTier,
    MacAlertSeverity,
    MacAlertStatus,
    MacAnomalyAlert,
    MacAnomalyAlertUpdate,
    MacChatHistoryOut,
    MacChatMessageIn,
    MacChatRole,
    MacChatSession,
    MacInventory,
    MacIssue,
    MacIssueCategory,
    MacIssueStatus,
    MacRegion,
    MacStation,
    MacStationKPI,
    NonfuelCategory,
    ProductCategory,
    ShiftType,
    StationType,
)

BASE = "/api/projects/mol-asm-cockpit"


# ---------------------------------------------------------------------------
# Enum prefix discipline
# ---------------------------------------------------------------------------


class TestEnumPrefixes:
    """All alert/issue/chat enums must carry the Mac prefix to avoid
    OpenAPI schema collisions with other accelerators."""

    def test_known_mac_prefixed_enums_exist(self):
        required = {
            "MacAlertSeverity",
            "MacAlertStatus",
            "MacIssueStatus",
            "MacIssueCategory",
            "MacChatRole",
        }
        for name in required:
            assert hasattr(mac_models, name), f"Missing enum: {name}"

    def test_no_unprefixed_collision_names(self):
        """Regression: bare names would collide with yard_pro / other accelerators."""
        for bare in ("AlertSeverity", "AlertStatus", "IssueStatus", "ChatRole"):
            assert not hasattr(mac_models, bare), (
                f"'{bare}' must not exist on mac_models — use Mac-prefix"
            )


# ---------------------------------------------------------------------------
# Enum value stability
# ---------------------------------------------------------------------------


class TestEnumValues:
    """Enum values back DB rows — any drift would corrupt persisted data."""

    def test_alert_severity_four_levels(self):
        assert MacAlertSeverity.low == "low"
        assert MacAlertSeverity.medium == "medium"
        assert MacAlertSeverity.high == "high"
        assert MacAlertSeverity.critical == "critical"

    def test_alert_status_four_states(self):
        assert MacAlertStatus.active == "active"
        assert MacAlertStatus.acknowledged == "acknowledged"
        assert MacAlertStatus.resolved == "resolved"
        assert MacAlertStatus.dismissed == "dismissed"

    def test_issue_status_values(self):
        assert MacIssueStatus.open == "open"
        assert MacIssueStatus.in_progress == "in_progress"
        assert MacIssueStatus.resolved == "resolved"
        assert MacIssueStatus.closed == "closed"

    def test_station_type_values(self):
        assert StationType.highway == "highway"
        assert StationType.urban == "urban"
        assert StationType.suburban == "suburban"

    def test_fuel_type_includes_lpg(self):
        assert FuelType.lpg == "lpg"
        assert FuelType.diesel == "diesel"
        assert FuelType.premium_98 == "premium_98"

    def test_loyalty_tier_four_levels(self):
        assert LoyaltyTier.bronze == "bronze"
        assert LoyaltyTier.silver == "silver"
        assert LoyaltyTier.gold == "gold"
        assert LoyaltyTier.platinum == "platinum"

    def test_shift_type_values(self):
        assert ShiftType.morning == "morning"
        assert ShiftType.afternoon == "afternoon"
        assert ShiftType.night == "night"


# ---------------------------------------------------------------------------
# DB model defaults via session
# ---------------------------------------------------------------------------


class TestModelDefaults:
    """Verify default field values on SQLModel tables.
    Tests use flush-only (no commit) → rolled back at teardown."""

    def _make_region_and_station(self, session, suffix: str):
        region = MacRegion(name=f"Defaults Region {suffix}", country="HU")
        session.add(region)
        session.flush()
        station = MacStation(
            station_code=f"DFLT-{suffix}-001",
            name=f"Defaults Station {suffix}",
            city="Budapest",
            region_id=region.id,
            station_type=StationType.urban,
            latitude=47.5,
            longitude=19.0,
        )
        session.add(station)
        session.flush()
        return region, station

    def test_anomaly_alert_status_defaults_to_active(self, session):
        _, station = self._make_region_and_station(session, "ALERT")
        alert = MacAnomalyAlert(
            station_id=station.id,
            metric_type="fuel_volume",
            severity=MacAlertSeverity.high,
            title="Test alert",
            description="Test description",
            suggested_action="Test action",
        )
        session.add(alert)
        session.flush()
        assert alert.status == MacAlertStatus.active

    def test_anomaly_alert_resolved_at_is_none_by_default(self, session):
        _, station = self._make_region_and_station(session, "RESOLVD")
        alert = MacAnomalyAlert(
            station_id=station.id,
            metric_type="nonfuel_revenue",
            severity=MacAlertSeverity.low,
            title="Minor alert",
            description="Minor issue",
            suggested_action="Monitor",
        )
        session.add(alert)
        session.flush()
        assert alert.resolved_at is None

    def test_issue_default_status_open_priority_three(self, session):
        _, station = self._make_region_and_station(session, "ISSUE")
        issue = MacIssue(
            station_id=station.id,
            category=MacIssueCategory.equipment,
            title="Pump fault",
            description="Pump 3 is not working",
        )
        session.add(issue)
        session.flush()
        assert issue.status == MacIssueStatus.open
        assert issue.priority == 3
        assert issue.resolved_at is None

    def test_inventory_delivery_scheduled_defaults_false(self, session):
        _, station = self._make_region_and_station(session, "INV")
        inv = MacInventory(
            station_id=station.id,
            record_date=date.today(),
            product_category=ProductCategory.coffee,
            stock_level=100,
            reorder_point=20,
            spoilage_count=2,
            stock_out_events=0,
        )
        session.add(inv)
        session.flush()
        assert inv.delivery_scheduled is False

    def test_station_defaults_no_ev_no_fresh(self, session):
        region = MacRegion(name="Defaults Region STNDEF", country="HU")
        session.add(region)
        session.flush()
        station = MacStation(
            station_code="DFLT-STNDEF-001",
            name="Station No Extras",
            city="Győr",
            region_id=region.id,
            station_type=StationType.highway,
            latitude=47.7,
            longitude=17.6,
        )
        session.add(station)
        session.flush()
        assert station.has_ev_charging is False
        assert station.has_fresh_corner is False
        assert station.num_pumps == 6
        assert station.shop_area_sqm == 80.0

    def test_chat_session_default_type(self, session):
        chat_session = MacChatSession()
        session.add(chat_session)
        session.flush()
        assert chat_session.session_type == "issue_resolution"


# ---------------------------------------------------------------------------
# Pydantic I/O model shapes
# ---------------------------------------------------------------------------


class TestPydanticModels:
    """I/O model completeness and validation."""

    def test_station_kpi_has_all_dashboard_fields(self):
        """MacStationKPI carries all fields the dashboard cards consume."""
        fields = set(MacStationKPI.model_fields.keys())
        required = {
            "station_id", "station_code", "station_name", "city", "region_name",
            "total_fuel_volume", "total_fuel_revenue", "total_fuel_margin",
            "total_nonfuel_revenue", "total_nonfuel_margin", "active_alerts",
        }
        missing = required - fields
        assert not missing, f"MacStationKPI missing fields: {missing}"

    def test_anomaly_alert_update_all_fields_optional(self):
        """Partial PATCH: both fields optional — empty update is valid."""
        update = MacAnomalyAlertUpdate()
        assert update.status is None
        assert update.resolved_at is None

    def test_anomaly_alert_update_accepts_valid_status(self):
        update = MacAnomalyAlertUpdate(status=MacAlertStatus.acknowledged)
        assert update.status == MacAlertStatus.acknowledged

    def test_chat_message_in_strips_html_tags(self):
        """LongText sanitizes HTML before the payload reaches the DB."""
        msg = MacChatMessageIn(message="<script>alert('xss')</script>Hello")
        assert "<script>" not in msg.message
        assert "Hello" in msg.message

    def test_chat_message_in_strips_null_bytes(self):
        """Null bytes are removed by the sanitizer."""
        msg = MacChatMessageIn(message="clean\x00text")
        assert "\x00" not in msg.message
        assert "cleantext" in msg.message

    def test_chat_message_in_max_length_5000(self):
        """LongText has a 5000-char ceiling."""
        with pytest.raises(ValidationError):
            MacChatMessageIn(message="x" * 5001)

    def test_chat_history_out_required_fields(self):
        fields = set(MacChatHistoryOut.model_fields.keys())
        for f in ("session_id", "session_type", "started_at", "messages"):
            assert f in fields, f"MacChatHistoryOut missing field: {f}"
