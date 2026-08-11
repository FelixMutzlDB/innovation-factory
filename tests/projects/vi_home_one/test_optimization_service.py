"""Unit tests for the optimization suggestion service.

Tests all branches of generate_optimization_suggestions():
- Returns empty list when no readings exist
- Energy-saver mode: high consumption, heat pump, solar export, standby
- Cost-saver mode: load shifting, EV charging, battery discharge, solar self-consumption
- Boundary conditions (threshold at/just-above/just-below)
"""
from __future__ import annotations

from datetime import datetime, timedelta, timezone

import pytest

import innovation_factory.backend.projects.vi_home_one.models  # noqa: F401


def _make_neighborhood(session):
    from innovation_factory.backend.projects.vi_home_one.models import VhNeighborhood
    n = VhNeighborhood(name="Opt Test Hood", location="Munich", total_households=1)
    session.add(n)
    session.flush()
    return n


def _make_household(session, n, **kwargs):
    from innovation_factory.backend.projects.vi_home_one.models import VhHousehold, OptimizationMode
    defaults = dict(
        neighborhood_id=n.id,
        owner_name="Tester",
        address="Musterstr. 1",
        optimization_mode=OptimizationMode.energy_saver,
        has_pv=False, has_battery=False, has_ev=False, has_heat_pump=False,
    )
    defaults.update(kwargs)
    h = VhHousehold(**defaults)
    session.add(h)
    session.flush()
    return h


def _make_reading(session, household_id, hours_ago=1, **kwargs):
    """Create a VhEnergyReading in the last-24h window by default."""
    from innovation_factory.backend.projects.vi_home_one.models import VhEnergyReading
    ts = datetime.now(timezone.utc) - timedelta(hours=hours_ago)
    defaults = dict(
        household_id=household_id,
        timestamp=ts,
        pv_generation_kwh=0.0,
        battery_charge_kwh=0.0,
        battery_discharge_kwh=0.0,
        battery_level_kwh=0.0,
        grid_import_kwh=0.0,
        grid_export_kwh=0.0,
        ev_consumption_kwh=0.0,
        heat_pump_consumption_kwh=0.0,
        household_consumption_kwh=0.0,
        total_consumption_kwh=0.0,
    )
    defaults.update(kwargs)
    r = VhEnergyReading(**defaults)
    session.add(r)
    session.flush()
    return r


def _make_device(session, household_id, device_type, capacity_kw=5.0):
    from innovation_factory.backend.projects.vi_home_one.models import VhEnergyDevice
    from datetime import date
    d = VhEnergyDevice(
        household_id=household_id,
        device_type=device_type,
        brand="Test Brand",
        model="Test Model",
        capacity_kw=capacity_kw,
        installation_date=date(2022, 1, 1),
    )
    session.add(d)
    session.flush()
    return d


class TestNoReadings:
    def test_empty_when_no_readings(self, session):
        from innovation_factory.backend.projects.vi_home_one.services.optimization import (
            generate_optimization_suggestions,
        )

        n = _make_neighborhood(session)
        h = _make_household(session, n)
        suggestions = generate_optimization_suggestions(h, session)
        assert suggestions == []

    def test_empty_when_all_readings_outside_24h_window(self, session):
        from innovation_factory.backend.projects.vi_home_one.services.optimization import (
            generate_optimization_suggestions,
        )

        n = _make_neighborhood(session)
        h = _make_household(session, n)
        # Reading 25h ago — outside the 24h window
        _make_reading(session, h.id, hours_ago=25, total_consumption_kwh=3.0)
        session.commit()

        suggestions = generate_optimization_suggestions(h, session)
        assert suggestions == []


class TestEnergySaverMode:
    """All energy_saver branch rules."""

    def test_high_consumption_triggers_suggestion(self, session):
        from innovation_factory.backend.projects.vi_home_one.models import OptimizationMode
        from innovation_factory.backend.projects.vi_home_one.services.optimization import (
            generate_optimization_suggestions,
        )

        n = _make_neighborhood(session)
        h = _make_household(session, n, optimization_mode=OptimizationMode.energy_saver)

        # avg = 2.0, threshold = 3.0 — create one below and two above
        _make_reading(session, h.id, hours_ago=3, total_consumption_kwh=1.0)
        _make_reading(session, h.id, hours_ago=2, total_consumption_kwh=1.0)
        _make_reading(session, h.id, hours_ago=1, total_consumption_kwh=4.0)  # 2x avg → >1.5x
        session.commit()

        suggestions = generate_optimization_suggestions(h, session)
        ids = [s.id for s in suggestions]
        assert "energy-saver-1" in ids

    def test_below_high_consumption_threshold_no_suggestion(self, session):
        from innovation_factory.backend.projects.vi_home_one.models import OptimizationMode
        from innovation_factory.backend.projects.vi_home_one.services.optimization import (
            generate_optimization_suggestions,
        )

        n = _make_neighborhood(session)
        h = _make_household(session, n, optimization_mode=OptimizationMode.energy_saver)
        # All readings equal avg — none exceed 1.5x avg
        for i in range(1, 4):
            _make_reading(session, h.id, hours_ago=i, total_consumption_kwh=2.0)
        session.commit()

        suggestions = generate_optimization_suggestions(h, session)
        assert "energy-saver-1" not in [s.id for s in suggestions]

    def test_heat_pump_high_avg_triggers_suggestion(self, session):
        from innovation_factory.backend.projects.vi_home_one.models import OptimizationMode, DeviceType
        from innovation_factory.backend.projects.vi_home_one.services.optimization import (
            generate_optimization_suggestions,
        )

        n = _make_neighborhood(session)
        h = _make_household(session, n, optimization_mode=OptimizationMode.energy_saver, has_heat_pump=True)
        _make_device(session, h.id, DeviceType.heat_pump)
        # avg heat pump > 2.0 kWh
        _make_reading(session, h.id, hours_ago=2, total_consumption_kwh=3.0, heat_pump_consumption_kwh=3.0)
        _make_reading(session, h.id, hours_ago=1, total_consumption_kwh=3.0, heat_pump_consumption_kwh=3.0)
        session.commit()

        suggestions = generate_optimization_suggestions(h, session)
        assert "energy-saver-2" in [s.id for s in suggestions]

    def test_heat_pump_below_threshold_no_suggestion(self, session):
        from innovation_factory.backend.projects.vi_home_one.models import OptimizationMode, DeviceType
        from innovation_factory.backend.projects.vi_home_one.services.optimization import (
            generate_optimization_suggestions,
        )

        n = _make_neighborhood(session)
        h = _make_household(session, n, optimization_mode=OptimizationMode.energy_saver, has_heat_pump=True)
        _make_device(session, h.id, DeviceType.heat_pump)
        # avg heat pump 1.5 kWh — below 2.0 threshold
        _make_reading(session, h.id, hours_ago=1, total_consumption_kwh=1.5, heat_pump_consumption_kwh=1.5)
        session.commit()

        suggestions = generate_optimization_suggestions(h, session)
        assert "energy-saver-2" not in [s.id for s in suggestions]

    def test_no_heat_pump_device_suppresses_hp_suggestion(self, session):
        """Heat pump suggestion requires the device to be registered."""
        from innovation_factory.backend.projects.vi_home_one.models import OptimizationMode
        from innovation_factory.backend.projects.vi_home_one.services.optimization import (
            generate_optimization_suggestions,
        )

        n = _make_neighborhood(session)
        h = _make_household(session, n, optimization_mode=OptimizationMode.energy_saver)
        # High heat pump reading but no device in DB
        _make_reading(session, h.id, hours_ago=1, total_consumption_kwh=4.0, heat_pump_consumption_kwh=4.0)
        session.commit()

        suggestions = generate_optimization_suggestions(h, session)
        assert "energy-saver-2" not in [s.id for s in suggestions]

    def test_high_solar_export_triggers_suggestion(self, session):
        from innovation_factory.backend.projects.vi_home_one.models import OptimizationMode
        from innovation_factory.backend.projects.vi_home_one.services.optimization import (
            generate_optimization_suggestions,
        )

        n = _make_neighborhood(session)
        h = _make_household(session, n, optimization_mode=OptimizationMode.energy_saver)
        # total_grid_export > 5.0
        _make_reading(session, h.id, hours_ago=1, total_consumption_kwh=1.0, grid_export_kwh=6.0)
        session.commit()

        suggestions = generate_optimization_suggestions(h, session)
        assert "energy-saver-3" in [s.id for s in suggestions]

    def test_solar_export_below_threshold_no_suggestion(self, session):
        from innovation_factory.backend.projects.vi_home_one.models import OptimizationMode
        from innovation_factory.backend.projects.vi_home_one.services.optimization import (
            generate_optimization_suggestions,
        )

        n = _make_neighborhood(session)
        h = _make_household(session, n, optimization_mode=OptimizationMode.energy_saver)
        _make_reading(session, h.id, hours_ago=1, total_consumption_kwh=1.0, grid_export_kwh=4.9)
        session.commit()

        suggestions = generate_optimization_suggestions(h, session)
        assert "energy-saver-3" not in [s.id for s in suggestions]

    def test_night_standby_triggers_suggestion(self, session):
        """A reading with hour=2 (0-6 window) and high household consumption."""
        from innovation_factory.backend.projects.vi_home_one.models import OptimizationMode
        from innovation_factory.backend.projects.vi_home_one.services.optimization import (
            generate_optimization_suggestions,
        )

        n = _make_neighborhood(session)
        h = _make_household(session, n, optimization_mode=OptimizationMode.energy_saver)

        # Build a timestamp in the 00-06 window (use today 2:00 UTC).
        now = datetime.now(timezone.utc)
        ts = now.replace(hour=2, minute=0, second=0, microsecond=0)
        if ts > now:
            ts -= timedelta(days=1)

        from innovation_factory.backend.projects.vi_home_one.models import VhEnergyReading
        r = VhEnergyReading(
            household_id=h.id, timestamp=ts,
            household_consumption_kwh=0.5,  # > 0.3 threshold
            total_consumption_kwh=0.5,
        )
        session.add(r)
        session.commit()

        suggestions = generate_optimization_suggestions(h, session)
        assert "energy-saver-4" in [s.id for s in suggestions]

    def test_savings_calculation_energy_saver_solar(self, session):
        """energy-saver-3 potential_savings_eur = export * 0.5 * (0.32 - 0.082)."""
        from innovation_factory.backend.projects.vi_home_one.models import OptimizationMode
        from innovation_factory.backend.projects.vi_home_one.services.optimization import (
            generate_optimization_suggestions,
        )

        n = _make_neighborhood(session)
        h = _make_household(session, n, optimization_mode=OptimizationMode.energy_saver)
        _make_reading(session, h.id, hours_ago=1, total_consumption_kwh=1.0, grid_export_kwh=10.0)
        session.commit()

        suggestions = generate_optimization_suggestions(h, session)
        s = next(x for x in suggestions if x.id == "energy-saver-3")
        expected_kwh = round(10.0 * 0.5, 2)
        expected_eur = round(10.0 * 0.5 * (0.32 - 0.082), 2)
        assert s.potential_savings_kwh == expected_kwh
        assert s.potential_savings_eur == expected_eur


class TestCostSaverMode:
    """All cost_saver branch rules."""

    def test_high_daytime_grid_import_triggers_suggestion(self, session):
        from innovation_factory.backend.projects.vi_home_one.models import OptimizationMode
        from innovation_factory.backend.projects.vi_home_one.services.optimization import (
            generate_optimization_suggestions,
        )

        n = _make_neighborhood(session)
        h = _make_household(session, n, optimization_mode=OptimizationMode.cost_saver)

        # Reading during expensive hours (6-22), grid import > 10 kWh total
        now = datetime.now(timezone.utc)
        ts = now.replace(hour=14, minute=0, second=0, microsecond=0)
        if ts > now:
            ts -= timedelta(days=1)

        from innovation_factory.backend.projects.vi_home_one.models import VhEnergyReading
        r = VhEnergyReading(
            household_id=h.id, timestamp=ts,
            grid_import_kwh=11.0, total_consumption_kwh=11.0,
        )
        session.add(r)
        session.commit()

        suggestions = generate_optimization_suggestions(h, session)
        assert "cost-saver-1" in [s.id for s in suggestions]

    def test_daytime_grid_import_below_threshold_no_suggestion(self, session):
        from innovation_factory.backend.projects.vi_home_one.models import OptimizationMode
        from innovation_factory.backend.projects.vi_home_one.services.optimization import (
            generate_optimization_suggestions,
        )

        n = _make_neighborhood(session)
        h = _make_household(session, n, optimization_mode=OptimizationMode.cost_saver)

        now = datetime.now(timezone.utc)
        ts = now.replace(hour=14, minute=0, second=0, microsecond=0)
        if ts > now:
            ts -= timedelta(days=1)

        from innovation_factory.backend.projects.vi_home_one.models import VhEnergyReading
        r = VhEnergyReading(
            household_id=h.id, timestamp=ts,
            grid_import_kwh=9.0, total_consumption_kwh=9.0,
        )
        session.add(r)
        session.commit()

        suggestions = generate_optimization_suggestions(h, session)
        assert "cost-saver-1" not in [s.id for s in suggestions]

    def test_ev_day_charging_triggers_suggestion(self, session):
        from innovation_factory.backend.projects.vi_home_one.models import OptimizationMode
        from innovation_factory.backend.projects.vi_home_one.services.optimization import (
            generate_optimization_suggestions,
        )

        n = _make_neighborhood(session)
        h = _make_household(session, n, optimization_mode=OptimizationMode.cost_saver, has_ev=True)

        now = datetime.now(timezone.utc)
        ts = now.replace(hour=10, minute=0, second=0, microsecond=0)
        if ts > now:
            ts -= timedelta(days=1)

        from innovation_factory.backend.projects.vi_home_one.models import VhEnergyReading
        r = VhEnergyReading(
            household_id=h.id, timestamp=ts,
            ev_consumption_kwh=5.0, total_consumption_kwh=5.0,
        )
        session.add(r)
        session.commit()

        suggestions = generate_optimization_suggestions(h, session)
        assert "cost-saver-2" in [s.id for s in suggestions]

    def test_ev_suggestion_not_shown_without_ev(self, session):
        """cost-saver-2 requires household.has_ev = True."""
        from innovation_factory.backend.projects.vi_home_one.models import OptimizationMode
        from innovation_factory.backend.projects.vi_home_one.services.optimization import (
            generate_optimization_suggestions,
        )

        n = _make_neighborhood(session)
        h = _make_household(session, n, optimization_mode=OptimizationMode.cost_saver, has_ev=False)

        now = datetime.now(timezone.utc)
        ts = now.replace(hour=10, minute=0, second=0, microsecond=0)
        if ts > now:
            ts -= timedelta(days=1)

        from innovation_factory.backend.projects.vi_home_one.models import VhEnergyReading
        r = VhEnergyReading(
            household_id=h.id, timestamp=ts,
            ev_consumption_kwh=5.0, total_consumption_kwh=5.0,
        )
        session.add(r)
        session.commit()

        suggestions = generate_optimization_suggestions(h, session)
        assert "cost-saver-2" not in [s.id for s in suggestions]

    def test_battery_low_discharge_peak_hours_triggers_suggestion(self, session):
        """cost-saver-3: battery not discharging during 18-21 hours."""
        from innovation_factory.backend.projects.vi_home_one.models import OptimizationMode
        from innovation_factory.backend.projects.vi_home_one.services.optimization import (
            generate_optimization_suggestions,
        )

        n = _make_neighborhood(session)
        h = _make_household(session, n, optimization_mode=OptimizationMode.cost_saver, has_battery=True)

        now = datetime.now(timezone.utc)
        ts = now.replace(hour=19, minute=0, second=0, microsecond=0)
        if ts > now:
            ts -= timedelta(days=1)

        from innovation_factory.backend.projects.vi_home_one.models import VhEnergyReading
        # discharge < 0.5 during peak hours
        r = VhEnergyReading(
            household_id=h.id, timestamp=ts,
            battery_discharge_kwh=0.1, total_consumption_kwh=2.0,
        )
        session.add(r)
        session.commit()

        suggestions = generate_optimization_suggestions(h, session)
        assert "cost-saver-3" in [s.id for s in suggestions]

    def test_battery_suggestion_not_shown_without_battery(self, session):
        from innovation_factory.backend.projects.vi_home_one.models import OptimizationMode
        from innovation_factory.backend.projects.vi_home_one.services.optimization import (
            generate_optimization_suggestions,
        )

        n = _make_neighborhood(session)
        h = _make_household(session, n, optimization_mode=OptimizationMode.cost_saver, has_battery=False)

        now = datetime.now(timezone.utc)
        ts = now.replace(hour=19, minute=0, second=0, microsecond=0)
        if ts > now:
            ts -= timedelta(days=1)

        from innovation_factory.backend.projects.vi_home_one.models import VhEnergyReading
        r = VhEnergyReading(
            household_id=h.id, timestamp=ts,
            battery_discharge_kwh=0.0, total_consumption_kwh=2.0,
        )
        session.add(r)
        session.commit()

        suggestions = generate_optimization_suggestions(h, session)
        assert "cost-saver-3" not in [s.id for s in suggestions]

    def test_pv_high_export_cost_saver_triggers_suggestion(self, session):
        from innovation_factory.backend.projects.vi_home_one.models import OptimizationMode
        from innovation_factory.backend.projects.vi_home_one.services.optimization import (
            generate_optimization_suggestions,
        )

        n = _make_neighborhood(session)
        h = _make_household(session, n, optimization_mode=OptimizationMode.cost_saver, has_pv=True)
        _make_reading(session, h.id, hours_ago=1, total_consumption_kwh=1.0, grid_export_kwh=8.0)
        session.commit()

        suggestions = generate_optimization_suggestions(h, session)
        assert "cost-saver-4" in [s.id for s in suggestions]

    def test_pv_suggestion_not_shown_without_pv(self, session):
        from innovation_factory.backend.projects.vi_home_one.models import OptimizationMode
        from innovation_factory.backend.projects.vi_home_one.services.optimization import (
            generate_optimization_suggestions,
        )

        n = _make_neighborhood(session)
        h = _make_household(session, n, optimization_mode=OptimizationMode.cost_saver, has_pv=False)
        _make_reading(session, h.id, hours_ago=1, total_consumption_kwh=1.0, grid_export_kwh=8.0)
        session.commit()

        suggestions = generate_optimization_suggestions(h, session)
        assert "cost-saver-4" not in [s.id for s in suggestions]

    def test_ev_savings_calculation(self, session):
        """cost-saver-2 savings = day_charging_kwh * (0.32 - 0.24)."""
        from innovation_factory.backend.projects.vi_home_one.models import OptimizationMode
        from innovation_factory.backend.projects.vi_home_one.services.optimization import (
            generate_optimization_suggestions,
        )

        n = _make_neighborhood(session)
        h = _make_household(session, n, optimization_mode=OptimizationMode.cost_saver, has_ev=True)

        now = datetime.now(timezone.utc)
        ts = now.replace(hour=10, minute=0, second=0, microsecond=0)
        if ts > now:
            ts -= timedelta(days=1)

        from innovation_factory.backend.projects.vi_home_one.models import VhEnergyReading
        r = VhEnergyReading(
            household_id=h.id, timestamp=ts,
            ev_consumption_kwh=20.0, total_consumption_kwh=20.0,
        )
        session.add(r)
        session.commit()

        suggestions = generate_optimization_suggestions(h, session)
        s = next(x for x in suggestions if x.id == "cost-saver-2")
        expected_eur = round(20.0 * (0.32 - 0.24), 2)
        assert s.potential_savings_eur == expected_eur
        # cost-saver mode doesn't set kwh savings for this rule
        assert s.potential_savings_kwh is None


class TestSuggestionOutputShape:
    """All suggestions must have id, category, title, description."""

    def test_energy_saver_suggestion_has_required_fields(self, session):
        from innovation_factory.backend.projects.vi_home_one.models import OptimizationMode
        from innovation_factory.backend.projects.vi_home_one.services.optimization import (
            generate_optimization_suggestions,
        )

        n = _make_neighborhood(session)
        h = _make_household(session, n, optimization_mode=OptimizationMode.energy_saver)
        _make_reading(session, h.id, hours_ago=1, total_consumption_kwh=1.0, grid_export_kwh=6.0)
        session.commit()

        suggestions = generate_optimization_suggestions(h, session)
        for s in suggestions:
            assert s.id
            assert s.category
            assert s.title
            assert s.description
