"""API tests for energy readings endpoints.

Covers:
- GET /energy/households/{id}/readings  → list, pagination, time window
- GET /energy/households/{id}/current   → 200 / 404 / returns latest
"""
from __future__ import annotations

from datetime import datetime, timedelta, timezone

import pytest

import innovation_factory.backend.projects.vi_home_one.models  # noqa: F401

BASE = "/api/projects/vi-home-one"


def _seed_neighborhood_and_household(session):
    from innovation_factory.backend.projects.vi_home_one.models import VhNeighborhood, VhHousehold
    n = VhNeighborhood(name="Energy Test Hood", location="Berlin", total_households=1)
    session.add(n)
    session.commit()
    session.refresh(n)
    h = VhHousehold(neighborhood_id=n.id, owner_name="Energy User", address="Main St. 1")
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
        household_consumption_kwh=0.0, total_consumption_kwh=1.0,
    )
    defaults.update(kwargs)
    r = VhEnergyReading(**defaults)
    session.add(r)
    session.commit()
    session.refresh(r)
    return r


class TestGetReadings:
    def test_empty_returns_empty_list(self, client, session):
        h = _seed_neighborhood_and_household(session)
        resp = client.get(f"{BASE}/energy/households/{h.id}/readings")
        assert resp.status_code == 200
        assert resp.json() == []

    def test_readings_within_window_returned(self, client, session):
        h = _seed_neighborhood_and_household(session)
        _seed_reading(session, h.id, hours_ago=12)
        resp = client.get(f"{BASE}/energy/households/{h.id}/readings?hours=24")
        assert resp.status_code == 200
        assert len(resp.json()) == 1

    def test_reading_outside_window_excluded(self, client, session):
        h = _seed_neighborhood_and_household(session)
        _seed_reading(session, h.id, hours_ago=25)  # outside default 24h window
        resp = client.get(f"{BASE}/energy/households/{h.id}/readings?hours=24")
        assert resp.status_code == 200
        assert len(resp.json()) == 0

    def test_wider_window_includes_older_reading(self, client, session):
        h = _seed_neighborhood_and_household(session)
        _seed_reading(session, h.id, hours_ago=48)
        resp = client.get(f"{BASE}/energy/households/{h.id}/readings?hours=72")
        assert resp.status_code == 200
        assert len(resp.json()) == 1

    def test_reading_response_shape(self, client, session):
        h = _seed_neighborhood_and_household(session)
        _seed_reading(session, h.id, pv_generation_kwh=3.5)
        resp = client.get(f"{BASE}/energy/households/{h.id}/readings")
        assert resp.status_code == 200
        item = resp.json()[0]
        expected_fields = {
            "id", "household_id", "timestamp",
            "pv_generation_kwh", "battery_charge_kwh", "battery_discharge_kwh",
            "battery_level_kwh", "grid_import_kwh", "grid_export_kwh",
            "ev_consumption_kwh", "heat_pump_consumption_kwh",
            "household_consumption_kwh", "total_consumption_kwh",
        }
        assert expected_fields.issubset(set(item.keys()))

    def test_readings_ordered_newest_first(self, client, session):
        h = _seed_neighborhood_and_household(session)
        _seed_reading(session, h.id, hours_ago=3, total_consumption_kwh=1.0)
        _seed_reading(session, h.id, hours_ago=2, total_consumption_kwh=2.0)
        _seed_reading(session, h.id, hours_ago=1, total_consumption_kwh=3.0)
        resp = client.get(f"{BASE}/energy/households/{h.id}/readings")
        assert resp.status_code == 200
        readings = resp.json()
        # newest first — timestamps should be descending
        timestamps = [r["timestamp"] for r in readings]
        assert timestamps == sorted(timestamps, reverse=True)

    def test_pagination_limit(self, client, session):
        h = _seed_neighborhood_and_household(session)
        for i in range(5):
            _seed_reading(session, h.id, hours_ago=i + 1)
        resp = client.get(f"{BASE}/energy/households/{h.id}/readings?limit=3")
        assert resp.status_code == 200
        assert len(resp.json()) <= 3

    def test_values_preserved_in_response(self, client, session):
        h = _seed_neighborhood_and_household(session)
        _seed_reading(
            session, h.id,
            pv_generation_kwh=5.0,
            grid_import_kwh=1.5,
            total_consumption_kwh=6.5,
        )
        resp = client.get(f"{BASE}/energy/households/{h.id}/readings")
        assert resp.status_code == 200
        item = resp.json()[0]
        assert item["pv_generation_kwh"] == 5.0
        assert item["grid_import_kwh"] == 1.5
        assert item["total_consumption_kwh"] == 6.5


class TestGetCurrentReading:
    def test_no_readings_returns_404(self, client, session):
        h = _seed_neighborhood_and_household(session)
        resp = client.get(f"{BASE}/energy/households/{h.id}/current")
        assert resp.status_code == 404

    def test_returns_most_recent_reading(self, client, session):
        h = _seed_neighborhood_and_household(session)
        _seed_reading(session, h.id, hours_ago=5, total_consumption_kwh=1.0)
        r_latest = _seed_reading(session, h.id, hours_ago=1, total_consumption_kwh=7.7)

        resp = client.get(f"{BASE}/energy/households/{h.id}/current")
        assert resp.status_code == 200
        data = resp.json()
        assert data["total_consumption_kwh"] == 7.7
        assert data["id"] == r_latest.id

    def test_current_reading_shape(self, client, session):
        h = _seed_neighborhood_and_household(session)
        _seed_reading(session, h.id)
        resp = client.get(f"{BASE}/energy/households/{h.id}/current")
        assert resp.status_code == 200
        data = resp.json()
        assert "id" in data
        assert "household_id" in data
        assert "timestamp" in data
        assert "total_consumption_kwh" in data
