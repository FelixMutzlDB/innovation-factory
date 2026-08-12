"""Tests for inventory, competitor price, and price history endpoints."""
from __future__ import annotations

from datetime import date, timedelta

from ._helpers import _seeding_session, seed_region_and_station

BASE = "/api/projects/mol-asm-cockpit"


def _seed_inventory(client, station_id: int, *, record_date: date,
                    category: str = "coffee") -> int:
    from innovation_factory.backend.projects.mol_asm_cockpit.models import (
        MacInventory, ProductCategory,
    )
    with _seeding_session(client) as session:
        inv = MacInventory(
            station_id=station_id,
            record_date=record_date,
            product_category=ProductCategory(category),
            stock_level=100,
            reorder_point=20,
            spoilage_count=3,
            stock_out_events=0,
        )
        session.add(inv)
        session.flush()
        assert inv.id is not None
        return inv.id


def _seed_competitor_price(client, station_id: int, *, price_date: date,
                            fuel_type: str = "diesel") -> int:
    from innovation_factory.backend.projects.mol_asm_cockpit.models import (
        MacCompetitorPrice, FuelType,
    )
    with _seeding_session(client) as session:
        cp = MacCompetitorPrice(
            station_id=station_id,
            price_date=price_date,
            competitor_name="Shell",
            fuel_type=FuelType(fuel_type),
            price_per_liter=1.65,
        )
        session.add(cp)
        session.flush()
        assert cp.id is not None
        return cp.id


def _seed_price_history(client, station_id: int, *, price_date: date,
                         fuel_type: str = "diesel") -> int:
    from innovation_factory.backend.projects.mol_asm_cockpit.models import (
        MacPriceHistory, FuelType,
    )
    with _seeding_session(client) as session:
        ph = MacPriceHistory(
            station_id=station_id,
            price_date=price_date,
            fuel_type=FuelType(fuel_type),
            price_per_liter=1.60,
            cost_per_liter=1.48,
        )
        session.add(ph)
        session.flush()
        assert ph.id is not None
        return ph.id


# ---------------------------------------------------------------------------
# Inventory
# ---------------------------------------------------------------------------


class TestInventory:
    def test_returns_200(self, client):
        resp = client.get(f"{BASE}/inventory")
        assert resp.status_code == 200
        assert isinstance(resp.json(), list)

    def test_seeded_inventory_appears(self, client):
        _, station_id = seed_region_and_station(client, "INV-A")
        inv_id = _seed_inventory(client, station_id, record_date=date.today())
        resp = client.get(f"{BASE}/inventory?station_id={station_id}")
        assert resp.status_code == 200
        ids = [i["id"] for i in resp.json()]
        assert inv_id in ids

    def test_filter_by_station_id(self, client):
        _, station_id = seed_region_and_station(client, "INV-B")
        _seed_inventory(client, station_id, record_date=date.today())
        resp = client.get(f"{BASE}/inventory?station_id={station_id}")
        assert resp.status_code == 200
        assert all(i["station_id"] == station_id for i in resp.json())

    def test_filter_by_product_category(self, client):
        _, station_id = seed_region_and_station(client, "INV-C")
        coffee_id = _seed_inventory(client, station_id, record_date=date.today(),
                                    category="coffee")
        bakery_id = _seed_inventory(client, station_id, record_date=date.today(),
                                    category="bakery")
        resp = client.get(
            f"{BASE}/inventory?station_id={station_id}&product_category=coffee"
        )
        assert resp.status_code == 200
        ids = [i["id"] for i in resp.json()]
        assert coffee_id in ids
        assert bakery_id not in ids

    def test_days_cutoff_excludes_old_record(self, client):
        _, station_id = seed_region_and_station(client, "INV-D")
        old_id = _seed_inventory(
            client, station_id,
            record_date=date.today() - timedelta(days=100),
        )
        resp = client.get(
            f"{BASE}/inventory?station_id={station_id}&days=7"
        )
        assert resp.status_code == 200
        ids = [i["id"] for i in resp.json()]
        assert old_id not in ids

    def test_inventory_has_required_fields(self, client):
        _, station_id = seed_region_and_station(client, "INV-E")
        _seed_inventory(client, station_id, record_date=date.today())
        resp = client.get(f"{BASE}/inventory?station_id={station_id}")
        assert resp.status_code == 200
        rows = resp.json()
        assert len(rows) >= 1
        row = rows[0]
        for field in (
            "id", "station_id", "record_date", "product_category",
            "stock_level", "reorder_point", "spoilage_count",
            "stock_out_events", "delivery_scheduled",
        ):
            assert field in row, f"Inventory missing field: {field}"


# ---------------------------------------------------------------------------
# Competitor prices
# ---------------------------------------------------------------------------


class TestCompetitorPrices:
    def test_returns_200(self, client):
        resp = client.get(f"{BASE}/inventory/competitor-prices")
        assert resp.status_code == 200
        assert isinstance(resp.json(), list)

    def test_seeded_price_appears(self, client):
        _, station_id = seed_region_and_station(client, "COMP-A")
        cp_id = _seed_competitor_price(client, station_id, price_date=date.today())
        resp = client.get(
            f"{BASE}/inventory/competitor-prices?station_id={station_id}"
        )
        assert resp.status_code == 200
        ids = [p["id"] for p in resp.json()]
        assert cp_id in ids

    def test_days_cutoff_excludes_old_record(self, client):
        _, station_id = seed_region_and_station(client, "COMP-B")
        old_id = _seed_competitor_price(
            client, station_id,
            price_date=date.today() - timedelta(days=400),
        )
        resp = client.get(
            f"{BASE}/inventory/competitor-prices?station_id={station_id}&days=30"
        )
        assert resp.status_code == 200
        ids = [p["id"] for p in resp.json()]
        assert old_id not in ids

    def test_competitor_price_has_required_fields(self, client):
        _, station_id = seed_region_and_station(client, "COMP-C")
        _seed_competitor_price(client, station_id, price_date=date.today())
        resp = client.get(
            f"{BASE}/inventory/competitor-prices?station_id={station_id}"
        )
        assert resp.status_code == 200
        rows = resp.json()
        assert len(rows) >= 1
        row = rows[0]
        for field in ("id", "station_id", "price_date", "competitor_name",
                      "fuel_type", "price_per_liter"):
            assert field in row, f"CompetitorPrice missing field: {field}"


# ---------------------------------------------------------------------------
# Price history
# ---------------------------------------------------------------------------


class TestPriceHistory:
    def test_returns_200(self, client):
        resp = client.get(f"{BASE}/inventory/price-history")
        assert resp.status_code == 200
        assert isinstance(resp.json(), list)

    def test_seeded_price_history_appears(self, client):
        _, station_id = seed_region_and_station(client, "PRICEH-A")
        ph_id = _seed_price_history(client, station_id, price_date=date.today())
        resp = client.get(
            f"{BASE}/inventory/price-history?station_id={station_id}"
        )
        assert resp.status_code == 200
        ids = [p["id"] for p in resp.json()]
        assert ph_id in ids

    def test_filter_by_fuel_type(self, client):
        _, station_id = seed_region_and_station(client, "PRICEH-B")
        diesel_id = _seed_price_history(
            client, station_id, price_date=date.today(), fuel_type="diesel"
        )
        lpg_id = _seed_price_history(
            client, station_id, price_date=date.today(), fuel_type="lpg"
        )
        resp = client.get(
            f"{BASE}/inventory/price-history?station_id={station_id}&fuel_type=diesel"
        )
        assert resp.status_code == 200
        ids = [p["id"] for p in resp.json()]
        assert diesel_id in ids
        assert lpg_id not in ids

    def test_price_history_has_required_fields(self, client):
        _, station_id = seed_region_and_station(client, "PRICEH-C")
        _seed_price_history(client, station_id, price_date=date.today())
        resp = client.get(
            f"{BASE}/inventory/price-history?station_id={station_id}"
        )
        assert resp.status_code == 200
        rows = resp.json()
        assert len(rows) >= 1
        row = rows[0]
        for field in ("id", "station_id", "price_date", "fuel_type",
                      "price_per_liter", "cost_per_liter"):
            assert field in row, f"PriceHistory missing field: {field}"
