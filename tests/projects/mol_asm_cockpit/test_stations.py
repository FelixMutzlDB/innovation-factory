"""Tests for station, region, and KPI endpoints.

Golden paths, 404 handling, filter params, and KPI aggregation
correctness (the most load-bearing logic in this accelerator).
"""
from __future__ import annotations

from datetime import date, timedelta

import pytest

from ._helpers import (
    seed_anomaly_alert,
    seed_fuel_sale,
    seed_nonfuel_sale,
    seed_region_and_station,
)

BASE = "/api/projects/mol-asm-cockpit"


# ---------------------------------------------------------------------------
# Regions
# ---------------------------------------------------------------------------


class TestRegionsEndpoint:
    def test_returns_200(self, client):
        resp = client.get(f"{BASE}/stations/regions")
        assert resp.status_code == 200
        assert isinstance(resp.json(), list)

    def test_seeded_region_appears_in_list(self, client):
        """Seed a region and verify it appears in the list response."""
        region_id, _ = seed_region_and_station(client, "REGIONS-A")
        resp = client.get(f"{BASE}/stations/regions")
        assert resp.status_code == 200
        ids = [r["id"] for r in resp.json()]
        assert region_id in ids

    def test_region_has_expected_fields(self, client):
        seed_region_and_station(client, "REGIONS-B")
        resp = client.get(f"{BASE}/stations/regions")
        assert resp.status_code == 200
        rows = resp.json()
        assert len(rows) >= 1
        row = rows[0]
        assert "id" in row
        assert "name" in row
        assert "country" in row


# ---------------------------------------------------------------------------
# List stations
# ---------------------------------------------------------------------------


class TestListStationsEndpoint:
    def test_returns_200_empty_or_seeded(self, client):
        resp = client.get(f"{BASE}/stations")
        assert resp.status_code == 200
        assert isinstance(resp.json(), list)

    def test_seeded_station_appears(self, client):
        _, station_id = seed_region_and_station(client, "LSTSTN-A")
        resp = client.get(f"{BASE}/stations")
        assert resp.status_code == 200
        ids = [s["id"] for s in resp.json()]
        assert station_id in ids

    def test_filter_by_region_id(self, client):
        region_id, station_id = seed_region_and_station(client, "LSTSTN-B")
        resp = client.get(f"{BASE}/stations?region_id={region_id}")
        assert resp.status_code == 200
        ids = [s["id"] for s in resp.json()]
        assert station_id in ids
        # All returned stations belong to the queried region
        for s in resp.json():
            assert s["region_id"] == region_id

    def test_filter_by_station_type_urban(self, client):
        """Seeded helpers create urban stations; they must appear in type filter."""
        _, station_id = seed_region_and_station(client, "LSTSTN-C")
        resp = client.get(f"{BASE}/stations?station_type=urban")
        assert resp.status_code == 200
        ids = [s["id"] for s in resp.json()]
        assert station_id in ids

    def test_unknown_region_returns_empty(self, client):
        resp = client.get(f"{BASE}/stations?region_id=999999")
        assert resp.status_code == 200
        assert resp.json() == []

    def test_station_has_required_fields(self, client):
        seed_region_and_station(client, "LSTSTN-D")
        resp = client.get(f"{BASE}/stations")
        assert resp.status_code == 200
        rows = resp.json()
        assert len(rows) >= 1
        row = rows[0]
        for field in ("id", "station_code", "name", "city", "region_id",
                      "latitude", "longitude", "station_type"):
            assert field in row, f"Field '{field}' missing from station response"


# ---------------------------------------------------------------------------
# Get single station
# ---------------------------------------------------------------------------


class TestGetStationEndpoint:
    def test_returns_station_by_id(self, client):
        _, station_id = seed_region_and_station(client, "GETSTN-A")
        resp = client.get(f"{BASE}/stations/{station_id}")
        assert resp.status_code == 200
        data = resp.json()
        assert data["id"] == station_id
        assert data["station_code"] == "TST-GETSTN-A"

    def test_unknown_station_returns_404(self, client):
        resp = client.get(f"{BASE}/stations/999999")
        assert resp.status_code == 404


# ---------------------------------------------------------------------------
# Station KPIs — aggregation correctness
# ---------------------------------------------------------------------------


class TestStationKPIEndpoint:
    def test_returns_200(self, client):
        resp = client.get(f"{BASE}/stations/kpis")
        assert resp.status_code == 200
        assert isinstance(resp.json(), list)

    def test_station_with_no_sales_shows_zeros(self, client):
        """A station with no fuel/nonfuel sales and no alerts must show all-zeros
        KPIs (the outer-join null-coalescing path: ``r[n] or 0``)."""
        _, station_id = seed_region_and_station(client, "KPI-ZEROS")
        resp = client.get(f"{BASE}/stations/kpis?days=30")
        assert resp.status_code == 200
        kpis = resp.json()
        our_kpi = next((k for k in kpis if k["station_id"] == station_id), None)
        assert our_kpi is not None, "Station must appear in KPI list"
        assert our_kpi["total_fuel_volume"] == pytest.approx(0.0)
        assert our_kpi["total_fuel_revenue"] == pytest.approx(0.0)
        assert our_kpi["total_fuel_margin"] == pytest.approx(0.0)
        assert our_kpi["total_nonfuel_revenue"] == pytest.approx(0.0)
        assert our_kpi["total_nonfuel_margin"] == pytest.approx(0.0)
        assert our_kpi["active_alerts"] == 0

    def test_kpi_sums_fuel_revenue_correctly(self, client):
        """Two fuel sales → KPI aggregates both into the total."""
        _, station_id = seed_region_and_station(client, "KPI-FUEL")
        seed_fuel_sale(client, station_id, sale_date=date.today(),
                       volume_liters=100.0, revenue=160.0, margin=12.0)
        seed_fuel_sale(client, station_id, sale_date=date.today(),
                       volume_liters=200.0, revenue=320.0, margin=24.0)

        resp = client.get(f"{BASE}/stations/kpis?days=30")
        assert resp.status_code == 200
        kpis = resp.json()
        our_kpi = next((k for k in kpis if k["station_id"] == station_id), None)
        assert our_kpi is not None
        assert our_kpi["total_fuel_volume"] == pytest.approx(300.0)
        assert our_kpi["total_fuel_revenue"] == pytest.approx(480.0)
        assert our_kpi["total_fuel_margin"] == pytest.approx(36.0)

    def test_kpi_sums_nonfuel_revenue(self, client):
        """Nonfuel sales are aggregated separately."""
        _, station_id = seed_region_and_station(client, "KPI-NONFUEL")
        seed_nonfuel_sale(client, station_id, sale_date=date.today(),
                          revenue=50.0, margin=25.0)
        seed_nonfuel_sale(client, station_id, sale_date=date.today(),
                          revenue=70.0, margin=35.0)

        resp = client.get(f"{BASE}/stations/kpis?days=30")
        assert resp.status_code == 200
        kpis = resp.json()
        our_kpi = next((k for k in kpis if k["station_id"] == station_id), None)
        assert our_kpi is not None
        assert our_kpi["total_nonfuel_revenue"] == pytest.approx(120.0)
        assert our_kpi["total_nonfuel_margin"] == pytest.approx(60.0)

    def test_kpi_counts_only_active_alerts(self, client):
        """Resolved and dismissed alerts must NOT increment active_alerts count."""
        _, station_id = seed_region_and_station(client, "KPI-ALERTS")
        seed_anomaly_alert(client, station_id, "KPIA1", status="active")
        seed_anomaly_alert(client, station_id, "KPIA2", status="active")
        seed_anomaly_alert(client, station_id, "KPIA3", status="resolved")
        seed_anomaly_alert(client, station_id, "KPIA4", status="dismissed")
        seed_anomaly_alert(client, station_id, "KPIA5", status="acknowledged")

        resp = client.get(f"{BASE}/stations/kpis?days=30")
        assert resp.status_code == 200
        kpis = resp.json()
        our_kpi = next((k for k in kpis if k["station_id"] == station_id), None)
        assert our_kpi is not None
        # Only 2 active alerts; acknowledged/resolved/dismissed are excluded
        assert our_kpi["active_alerts"] == 2

    def test_kpi_excludes_sales_outside_days_window(self, client):
        """A fuel sale dated 400 days ago must not appear in a 30-day KPI query."""
        _, station_id = seed_region_and_station(client, "KPI-WINDOW")
        old_date = date.today() - timedelta(days=400)
        seed_fuel_sale(client, station_id, sale_date=old_date,
                       volume_liters=500.0, revenue=800.0, margin=60.0)

        resp = client.get(f"{BASE}/stations/kpis?days=30")
        assert resp.status_code == 200
        kpis = resp.json()
        our_kpi = next((k for k in kpis if k["station_id"] == station_id), None)
        assert our_kpi is not None
        # Old sale is outside the 30-day window → revenue should be 0
        assert our_kpi["total_fuel_revenue"] == pytest.approx(0.0)

    def test_kpi_days_param_invalid_too_low(self, client):
        """days must be >= 1 per the Query constraint."""
        resp = client.get(f"{BASE}/stations/kpis?days=0")
        assert resp.status_code == 422

    def test_kpi_days_param_invalid_too_high(self, client):
        """days must be <= 365 per the Query constraint."""
        resp = client.get(f"{BASE}/stations/kpis?days=400")
        assert resp.status_code == 422

    def test_kpi_has_expected_fields(self, client):
        """KPI response shape must include all dashboard fields."""
        seed_region_and_station(client, "KPI-FIELDS")
        resp = client.get(f"{BASE}/stations/kpis?days=30")
        assert resp.status_code == 200
        rows = resp.json()
        assert len(rows) >= 1
        row = rows[0]
        for field in (
            "station_id", "station_code", "station_name", "city", "region_name",
            "total_fuel_volume", "total_fuel_revenue", "total_fuel_margin",
            "total_nonfuel_revenue", "total_nonfuel_margin", "active_alerts",
        ):
            assert field in row, f"KPI row missing field: {field}"
