"""API tests for energy provider endpoints.

Covers:
- GET /providers             → list, shape
- GET /providers/compare     → 404 household / 404 provider / 404 no readings
                              → 200 golden path / math correctness / sort order
"""
from __future__ import annotations

from datetime import datetime, timedelta, timezone

import pytest

import innovation_factory.backend.projects.vi_home_one.models  # noqa: F401

BASE = "/api/projects/vi-home-one"


def _seed_neighborhood_and_household(session, owner="Provider User"):
    from innovation_factory.backend.projects.vi_home_one.models import VhNeighborhood, VhHousehold
    n = VhNeighborhood(name="Provider Hood", location="Frankfurt", total_households=1)
    session.add(n)
    session.commit()
    session.refresh(n)
    h = VhHousehold(neighborhood_id=n.id, owner_name=owner, address="Provider Str. 1")
    session.add(h)
    session.commit()
    session.refresh(h)
    return h


def _seed_provider(session, name="Test Provider", base=5.0, kwh=0.32, night=None, feed_in=0.082):
    from innovation_factory.backend.projects.vi_home_one.models import VhEnergyProvider
    p = VhEnergyProvider(
        name=name, base_rate_eur=base, kwh_rate_eur=kwh,
        night_rate_eur=night, feed_in_rate_eur=feed_in,
    )
    session.add(p)
    session.commit()
    session.refresh(p)
    return p


def _seed_reading(session, household_id, hours_ago=24*15, **kwargs):
    """Default: within 30 days for provider comparison."""
    from innovation_factory.backend.projects.vi_home_one.models import VhEnergyReading
    ts = datetime.now(timezone.utc) - timedelta(hours=hours_ago)
    defaults = dict(
        household_id=household_id, timestamp=ts,
        grid_import_kwh=5.0, grid_export_kwh=1.0,
        total_consumption_kwh=5.0,
    )
    defaults.update(kwargs)
    r = VhEnergyReading(**defaults)
    session.add(r)
    session.commit()
    session.refresh(r)
    return r


class TestListProviders:
    def test_empty_returns_empty_list(self, client):
        resp = client.get(f"{BASE}/providers")
        assert resp.status_code == 200
        assert isinstance(resp.json(), list)

    def test_seeded_provider_appears(self, client, session):
        _seed_provider(session, name="E.ON Test")
        resp = client.get(f"{BASE}/providers")
        assert resp.status_code == 200
        names = [p["name"] for p in resp.json()]
        assert "E.ON Test" in names

    def test_response_shape(self, client, session):
        _seed_provider(session)
        resp = client.get(f"{BASE}/providers")
        assert resp.status_code == 200
        item = resp.json()[0]
        expected = {"id", "name", "base_rate_eur", "kwh_rate_eur", "feed_in_rate_eur"}
        assert expected.issubset(set(item.keys()))

    def test_optional_night_rate_in_response(self, client, session):
        _seed_provider(session, name="Night Provider", night=0.24)
        resp = client.get(f"{BASE}/providers")
        assert resp.status_code == 200
        provider = next(p for p in resp.json() if p["name"] == "Night Provider")
        assert provider["night_rate_eur"] == 0.24


class TestCompareProviders:
    def test_unknown_household_returns_404(self, client, session):
        p = _seed_provider(session)
        resp = client.get(
            f"{BASE}/providers/compare",
            params={"household_id": 99999, "current_provider_id": p.id},
        )
        assert resp.status_code == 404

    def test_unknown_provider_returns_404(self, client, session):
        h = _seed_neighborhood_and_household(session)
        resp = client.get(
            f"{BASE}/providers/compare",
            params={"household_id": h.id, "current_provider_id": 99999},
        )
        assert resp.status_code == 404

    def test_no_readings_returns_404(self, client, session):
        h = _seed_neighborhood_and_household(session)
        p = _seed_provider(session)
        resp = client.get(
            f"{BASE}/providers/compare",
            params={"household_id": h.id, "current_provider_id": p.id},
        )
        assert resp.status_code == 404

    def test_golden_path_returns_200(self, client, session):
        h = _seed_neighborhood_and_household(session)
        p_current = _seed_provider(session, name="Current Provider", kwh=0.32)
        p_alt = _seed_provider(session, name="Alternative", kwh=0.28)
        _seed_reading(session, h.id)

        resp = client.get(
            f"{BASE}/providers/compare",
            params={"household_id": h.id, "current_provider_id": p_current.id},
        )
        assert resp.status_code == 200
        data = resp.json()
        assert data["current_provider"]["name"] == "Current Provider"
        assert isinstance(data["alternative_providers"], list)

    def test_comparison_response_shape(self, client, session):
        h = _seed_neighborhood_and_household(session)
        p = _seed_provider(session, name="Only Provider", kwh=0.32)
        _seed_reading(session, h.id)

        resp = client.get(
            f"{BASE}/providers/compare",
            params={"household_id": h.id, "current_provider_id": p.id},
        )
        assert resp.status_code == 200
        data = resp.json()
        required = {"current_provider", "current_monthly_cost_eur", "alternative_providers"}
        assert required.issubset(set(data.keys()))

    def test_cheaper_alternative_has_positive_savings(self, client, session):
        h = _seed_neighborhood_and_household(session)
        p_current = _seed_provider(session, name="Expensive", kwh=0.40, feed_in=0.08)
        p_cheap = _seed_provider(session, name="Cheap", kwh=0.20, feed_in=0.08)
        _seed_reading(session, h.id, grid_import_kwh=10.0, grid_export_kwh=0.0)

        resp = client.get(
            f"{BASE}/providers/compare",
            params={"household_id": h.id, "current_provider_id": p_current.id},
        )
        assert resp.status_code == 200
        alts = resp.json()["alternative_providers"]
        cheap_alt = next(a for a in alts if a["provider"]["name"] == "Cheap")
        assert cheap_alt["potential_savings_eur"] > 0
        assert cheap_alt["potential_savings_percent"] > 0

    def test_more_expensive_alternative_has_negative_savings(self, client, session):
        h = _seed_neighborhood_and_household(session)
        p_current = _seed_provider(session, name="Cheap Current", kwh=0.20, feed_in=0.08)
        p_expensive = _seed_provider(session, name="Expensive Alt", kwh=0.40, feed_in=0.08)
        _seed_reading(session, h.id, grid_import_kwh=10.0, grid_export_kwh=0.0)

        resp = client.get(
            f"{BASE}/providers/compare",
            params={"household_id": h.id, "current_provider_id": p_current.id},
        )
        assert resp.status_code == 200
        alts = resp.json()["alternative_providers"]
        expensive_alt = next(a for a in alts if a["provider"]["name"] == "Expensive Alt")
        assert expensive_alt["potential_savings_eur"] < 0

    def test_alternatives_sorted_by_savings_descending(self, client, session):
        """Best-saving provider should be first in the list."""
        h = _seed_neighborhood_and_household(session)
        p_current = _seed_provider(session, name="Reference", kwh=0.35, feed_in=0.08)
        _seed_provider(session, name="Midrange", kwh=0.30, feed_in=0.08)
        _seed_provider(session, name="Cheapest", kwh=0.22, feed_in=0.08)
        _seed_reading(session, h.id, grid_import_kwh=10.0, grid_export_kwh=0.0)

        resp = client.get(
            f"{BASE}/providers/compare",
            params={"household_id": h.id, "current_provider_id": p_current.id},
        )
        assert resp.status_code == 200
        alts = resp.json()["alternative_providers"]
        savings = [a["potential_savings_eur"] for a in alts]
        assert savings == sorted(savings, reverse=True)

    def test_current_provider_not_in_alternatives(self, client, session):
        h = _seed_neighborhood_and_household(session)
        p = _seed_provider(session, name="Solo Provider")
        _seed_reading(session, h.id)

        resp = client.get(
            f"{BASE}/providers/compare",
            params={"household_id": h.id, "current_provider_id": p.id},
        )
        assert resp.status_code == 200
        alt_ids = [a["provider"]["id"] for a in resp.json()["alternative_providers"]]
        assert p.id not in alt_ids


class TestCalculateMonthlyCost:
    """Unit test the _calculate_monthly_cost helper directly."""

    def test_base_rate_included(self):
        from innovation_factory.backend.projects.vi_home_one.routers.providers import _calculate_monthly_cost
        from innovation_factory.backend.projects.vi_home_one.models import VhEnergyProvider, VhEnergyReading

        provider = VhEnergyProvider(
            name="Test", base_rate_eur=10.0, kwh_rate_eur=0.30,
            feed_in_rate_eur=0.08,
        )
        cost = _calculate_monthly_cost([], provider)
        assert cost == pytest.approx(10.0)

    def test_grid_import_billed_at_kwh_rate(self):
        from innovation_factory.backend.projects.vi_home_one.routers.providers import _calculate_monthly_cost
        from innovation_factory.backend.projects.vi_home_one.models import VhEnergyProvider, VhEnergyReading

        provider = VhEnergyProvider(
            name="T", base_rate_eur=0.0, kwh_rate_eur=0.30, feed_in_rate_eur=0.0,
        )
        reading = VhEnergyReading(
            household_id=1,
            timestamp=datetime(2026, 1, 15, 12, 0, tzinfo=timezone.utc),
            grid_import_kwh=10.0,
        )
        cost = _calculate_monthly_cost([reading], provider)
        assert cost == pytest.approx(3.0)

    def test_grid_export_reduces_cost(self):
        from innovation_factory.backend.projects.vi_home_one.routers.providers import _calculate_monthly_cost
        from innovation_factory.backend.projects.vi_home_one.models import VhEnergyProvider, VhEnergyReading

        provider = VhEnergyProvider(
            name="T", base_rate_eur=0.0, kwh_rate_eur=0.30, feed_in_rate_eur=0.10,
        )
        reading = VhEnergyReading(
            household_id=1,
            timestamp=datetime(2026, 1, 15, 12, 0, tzinfo=timezone.utc),
            grid_import_kwh=10.0, grid_export_kwh=5.0,
        )
        cost = _calculate_monthly_cost([reading], provider)
        # 10 * 0.30 - 5 * 0.10 = 3.0 - 0.5 = 2.5
        assert cost == pytest.approx(2.5)

    def test_night_rate_applied_in_night_window(self):
        """Readings at 23:00 → night window (22-6) → night rate used."""
        from innovation_factory.backend.projects.vi_home_one.routers.providers import _calculate_monthly_cost
        from innovation_factory.backend.projects.vi_home_one.models import VhEnergyProvider, VhEnergyReading

        provider = VhEnergyProvider(
            name="Night", base_rate_eur=0.0, kwh_rate_eur=0.32,
            night_rate_eur=0.20, feed_in_rate_eur=0.0,
            night_start_hour=22, night_end_hour=6,
        )
        reading = VhEnergyReading(
            household_id=1,
            timestamp=datetime(2026, 1, 15, 23, 0, tzinfo=timezone.utc),
            grid_import_kwh=10.0,
        )
        cost = _calculate_monthly_cost([reading], provider)
        # Night rate applies: 10 * 0.20 = 2.0 (not 0.32)
        assert cost == pytest.approx(2.0)

    def test_day_rate_applied_outside_night_window(self):
        from innovation_factory.backend.projects.vi_home_one.routers.providers import _calculate_monthly_cost
        from innovation_factory.backend.projects.vi_home_one.models import VhEnergyProvider, VhEnergyReading

        provider = VhEnergyProvider(
            name="Day", base_rate_eur=0.0, kwh_rate_eur=0.32,
            night_rate_eur=0.20, feed_in_rate_eur=0.0,
            night_start_hour=22, night_end_hour=6,
        )
        reading = VhEnergyReading(
            household_id=1,
            timestamp=datetime(2026, 1, 15, 14, 0, tzinfo=timezone.utc),
            grid_import_kwh=10.0,
        )
        cost = _calculate_monthly_cost([reading], provider)
        # Day rate applies: 10 * 0.32 = 3.2
        assert cost == pytest.approx(3.2)
