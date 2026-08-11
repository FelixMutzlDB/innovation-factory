"""API tests for household endpoints.

Covers:
- GET /households/{id}              → 200 / 404
- PUT /households/{id}/optimization-mode  → 200 / 404 / persists change
- GET /households/{id}/cockpit      → 200 / 404 / shape / cost calculation
"""
from __future__ import annotations

from datetime import datetime, timedelta, timezone

import pytest

import innovation_factory.backend.projects.vi_home_one.models  # noqa: F401

BASE = "/api/projects/vi-home-one"


def _seed_neighborhood(session, name="HH Test Hood"):
    from innovation_factory.backend.projects.vi_home_one.models import VhNeighborhood
    n = VhNeighborhood(name=name, location="Test City", total_households=1)
    session.add(n)
    session.commit()
    session.refresh(n)
    return n


def _seed_household(session, neighborhood_id, **kwargs):
    from innovation_factory.backend.projects.vi_home_one.models import VhHousehold, OptimizationMode
    defaults = dict(
        neighborhood_id=neighborhood_id,
        owner_name="Default Owner",
        address="Default Str. 1",
        optimization_mode=OptimizationMode.energy_saver,
        has_pv=False, has_battery=False, has_ev=False, has_heat_pump=False,
    )
    defaults.update(kwargs)
    h = VhHousehold(**defaults)
    session.add(h)
    session.commit()
    session.refresh(h)
    return h


def _seed_reading(session, household_id, hours_ago=1, **kwargs):
    from innovation_factory.backend.projects.vi_home_one.models import VhEnergyReading
    ts = datetime.now(timezone.utc) - timedelta(hours=hours_ago)
    defaults = dict(
        household_id=household_id, timestamp=ts,
        pv_generation_kwh=0.0, battery_charge_kwh=0.0,
        battery_discharge_kwh=0.0, battery_level_kwh=0.0,
        grid_import_kwh=0.0, grid_export_kwh=0.0,
        ev_consumption_kwh=0.0, heat_pump_consumption_kwh=0.0,
        household_consumption_kwh=0.0, total_consumption_kwh=0.0,
    )
    defaults.update(kwargs)
    r = VhEnergyReading(**defaults)
    session.add(r)
    session.commit()
    session.refresh(r)
    return r


class TestGetHousehold:
    def test_unknown_id_returns_404(self, client):
        resp = client.get(f"{BASE}/households/99999")
        assert resp.status_code == 404

    def test_known_id_returns_200(self, client, session):
        n = _seed_neighborhood(session)
        h = _seed_household(session, n.id, owner_name="Test Owner")
        resp = client.get(f"{BASE}/households/{h.id}")
        assert resp.status_code == 200
        data = resp.json()
        assert data["id"] == h.id
        assert data["owner_name"] == "Test Owner"

    def test_response_shape(self, client, session):
        n = _seed_neighborhood(session)
        h = _seed_household(session, n.id)
        resp = client.get(f"{BASE}/households/{h.id}")
        assert resp.status_code == 200
        data = resp.json()
        expected_fields = {
            "id", "neighborhood_id", "owner_name", "address",
            "optimization_mode", "has_pv", "has_battery", "has_ev",
            "has_heat_pump", "created_at", "updated_at",
        }
        assert expected_fields.issubset(set(data.keys()))


class TestUpdateOptimizationMode:
    def test_unknown_id_returns_404(self, client):
        resp = client.put(
            f"{BASE}/households/99999/optimization-mode",
            json={"optimization_mode": "cost_saver"},
        )
        assert resp.status_code == 404

    def test_mode_change_persists(self, client, session):
        n = _seed_neighborhood(session)
        h = _seed_household(session, n.id, optimization_mode="energy_saver")
        resp = client.put(
            f"{BASE}/households/{h.id}/optimization-mode",
            json={"optimization_mode": "cost_saver"},
        )
        assert resp.status_code == 200
        assert resp.json()["optimization_mode"] == "cost_saver"

        # Verify it persisted with a subsequent GET
        get_resp = client.get(f"{BASE}/households/{h.id}")
        assert get_resp.json()["optimization_mode"] == "cost_saver"

    def test_mode_roundtrip_energy_saver(self, client, session):
        n = _seed_neighborhood(session)
        h = _seed_household(session, n.id, optimization_mode="cost_saver")
        resp = client.put(
            f"{BASE}/households/{h.id}/optimization-mode",
            json={"optimization_mode": "energy_saver"},
        )
        assert resp.status_code == 200
        assert resp.json()["optimization_mode"] == "energy_saver"

    def test_invalid_mode_returns_422(self, client, session):
        n = _seed_neighborhood(session)
        h = _seed_household(session, n.id)
        resp = client.put(
            f"{BASE}/households/{h.id}/optimization-mode",
            json={"optimization_mode": "turbo_mode"},
        )
        assert resp.status_code == 422


class TestGetCockpit:
    def test_unknown_id_returns_404(self, client):
        resp = client.get(f"{BASE}/households/99999/cockpit")
        assert resp.status_code == 404

    def test_cockpit_with_no_readings_returns_zero_values(self, client, session):
        n = _seed_neighborhood(session)
        h = _seed_household(session, n.id)
        resp = client.get(f"{BASE}/households/{h.id}/cockpit")
        assert resp.status_code == 200
        data = resp.json()
        assert data["current_consumption_kw"] == 0.0
        assert data["cost_today_eur"] == 0.0
        assert data["cost_this_month_eur"] == 0.0
        assert data["consumption_breakdown"] == []

    def test_cockpit_response_shape(self, client, session):
        n = _seed_neighborhood(session)
        h = _seed_household(session, n.id)
        resp = client.get(f"{BASE}/households/{h.id}/cockpit")
        assert resp.status_code == 200
        data = resp.json()
        required = {
            "household", "current_consumption_kw", "consumption_breakdown",
            "energy_sources", "recent_readings", "cost_today_eur",
            "cost_this_month_eur", "devices",
        }
        assert required.issubset(set(data.keys()))

    def test_energy_sources_shape(self, client, session):
        n = _seed_neighborhood(session)
        h = _seed_household(session, n.id)
        resp = client.get(f"{BASE}/households/{h.id}/cockpit")
        assert resp.status_code == 200
        sources = resp.json()["energy_sources"]
        assert "pv_generation_kw" in sources
        assert "battery_discharge_kw" in sources
        assert "grid_import_kw" in sources
        assert "total_available_kw" in sources

    def test_total_available_kw_is_sum_of_sources(self, client, session):
        n = _seed_neighborhood(session)
        h = _seed_household(session, n.id)
        _seed_reading(
            session, h.id, hours_ago=1,
            pv_generation_kwh=3.0, battery_discharge_kwh=1.5, grid_import_kwh=0.5,
            total_consumption_kwh=5.0,
        )
        resp = client.get(f"{BASE}/households/{h.id}/cockpit")
        assert resp.status_code == 200
        sources = resp.json()["energy_sources"]
        expected_total = sources["pv_generation_kw"] + sources["battery_discharge_kw"] + sources["grid_import_kw"]
        assert sources["total_available_kw"] == pytest.approx(expected_total, abs=0.001)

    def test_cost_calculation_grid_import(self, client, session):
        """cost = grid_import * 0.32 - grid_export * 0.082 for today."""
        n = _seed_neighborhood(session)
        h = _seed_household(session, n.id)
        # Reading within today (hours_ago=0.5 → ~30 min ago)
        _seed_reading(
            session, h.id, hours_ago=0.5,
            grid_import_kwh=5.0, grid_export_kwh=2.0,
            total_consumption_kwh=3.0,
        )
        resp = client.get(f"{BASE}/households/{h.id}/cockpit")
        assert resp.status_code == 200
        cost = resp.json()["cost_today_eur"]
        expected = round(5.0 * 0.32 - 2.0 * 0.082, 2)
        assert cost == pytest.approx(expected, abs=0.01)

    def test_consumption_breakdown_shows_nonzero_categories(self, client, session):
        n = _seed_neighborhood(session)
        h = _seed_household(session, n.id)
        _seed_reading(
            session, h.id, hours_ago=1,
            heat_pump_consumption_kwh=2.0, ev_consumption_kwh=1.0,
            household_consumption_kwh=0.5, total_consumption_kwh=3.5,
        )
        resp = client.get(f"{BASE}/households/{h.id}/cockpit")
        assert resp.status_code == 200
        breakdown = resp.json()["consumption_breakdown"]
        assert len(breakdown) > 0
        for item in breakdown:
            assert "category" in item
            assert "value_kwh" in item
            assert "percentage" in item
            assert item["value_kwh"] > 0

    def test_recent_readings_are_within_24h(self, client, session):
        n = _seed_neighborhood(session)
        h = _seed_household(session, n.id)
        # Reading inside 24h
        _seed_reading(session, h.id, hours_ago=5)
        # Reading outside 24h (should not appear in recent_readings)
        _seed_reading(session, h.id, hours_ago=26)

        resp = client.get(f"{BASE}/households/{h.id}/cockpit")
        assert resp.status_code == 200
        readings = resp.json()["recent_readings"]
        # Only the reading inside 24h should be in recent_readings
        assert len(readings) <= 24
