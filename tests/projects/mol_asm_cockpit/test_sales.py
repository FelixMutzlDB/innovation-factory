"""Tests for fuel sales, non-fuel sales, and loyalty metric endpoints.

Covers: list with filters, days cutoff, field shapes.
"""
from __future__ import annotations

from datetime import date, timedelta

import pytest

from ._helpers import (
    _seeding_session,
    seed_fuel_sale,
    seed_nonfuel_sale,
    seed_region_and_station,
)

BASE = "/api/projects/mol-asm-cockpit"


def _seed_loyalty(client, station_id: int, month: date) -> int:
    from innovation_factory.backend.projects.mol_asm_cockpit.models import MacLoyaltyMetric

    with _seeding_session(client) as session:
        metric = MacLoyaltyMetric(
            station_id=station_id,
            month=month,
            active_members=500,
            new_signups=40,
            points_redeemed=12000,
            loyalty_revenue_share=0.32,
        )
        session.add(metric)
        session.flush()
        assert metric.id is not None
        return metric.id


# ---------------------------------------------------------------------------
# Fuel sales
# ---------------------------------------------------------------------------


class TestFuelSales:
    def test_returns_200(self, client):
        resp = client.get(f"{BASE}/sales/fuel")
        assert resp.status_code == 200
        assert isinstance(resp.json(), list)

    def test_seeded_sale_appears(self, client):
        _, station_id = seed_region_and_station(client, "FUEL-A")
        sale_id = seed_fuel_sale(
            client, station_id, sale_date=date.today(), revenue=200.0
        )
        resp = client.get(f"{BASE}/sales/fuel?station_id={station_id}")
        assert resp.status_code == 200
        ids = [s["id"] for s in resp.json()]
        assert sale_id in ids

    def test_filter_by_station_id(self, client):
        _, station_id = seed_region_and_station(client, "FUEL-B")
        sale_id = seed_fuel_sale(client, station_id, sale_date=date.today())
        resp = client.get(f"{BASE}/sales/fuel?station_id={station_id}")
        assert resp.status_code == 200
        data = resp.json()
        assert all(s["station_id"] == station_id for s in data)
        assert any(s["id"] == sale_id for s in data)

    def test_filter_by_fuel_type(self, client):
        _, station_id = seed_region_and_station(client, "FUEL-C")
        diesel_id = seed_fuel_sale(
            client, station_id, sale_date=date.today(), fuel_type="diesel"
        )
        lpg_id = seed_fuel_sale(
            client, station_id, sale_date=date.today(), fuel_type="lpg"
        )
        resp = client.get(
            f"{BASE}/sales/fuel?station_id={station_id}&fuel_type=diesel"
        )
        assert resp.status_code == 200
        ids = [s["id"] for s in resp.json()]
        assert diesel_id in ids
        assert lpg_id not in ids

    def test_days_cutoff_excludes_old_record(self, client):
        """A sale from 400 days ago must not appear in a 30-day query."""
        _, station_id = seed_region_and_station(client, "FUEL-D")
        old_sale_id = seed_fuel_sale(
            client,
            station_id,
            sale_date=date.today() - timedelta(days=400),
        )
        resp = client.get(
            f"{BASE}/sales/fuel?station_id={station_id}&days=30"
        )
        assert resp.status_code == 200
        ids = [s["id"] for s in resp.json()]
        assert old_sale_id not in ids

    def test_recent_sale_within_days_window_appears(self, client):
        """A sale from yesterday must appear in a 7-day query."""
        _, station_id = seed_region_and_station(client, "FUEL-E")
        recent_id = seed_fuel_sale(
            client,
            station_id,
            sale_date=date.today() - timedelta(days=1),
        )
        resp = client.get(
            f"{BASE}/sales/fuel?station_id={station_id}&days=7"
        )
        assert resp.status_code == 200
        ids = [s["id"] for s in resp.json()]
        assert recent_id in ids

    def test_fuel_sale_has_required_fields(self, client):
        _, station_id = seed_region_and_station(client, "FUEL-F")
        seed_fuel_sale(client, station_id, sale_date=date.today())
        resp = client.get(f"{BASE}/sales/fuel?station_id={station_id}")
        assert resp.status_code == 200
        rows = resp.json()
        assert len(rows) >= 1
        row = rows[0]
        for field in (
            "id", "station_id", "sale_date", "fuel_type",
            "volume_liters", "revenue", "unit_price", "margin",
        ):
            assert field in row, f"Fuel sale missing field: {field}"

    def test_limit_too_low_returns_422(self, client):
        resp = client.get(f"{BASE}/sales/fuel?limit=0")
        assert resp.status_code == 422


# ---------------------------------------------------------------------------
# Non-fuel sales
# ---------------------------------------------------------------------------


class TestNonfuelSales:
    def test_returns_200(self, client):
        resp = client.get(f"{BASE}/sales/nonfuel")
        assert resp.status_code == 200

    def test_seeded_sale_appears(self, client):
        _, station_id = seed_region_and_station(client, "NONFUEL-A")
        sale_id = seed_nonfuel_sale(
            client, station_id, sale_date=date.today(), revenue=50.0
        )
        resp = client.get(f"{BASE}/sales/nonfuel?station_id={station_id}")
        assert resp.status_code == 200
        ids = [s["id"] for s in resp.json()]
        assert sale_id in ids

    def test_filter_by_category(self, client):
        _, station_id = seed_region_and_station(client, "NONFUEL-B")
        coffee_id = seed_nonfuel_sale(
            client, station_id, sale_date=date.today(), category="coffee"
        )
        bakery_id = seed_nonfuel_sale(
            client, station_id, sale_date=date.today(), category="bakery"
        )
        resp = client.get(
            f"{BASE}/sales/nonfuel?station_id={station_id}&category=coffee"
        )
        assert resp.status_code == 200
        ids = [s["id"] for s in resp.json()]
        assert coffee_id in ids
        assert bakery_id not in ids

    def test_days_cutoff_excludes_old_record(self, client):
        _, station_id = seed_region_and_station(client, "NONFUEL-C")
        old_id = seed_nonfuel_sale(
            client, station_id, sale_date=date.today() - timedelta(days=400)
        )
        resp = client.get(
            f"{BASE}/sales/nonfuel?station_id={station_id}&days=30"
        )
        assert resp.status_code == 200
        ids = [s["id"] for s in resp.json()]
        assert old_id not in ids

    def test_nonfuel_sale_has_required_fields(self, client):
        _, station_id = seed_region_and_station(client, "NONFUEL-D")
        seed_nonfuel_sale(client, station_id, sale_date=date.today())
        resp = client.get(f"{BASE}/sales/nonfuel?station_id={station_id}")
        assert resp.status_code == 200
        rows = resp.json()
        assert len(rows) >= 1
        row = rows[0]
        for field in ("id", "station_id", "sale_date", "category", "quantity", "revenue", "margin"):
            assert field in row, f"Nonfuel sale missing field: {field}"


# ---------------------------------------------------------------------------
# Loyalty metrics
# ---------------------------------------------------------------------------


class TestLoyaltyMetrics:
    def test_returns_200(self, client):
        resp = client.get(f"{BASE}/sales/loyalty")
        assert resp.status_code == 200

    def test_seeded_metric_appears(self, client):
        _, station_id = seed_region_and_station(client, "LOYALTY-A")
        metric_id = _seed_loyalty(client, station_id, date(2025, 3, 1))
        resp = client.get(f"{BASE}/sales/loyalty?station_id={station_id}")
        assert resp.status_code == 200
        ids = [m["id"] for m in resp.json()]
        assert metric_id in ids

    def test_filter_by_station_id(self, client):
        _, station_id = seed_region_and_station(client, "LOYALTY-B")
        metric_id = _seed_loyalty(client, station_id, date(2025, 4, 1))
        resp = client.get(f"{BASE}/sales/loyalty?station_id={station_id}")
        assert resp.status_code == 200
        data = resp.json()
        assert all(m["station_id"] == station_id for m in data)

    def test_loyalty_metric_has_required_fields(self, client):
        _, station_id = seed_region_and_station(client, "LOYALTY-C")
        _seed_loyalty(client, station_id, date(2025, 5, 1))
        resp = client.get(f"{BASE}/sales/loyalty?station_id={station_id}")
        assert resp.status_code == 200
        rows = resp.json()
        assert len(rows) >= 1
        row = rows[0]
        for field in (
            "id", "station_id", "month", "active_members",
            "new_signups", "points_redeemed", "loyalty_revenue_share",
        ):
            assert field in row, f"Loyalty metric missing field: {field}"

    def test_loyalty_limit_too_low_returns_422(self, client):
        resp = client.get(f"{BASE}/sales/loyalty?limit=0")
        assert resp.status_code == 422
