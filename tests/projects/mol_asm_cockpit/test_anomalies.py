"""Tests for anomaly alert endpoints.

Covers: list with filters, get by ID, 404, and the status-transition
logic where resolving/dismissing an alert auto-stamps resolved_at.
"""
from __future__ import annotations

from datetime import datetime, timezone

import pytest

from ._helpers import seed_anomaly_alert, seed_region_and_station

BASE = "/api/projects/mol-asm-cockpit"


# ---------------------------------------------------------------------------
# List anomaly alerts
# ---------------------------------------------------------------------------


class TestListAnomalies:
    def test_returns_200(self, client):
        resp = client.get(f"{BASE}/anomalies")
        assert resp.status_code == 200
        assert isinstance(resp.json(), list)

    def test_seeded_alert_appears_in_list(self, client):
        _, station_id = seed_region_and_station(client, "ANOMLIST-A")
        alert_id = seed_anomaly_alert(client, station_id, "LA1", severity="high")
        resp = client.get(f"{BASE}/anomalies")
        assert resp.status_code == 200
        ids = [a["id"] for a in resp.json()]
        assert alert_id in ids

    def test_filter_by_station_id(self, client):
        _, station_id = seed_region_and_station(client, "ANOMLIST-B")
        alert_id = seed_anomaly_alert(client, station_id, "LB1")
        resp = client.get(f"{BASE}/anomalies?station_id={station_id}")
        assert resp.status_code == 200
        data = resp.json()
        # All returned alerts belong to the queried station
        assert all(a["station_id"] == station_id for a in data)
        ids = [a["id"] for a in data]
        assert alert_id in ids

    def test_filter_by_status_active(self, client):
        _, station_id = seed_region_and_station(client, "ANOMLIST-C")
        active_id = seed_anomaly_alert(client, station_id, "LC1", status="active")
        resolved_id = seed_anomaly_alert(client, station_id, "LC2", status="resolved")
        resp = client.get(f"{BASE}/anomalies?station_id={station_id}&status=active")
        assert resp.status_code == 200
        ids = [a["id"] for a in resp.json()]
        assert active_id in ids
        assert resolved_id not in ids

    def test_filter_by_severity_critical(self, client):
        _, station_id = seed_region_and_station(client, "ANOMLIST-D")
        critical_id = seed_anomaly_alert(client, station_id, "LD1", severity="critical")
        low_id = seed_anomaly_alert(client, station_id, "LD2", severity="low")
        resp = client.get(f"{BASE}/anomalies?station_id={station_id}&severity=critical")
        assert resp.status_code == 200
        ids = [a["id"] for a in resp.json()]
        assert critical_id in ids
        assert low_id not in ids

    def test_alert_has_required_fields(self, client):
        _, station_id = seed_region_and_station(client, "ANOMLIST-E")
        seed_anomaly_alert(client, station_id, "LE1")
        resp = client.get(f"{BASE}/anomalies?station_id={station_id}")
        assert resp.status_code == 200
        rows = resp.json()
        assert len(rows) >= 1
        row = rows[0]
        for field in (
            "id", "station_id", "metric_type", "severity", "title",
            "description", "suggested_action", "status", "detected_at",
        ):
            assert field in row, f"Alert response missing field: {field}"

    def test_limit_param_constrains_results(self, client):
        _, station_id = seed_region_and_station(client, "ANOMLIST-F")
        # Seed 3 alerts
        for i in range(3):
            seed_anomaly_alert(client, station_id, f"LF{i}")
        resp = client.get(f"{BASE}/anomalies?station_id={station_id}&limit=2")
        assert resp.status_code == 200
        assert len(resp.json()) <= 2

    def test_limit_too_low_returns_422(self, client):
        resp = client.get(f"{BASE}/anomalies?limit=0")
        assert resp.status_code == 422

    def test_limit_too_high_returns_422(self, client):
        resp = client.get(f"{BASE}/anomalies?limit=501")
        assert resp.status_code == 422


# ---------------------------------------------------------------------------
# Get single alert
# ---------------------------------------------------------------------------


class TestGetAnomaly:
    def test_returns_alert_by_id(self, client):
        _, station_id = seed_region_and_station(client, "ANOMGET-A")
        alert_id = seed_anomaly_alert(client, station_id, "GA1", severity="medium")
        resp = client.get(f"{BASE}/anomalies/{alert_id}")
        assert resp.status_code == 200
        data = resp.json()
        assert data["id"] == alert_id
        assert data["station_id"] == station_id
        assert data["severity"] == "medium"
        assert data["title"] == "Test Alert GA1"

    def test_unknown_id_returns_404(self, client):
        resp = client.get(f"{BASE}/anomalies/999999")
        assert resp.status_code == 404


# ---------------------------------------------------------------------------
# Update / status transitions
# ---------------------------------------------------------------------------


class TestUpdateAnomaly:
    def test_acknowledge_sets_status(self, client):
        _, station_id = seed_region_and_station(client, "ANOMUPD-A")
        alert_id = seed_anomaly_alert(client, station_id, "UA1", status="active")
        resp = client.patch(
            f"{BASE}/anomalies/{alert_id}",
            json={"status": "acknowledged"},
        )
        assert resp.status_code == 200
        data = resp.json()
        assert data["status"] == "acknowledged"

    def test_acknowledge_does_not_set_resolved_at(self, client):
        """Only resolved/dismissed auto-stamp resolved_at; acknowledged does not."""
        _, station_id = seed_region_and_station(client, "ANOMUPD-B")
        alert_id = seed_anomaly_alert(client, station_id, "UB1", status="active")
        resp = client.patch(
            f"{BASE}/anomalies/{alert_id}",
            json={"status": "acknowledged"},
        )
        assert resp.status_code == 200
        # resolved_at must still be None after acknowledgment
        assert resp.json()["resolved_at"] is None

    def test_resolve_auto_stamps_resolved_at(self, client):
        """Resolving an alert must auto-set resolved_at to a non-null timestamp."""
        _, station_id = seed_region_and_station(client, "ANOMUPD-C")
        alert_id = seed_anomaly_alert(client, station_id, "UC1", status="active")
        resp = client.patch(
            f"{BASE}/anomalies/{alert_id}",
            json={"status": "resolved"},
        )
        assert resp.status_code == 200
        data = resp.json()
        assert data["status"] == "resolved"
        assert data["resolved_at"] is not None, "resolved_at must be set when resolving"

    def test_dismiss_auto_stamps_resolved_at(self, client):
        """Dismissing an alert must also auto-set resolved_at."""
        _, station_id = seed_region_and_station(client, "ANOMUPD-D")
        alert_id = seed_anomaly_alert(client, station_id, "UD1", status="active")
        resp = client.patch(
            f"{BASE}/anomalies/{alert_id}",
            json={"status": "dismissed"},
        )
        assert resp.status_code == 200
        data = resp.json()
        assert data["status"] == "dismissed"
        assert data["resolved_at"] is not None, "resolved_at must be set when dismissing"

    def test_update_unknown_id_returns_404(self, client):
        resp = client.patch(
            f"{BASE}/anomalies/999999",
            json={"status": "resolved"},
        )
        assert resp.status_code == 404

    def test_patch_with_no_fields_is_no_op(self, client):
        """An empty PATCH body is valid — no state changes, status stays active."""
        _, station_id = seed_region_and_station(client, "ANOMUPD-E")
        alert_id = seed_anomaly_alert(client, station_id, "UE1", status="active")
        resp = client.patch(f"{BASE}/anomalies/{alert_id}", json={})
        assert resp.status_code == 200
        assert resp.json()["status"] == "active"
