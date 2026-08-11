"""API tests for neighborhood endpoints.

Covers:
- GET /neighborhoods  → 200, empty list
- GET /neighborhoods  → 200 with seeded data
- GET /neighborhoods/{id}/summary → 404 for unknown
- GET /neighborhoods/{id}/summary → 200 golden path with households
- Neighborhood summary aggregates consumption/generation correctly
"""
from __future__ import annotations

from datetime import datetime, timedelta, timezone

import pytest

import innovation_factory.backend.projects.vi_home_one.models  # noqa: F401

BASE = "/api/projects/vi-home-one"


def _seed_neighborhood(session, name="Test Hood", location="Munich", total=2):
    from innovation_factory.backend.projects.vi_home_one.models import VhNeighborhood
    n = VhNeighborhood(name=name, location=location, total_households=total)
    session.add(n)
    session.commit()
    session.refresh(n)
    return n


def _seed_household(session, neighborhood_id, owner="Owner", address="Str. 1"):
    from innovation_factory.backend.projects.vi_home_one.models import VhHousehold
    h = VhHousehold(
        neighborhood_id=neighborhood_id,
        owner_name=owner,
        address=address,
        has_pv=True,
    )
    session.add(h)
    session.commit()
    session.refresh(h)
    return h


def _seed_reading(session, household_id, hours_ago=1, **kwargs):
    from innovation_factory.backend.projects.vi_home_one.models import VhEnergyReading
    ts = datetime.now(timezone.utc) - timedelta(hours=hours_ago)
    defaults = dict(
        household_id=household_id, timestamp=ts,
        pv_generation_kwh=2.0, total_consumption_kwh=3.0,
    )
    defaults.update(kwargs)
    r = VhEnergyReading(**defaults)
    session.add(r)
    session.commit()
    session.refresh(r)
    return r


class TestListNeighborhoods:
    def test_empty_list_returns_200(self, client):
        resp = client.get(f"{BASE}/neighborhoods")
        assert resp.status_code == 200
        assert isinstance(resp.json(), list)

    def test_seeded_neighborhood_appears_in_list(self, client, session):
        n = _seed_neighborhood(session, name="Visible Hood", location="Hamburg")
        resp = client.get(f"{BASE}/neighborhoods")
        assert resp.status_code == 200
        names = [item["name"] for item in resp.json()]
        assert "Visible Hood" in names

    def test_response_shape(self, client, session):
        _seed_neighborhood(session)
        resp = client.get(f"{BASE}/neighborhoods")
        assert resp.status_code == 200
        for item in resp.json():
            assert "id" in item
            assert "name" in item
            assert "location" in item
            assert "total_households" in item
            assert "created_at" in item


class TestNeighborhoodSummary:
    def test_unknown_id_returns_404(self, client):
        resp = client.get(f"{BASE}/neighborhoods/99999/summary")
        assert resp.status_code == 404

    def test_empty_neighborhood_returns_zero_aggregates(self, client, session):
        n = _seed_neighborhood(session, name="Empty Hood", total=0)
        resp = client.get(f"{BASE}/neighborhoods/{n.id}/summary")
        assert resp.status_code == 200
        data = resp.json()
        assert data["total_consumption_kwh"] == 0.0
        assert data["total_generation_kwh"] == 0.0
        assert data["households"] == []

    def test_summary_aggregates_household_readings(self, client, session):
        n = _seed_neighborhood(session, name="Active Hood", total=1)
        h = _seed_household(session, n.id, owner="Active Owner")
        # Two readings within 24h
        _seed_reading(session, h.id, hours_ago=2, pv_generation_kwh=3.0, total_consumption_kwh=2.5)
        _seed_reading(session, h.id, hours_ago=1, pv_generation_kwh=4.0, total_consumption_kwh=3.0)

        resp = client.get(f"{BASE}/neighborhoods/{n.id}/summary")
        assert resp.status_code == 200
        data = resp.json()
        assert data["total_consumption_kwh"] == pytest.approx(5.5, abs=0.01)
        assert data["total_generation_kwh"] == pytest.approx(7.0, abs=0.01)

    def test_summary_response_shape(self, client, session):
        n = _seed_neighborhood(session, name="Shape Hood")
        resp = client.get(f"{BASE}/neighborhoods/{n.id}/summary")
        assert resp.status_code == 200
        data = resp.json()
        required = {
            "id", "name", "location", "total_households",
            "total_consumption_kwh", "total_generation_kwh",
            "total_storage_capacity_kwh", "households",
        }
        assert required.issubset(set(data.keys()))

    def test_household_summary_shape_in_neighborhood(self, client, session):
        n = _seed_neighborhood(session, total=1)
        h = _seed_household(session, n.id, owner="HH Owner")
        _seed_reading(session, h.id)

        resp = client.get(f"{BASE}/neighborhoods/{n.id}/summary")
        assert resp.status_code == 200
        data = resp.json()
        households = data["households"]
        assert len(households) == 1
        hh = households[0]
        assert "id" in hh
        assert "owner_name" in hh
        assert "current_consumption_kw" in hh
        assert "current_generation_kw" in hh
        assert "battery_level_percent" in hh

    def test_battery_level_zero_when_no_battery_device(self, client, session):
        n = _seed_neighborhood(session, total=1)
        h = _seed_household(session, n.id)
        _seed_reading(session, h.id, battery_level_kwh=5.0)

        resp = client.get(f"{BASE}/neighborhoods/{n.id}/summary")
        assert resp.status_code == 200
        hh = resp.json()["households"][0]
        # No battery device registered → capacity = 0 → battery_level_percent = 0
        assert hh["battery_level_percent"] == 0.0
