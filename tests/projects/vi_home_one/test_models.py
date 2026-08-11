"""Model structure tests for vi_home_one.

Checks:
- All enum values are present and correctly typed
- 3-model pattern: table + Out (+ In where applicable)
- Field presence for the cockpit and ticket output models
- Pydantic serialization round-trips for the output models
"""
from __future__ import annotations

from datetime import date, datetime, timezone

import pytest

import innovation_factory.backend.projects.vi_home_one.models  # noqa: F401
from innovation_factory.backend.projects.vi_home_one.models import (
    AlertSeverity,
    ConsumptionCategory,
    DeviceType,
    OptimizationMode,
    VhChatRole,
    VhTicketStatus,
)


# ---------------------------------------------------------------------------
# Enums
# ---------------------------------------------------------------------------

class TestEnumValues:
    def test_device_type_values(self):
        assert DeviceType.heat_pump == "heat_pump"
        assert DeviceType.pv_system == "pv_system"
        assert DeviceType.battery == "battery"
        assert DeviceType.ev == "ev"
        assert DeviceType.grid_meter == "grid_meter"

    def test_optimization_mode_values(self):
        assert OptimizationMode.energy_saver == "energy_saver"
        assert OptimizationMode.cost_saver == "cost_saver"

    def test_ticket_status_lifecycle(self):
        statuses = {s.value for s in VhTicketStatus}
        assert statuses == {"new", "in_progress", "resolved", "escalated"}

    def test_alert_severity_ordering(self):
        """All four severity levels exist and are distinct strings."""
        assert len({s.value for s in AlertSeverity}) == 4
        assert AlertSeverity.critical == "critical"
        assert AlertSeverity.low == "low"

    def test_consumption_category_values(self):
        categories = {c.value for c in ConsumptionCategory}
        assert "household_appliances" in categories
        assert "ev_charging" in categories
        assert "climate_control" in categories

    def test_chat_role_values(self):
        assert VhChatRole.user == "user"
        assert VhChatRole.assistant == "assistant"
        assert VhChatRole.system == "system"


# ---------------------------------------------------------------------------
# 3-model pattern: table + Out (+ In where applicable)
# ---------------------------------------------------------------------------

class TestThreeModelPattern:
    """Every API-surfaced entity must follow DB / Out / In where write side exists."""

    @pytest.mark.parametrize("table, out, in_model", [
        ("VhNeighborhood", "VhNeighborhoodOut", None),
        ("VhHousehold", "VhHouseholdOut", None),
        ("VhEnergyDevice", "VhEnergyDeviceOut", None),
        ("VhEnergyReading", "VhEnergyReadingOut", None),
        ("VhEnergyProvider", "VhEnergyProviderOut", None),
        ("VhMaintenanceAlert", "VhMaintenanceAlertOut", None),
        ("VhTicket", "VhTicketOut", "VhTicketIn"),
    ])
    def test_model_classes_exist(self, table, out, in_model):
        import innovation_factory.backend.projects.vi_home_one.models as m
        assert hasattr(m, table), f"DB model {table} missing"
        assert hasattr(m, out), f"Out model {out} missing"
        if in_model:
            assert hasattr(m, in_model), f"In model {in_model} missing"


# ---------------------------------------------------------------------------
# Field presence on composite output models
# ---------------------------------------------------------------------------

class TestCockpitOutShape:
    """VhHouseholdCockpitOut must carry all fields the cockpit cards consume."""

    def test_cockpit_out_has_required_fields(self):
        from innovation_factory.backend.projects.vi_home_one.models import VhHouseholdCockpitOut
        fields = set(VhHouseholdCockpitOut.model_fields.keys())
        required = {
            "household", "current_consumption_kw", "consumption_breakdown",
            "energy_sources", "recent_readings", "cost_today_eur",
            "cost_this_month_eur", "devices",
        }
        missing = required - fields
        assert not missing, f"VhHouseholdCockpitOut missing fields: {missing}"


class TestNeighborhoodSummaryOutShape:
    def test_summary_out_has_households_list(self):
        from innovation_factory.backend.projects.vi_home_one.models import VhNeighborhoodSummaryOut
        fields = set(VhNeighborhoodSummaryOut.model_fields.keys())
        assert "households" in fields
        assert "total_consumption_kwh" in fields
        assert "total_generation_kwh" in fields


class TestTicketOutShape:
    def test_ticket_out_has_resolved_at(self):
        from innovation_factory.backend.projects.vi_home_one.models import VhTicketOut
        fields = set(VhTicketOut.model_fields.keys())
        assert "resolved_at" in fields
        assert "status" in fields
        assert "resolution_notes" in fields


# ---------------------------------------------------------------------------
# Pydantic serialization round-trips
# ---------------------------------------------------------------------------

class TestSerializationRoundTrips:
    def test_energy_reading_out_serializes(self):
        from innovation_factory.backend.projects.vi_home_one.models import VhEnergyReadingOut

        now = datetime.now(timezone.utc)
        r = VhEnergyReadingOut(
            id=1, household_id=10, timestamp=now,
            pv_generation_kwh=3.5, battery_charge_kwh=0.5,
            battery_discharge_kwh=0.0, battery_level_kwh=5.0,
            grid_import_kwh=1.2, grid_export_kwh=0.0,
            ev_consumption_kwh=2.0, heat_pump_consumption_kwh=1.5,
            household_consumption_kwh=0.8, total_consumption_kwh=4.3,
        )
        data = r.model_dump()
        assert data["pv_generation_kwh"] == 3.5
        assert data["total_consumption_kwh"] == 4.3
        # Round-trip
        r2 = VhEnergyReadingOut(**data)
        assert r2.id == r.id

    def test_ticket_in_serializes(self):
        from innovation_factory.backend.projects.vi_home_one.models import VhTicketIn

        t = VhTicketIn(title="Heat pump not working", description="No heating since yesterday")
        assert t.priority is None
        assert t.device_id is None
        d = t.model_dump()
        t2 = VhTicketIn(**d)
        assert t2.title == t.title

    def test_optimization_mode_update_serializes(self):
        from innovation_factory.backend.projects.vi_home_one.models import VhOptimizationModeUpdate

        u = VhOptimizationModeUpdate(optimization_mode=OptimizationMode.cost_saver)
        assert u.model_dump()["optimization_mode"] == "cost_saver"

    def test_provider_out_optional_night_rate(self):
        from innovation_factory.backend.projects.vi_home_one.models import VhEnergyProviderOut

        p = VhEnergyProviderOut(
            id=1, name="Test Provider", base_rate_eur=5.0,
            kwh_rate_eur=0.32, night_rate_eur=None, feed_in_rate_eur=0.082,
        )
        assert p.night_rate_eur is None
        data = p.model_dump()
        p2 = VhEnergyProviderOut(**data)
        assert p2.name == "Test Provider"

    def test_maintenance_alert_acknowledge_model(self):
        from innovation_factory.backend.projects.vi_home_one.models import VhMaintenanceAlertAcknowledge

        a = VhMaintenanceAlertAcknowledge(is_acknowledged=True)
        assert a.is_acknowledged is True
        a2 = VhMaintenanceAlertAcknowledge(is_acknowledged=False)
        assert a2.is_acknowledged is False


# ---------------------------------------------------------------------------
# DB model defaults
# ---------------------------------------------------------------------------

class TestModelDefaults:
    def test_household_default_optimization_mode(self):
        from innovation_factory.backend.projects.vi_home_one.models import VhHousehold

        h = VhHousehold(
            neighborhood_id=1,
            owner_name="Test Owner",
            address="Test Street 1",
        )
        assert h.optimization_mode == OptimizationMode.energy_saver

    def test_household_default_boolean_flags(self):
        from innovation_factory.backend.projects.vi_home_one.models import VhHousehold

        h = VhHousehold(neighborhood_id=1, owner_name="x", address="y")
        assert h.has_pv is False
        assert h.has_battery is False
        assert h.has_ev is False
        assert h.has_heat_pump is False

    def test_ticket_default_status(self):
        from innovation_factory.backend.projects.vi_home_one.models import VhTicket

        t = VhTicket(household_id=1, title="x", description="y")
        assert t.status == VhTicketStatus.new

    def test_maintenance_alert_default_unacknowledged(self):
        from innovation_factory.backend.projects.vi_home_one.models import VhMaintenanceAlert

        a = VhMaintenanceAlert(
            device_id=1, alert_type="filter_dirty",
            severity=AlertSeverity.medium, message="Check filter",
        )
        assert a.is_acknowledged is False
        assert a.acknowledged_at is None

    def test_energy_reading_defaults_to_zero(self):
        from innovation_factory.backend.projects.vi_home_one.models import VhEnergyReading

        r = VhEnergyReading(household_id=1, timestamp=datetime.now(timezone.utc))
        assert r.pv_generation_kwh == 0.0
        assert r.total_consumption_kwh == 0.0
        assert r.battery_level_kwh == 0.0


# ---------------------------------------------------------------------------
# DB persistence smoke tests (uses session fixture)
# ---------------------------------------------------------------------------

class TestDbPersistence:
    def test_neighborhood_persists(self, session):
        from innovation_factory.backend.projects.vi_home_one.models import VhNeighborhood

        n = VhNeighborhood(name="Green Quarter", location="Berlin", total_households=12)
        session.add(n)
        session.flush()
        assert n.id is not None

    def test_household_foreign_key(self, session):
        from innovation_factory.backend.projects.vi_home_one.models import VhHousehold, VhNeighborhood

        n = VhNeighborhood(name="Solar Alley", location="Hamburg", total_households=5)
        session.add(n)
        session.flush()

        h = VhHousehold(
            neighborhood_id=n.id,
            owner_name="Anna Schmidt",
            address="Hauptstr. 7",
            has_pv=True,
        )
        session.add(h)
        session.flush()
        assert h.neighborhood_id == n.id

    def test_energy_device_persists(self, session):
        from innovation_factory.backend.projects.vi_home_one.models import (
            VhEnergyDevice, VhHousehold, VhNeighborhood,
        )

        n = VhNeighborhood(name="PV Park", location="Munich", total_households=3)
        session.add(n)
        session.flush()
        h = VhHousehold(neighborhood_id=n.id, owner_name="Bob", address="Str. 1")
        session.add(h)
        session.flush()

        d = VhEnergyDevice(
            household_id=h.id,
            device_type=DeviceType.pv_system,
            brand="Viessmann",
            model="Vitovolt 300",
            capacity_kw=8.5,
            installation_date=date(2023, 6, 1),
        )
        session.add(d)
        session.flush()
        assert d.id is not None
        assert d.capacity_kw == 8.5

    def test_ticket_with_optional_device(self, session):
        from innovation_factory.backend.projects.vi_home_one.models import (
            VhTicket, VhHousehold, VhNeighborhood,
        )

        n = VhNeighborhood(name="Tix Quarter", location="Cologne", total_households=8)
        session.add(n)
        session.flush()
        h = VhHousehold(neighborhood_id=n.id, owner_name="Carl", address="Weg 2")
        session.add(h)
        session.flush()

        t = VhTicket(
            household_id=h.id,
            title="Battery not charging",
            description="No charge for 3 days",
            priority="high",
        )
        session.add(t)
        session.flush()
        assert t.id is not None
        assert t.status == VhTicketStatus.new
        assert t.device_id is None
