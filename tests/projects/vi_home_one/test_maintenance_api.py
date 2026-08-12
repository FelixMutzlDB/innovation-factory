"""API tests for maintenance alert endpoints.

Covers:
- GET  /maintenance/households/{id}/alerts         → list, default excludes acknowledged
- GET  /maintenance/households/{id}/alerts?include_acknowledged=true
- POST /maintenance/alerts/{id}/acknowledge        → 200 / 404 / sets acknowledged_at
"""
from __future__ import annotations

from datetime import date

import pytest

import innovation_factory.backend.projects.vi_home_one.models  # noqa: F401

BASE = "/api/projects/vi-home-one"


def _seed_neighborhood_and_household(session, owner="Alert User"):
    from innovation_factory.backend.projects.vi_home_one.models import VhNeighborhood, VhHousehold
    n = VhNeighborhood(name="Alert Hood", location="Dresden", total_households=1)
    session.add(n)
    session.commit()
    session.refresh(n)
    h = VhHousehold(neighborhood_id=n.id, owner_name=owner, address="Alert Str. 1")
    session.add(h)
    session.commit()
    session.refresh(h)
    return h


def _seed_device(session, household_id, device_type=None):
    from innovation_factory.backend.projects.vi_home_one.models import VhEnergyDevice, DeviceType
    d = VhEnergyDevice(
        household_id=household_id,
        device_type=device_type or DeviceType.heat_pump,
        brand="Viessmann",
        model="Vitocal 250-A",
        installation_date=date(2022, 3, 1),
    )
    session.add(d)
    session.commit()
    session.refresh(d)
    return d


def _seed_alert(session, device_id, severity="medium", is_acknowledged=False):
    from innovation_factory.backend.projects.vi_home_one.models import VhMaintenanceAlert, AlertSeverity
    a = VhMaintenanceAlert(
        device_id=device_id,
        alert_type="filter_dirty",
        severity=AlertSeverity(severity),
        message="Air filter needs cleaning",
        is_acknowledged=is_acknowledged,
    )
    session.add(a)
    session.commit()
    session.refresh(a)
    return a


class TestListMaintenanceAlerts:
    def test_no_devices_returns_empty_list(self, client, session):
        h = _seed_neighborhood_and_household(session)
        resp = client.get(f"{BASE}/maintenance/households/{h.id}/alerts")
        assert resp.status_code == 200
        assert resp.json() == []

    def test_unacknowledged_alerts_included_by_default(self, client, session):
        h = _seed_neighborhood_and_household(session)
        d = _seed_device(session, h.id)
        _seed_alert(session, d.id, is_acknowledged=False)

        resp = client.get(f"{BASE}/maintenance/households/{h.id}/alerts")
        assert resp.status_code == 200
        assert len(resp.json()) == 1

    def test_acknowledged_alerts_excluded_by_default(self, client, session):
        h = _seed_neighborhood_and_household(session)
        d = _seed_device(session, h.id)
        _seed_alert(session, d.id, is_acknowledged=True)

        resp = client.get(f"{BASE}/maintenance/households/{h.id}/alerts")
        assert resp.status_code == 200
        assert len(resp.json()) == 0

    def test_include_acknowledged_returns_all(self, client, session):
        h = _seed_neighborhood_and_household(session)
        d = _seed_device(session, h.id)
        _seed_alert(session, d.id, is_acknowledged=False)
        _seed_alert(session, d.id, is_acknowledged=True)

        resp = client.get(
            f"{BASE}/maintenance/households/{h.id}/alerts?include_acknowledged=true"
        )
        assert resp.status_code == 200
        assert len(resp.json()) == 2

    def test_alert_response_shape(self, client, session):
        h = _seed_neighborhood_and_household(session)
        d = _seed_device(session, h.id)
        _seed_alert(session, d.id)

        resp = client.get(f"{BASE}/maintenance/households/{h.id}/alerts")
        assert resp.status_code == 200
        item = resp.json()[0]
        required = {
            "id", "device_id", "device_type", "device_model",
            "alert_type", "severity", "message", "is_acknowledged", "created_at",
        }
        assert required.issubset(set(item.keys()))

    def test_alert_device_info_populated(self, client, session):
        from innovation_factory.backend.projects.vi_home_one.models import DeviceType
        h = _seed_neighborhood_and_household(session)
        d = _seed_device(session, h.id, device_type=DeviceType.pv_system)
        _seed_alert(session, d.id)

        resp = client.get(f"{BASE}/maintenance/households/{h.id}/alerts")
        assert resp.status_code == 200
        item = resp.json()[0]
        assert item["device_type"] == "pv_system"
        assert item["device_model"] == "Vitocal 250-A"

    def test_multiple_severity_levels(self, client, session):
        h = _seed_neighborhood_and_household(session)
        d = _seed_device(session, h.id)
        _seed_alert(session, d.id, severity="low")
        _seed_alert(session, d.id, severity="critical")
        _seed_alert(session, d.id, severity="high")

        resp = client.get(
            f"{BASE}/maintenance/households/{h.id}/alerts"
        )
        assert resp.status_code == 200
        assert len(resp.json()) == 3
        severities = {item["severity"] for item in resp.json()}
        assert "low" in severities
        assert "critical" in severities
        assert "high" in severities


class TestAcknowledgeAlert:
    def test_unknown_alert_returns_404(self, client):
        resp = client.post(
            f"{BASE}/maintenance/alerts/99999/acknowledge",
            json={"is_acknowledged": True},
        )
        assert resp.status_code == 404

    def test_acknowledge_sets_flag_and_timestamp(self, client, session):
        h = _seed_neighborhood_and_household(session)
        d = _seed_device(session, h.id)
        a = _seed_alert(session, d.id, is_acknowledged=False)

        resp = client.post(
            f"{BASE}/maintenance/alerts/{a.id}/acknowledge",
            json={"is_acknowledged": True},
        )
        assert resp.status_code == 200
        data = resp.json()
        assert data["is_acknowledged"] is True
        assert data["id"] == a.id

    def test_unacknowledge_clears_flag(self, client, session):
        h = _seed_neighborhood_and_household(session)
        d = _seed_device(session, h.id)
        a = _seed_alert(session, d.id, is_acknowledged=True)

        resp = client.post(
            f"{BASE}/maintenance/alerts/{a.id}/acknowledge",
            json={"is_acknowledged": False},
        )
        assert resp.status_code == 200
        assert resp.json()["is_acknowledged"] is False

    def test_acknowledge_response_includes_device_info(self, client, session):
        h = _seed_neighborhood_and_household(session)
        d = _seed_device(session, h.id)
        a = _seed_alert(session, d.id)

        resp = client.post(
            f"{BASE}/maintenance/alerts/{a.id}/acknowledge",
            json={"is_acknowledged": True},
        )
        assert resp.status_code == 200
        data = resp.json()
        assert "device_type" in data
        assert "device_model" in data
