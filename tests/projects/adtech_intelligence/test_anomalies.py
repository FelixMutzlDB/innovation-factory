"""Anomaly detection route tests for AdTech Intelligence.

Covers:
- /anomalies/counts: structure (all AnomalySeverity keys + total key), zero-state
- /anomalies: list + status/severity/type filters
- /anomalies/{id}: get (404 for unknown)
- PATCH /anomalies/{id}: resolved_at side-effect when status is resolved or dismissed,
  no resolved_at when status is acknowledged
- /anomaly-rules: list (returns a list)
"""
from __future__ import annotations

from contextlib import contextmanager
from datetime import date, datetime, timezone

import pytest


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


@contextmanager
def _db_session(client):
    from innovation_factory.backend.app import app
    from innovation_factory.backend.dependencies import get_session

    override = app.dependency_overrides.get(get_session)
    assert override is not None
    gen = override()
    db = next(gen)
    try:
        yield db
    finally:
        try:
            next(gen)
        except StopIteration:
            pass


def _make_anomaly(
    db,
    *,
    campaign_id=None,
    anomaly_type=None,
    severity=None,
    status=None,
    suffix: str = "",
):
    from innovation_factory.backend.projects.adtech_intelligence.models import (
        AnomalySeverity,
        AnomalyStatus,
        AnomalyType,
        AtAnomaly,
    )

    a = AtAnomaly(
        campaign_id=campaign_id,
        anomaly_type=anomaly_type or AnomalyType.ctr_anomaly,
        severity=severity or AnomalySeverity.medium,
        title=f"Test Anomaly {suffix}",
        description=f"Anomaly description {suffix}",
        status=status or AnomalyStatus.new,
        metric_name="ctr",
        expected_value=0.05,
        actual_value=0.01,
        deviation_pct=-80.0,
    )
    db.add(a)
    db.commit()
    db.refresh(a)
    return a


BASE = "/api/projects/adtech-intelligence"


# ---------------------------------------------------------------------------
# Anomaly counts
# ---------------------------------------------------------------------------


class TestAnomalyCounts:
    def test_returns_200(self, client):
        resp = client.get(f"{BASE}/anomalies/counts")
        assert resp.status_code == 200

    def test_contains_all_severity_levels(self, client):
        """All four AnomalySeverity enum values must appear as keys in the response."""
        resp = client.get(f"{BASE}/anomalies/counts")
        assert resp.status_code == 200
        data = resp.json()
        for severity in ("low", "medium", "high", "critical"):
            assert severity in data, f"Key '{severity}' missing from anomaly counts response"

    def test_contains_total_key(self, client):
        resp = client.get(f"{BASE}/anomalies/counts")
        assert "total" in resp.json()

    def test_total_equals_sum_of_severities(self, client):
        resp = client.get(f"{BASE}/anomalies/counts")
        assert resp.status_code == 200
        data = resp.json()
        severity_sum = data["low"] + data["medium"] + data["high"] + data["critical"]
        assert data["total"] == severity_sum

    def test_all_values_non_negative(self, client):
        data = client.get(f"{BASE}/anomalies/counts").json()
        for key, val in data.items():
            assert isinstance(val, int) and val >= 0, f"{key}={val} is negative or non-int"

    def test_active_anomaly_increments_severity_count(self, client):
        """Adding a new critical anomaly must bump the critical count + total."""
        from innovation_factory.backend.projects.adtech_intelligence.models import (
            AnomalySeverity,
            AnomalyStatus,
        )

        before = client.get(f"{BASE}/anomalies/counts").json()

        with _db_session(client) as db:
            _make_anomaly(
                db,
                severity=AnomalySeverity.critical,
                status=AnomalyStatus.new,
                suffix="counts-crit-001",
            )

        after = client.get(f"{BASE}/anomalies/counts").json()
        assert after["critical"] >= before["critical"] + 1
        assert after["total"] >= before["total"] + 1

    def test_resolved_anomaly_not_counted(self, client):
        """Resolved anomalies must NOT appear in the active counts."""
        from innovation_factory.backend.projects.adtech_intelligence.models import (
            AnomalySeverity,
            AnomalyStatus,
        )

        before = client.get(f"{BASE}/anomalies/counts").json()

        with _db_session(client) as db:
            _make_anomaly(
                db,
                severity=AnomalySeverity.high,
                status=AnomalyStatus.resolved,
                suffix="counts-resolved-001",
            )

        after = client.get(f"{BASE}/anomalies/counts").json()
        # Resolved anomalies must not change active counts
        assert after["total"] == before["total"], (
            "Resolved anomaly should not appear in active anomaly counts"
        )


# ---------------------------------------------------------------------------
# Anomaly list
# ---------------------------------------------------------------------------


class TestAnomalyList:
    def test_returns_200_as_list(self, client):
        resp = client.get(f"{BASE}/anomalies")
        assert resp.status_code == 200
        assert isinstance(resp.json(), list)

    def test_filter_by_severity(self, client):
        from innovation_factory.backend.projects.adtech_intelligence.models import (
            AnomalySeverity,
            AnomalyStatus,
        )

        with _db_session(client) as db:
            low = _make_anomaly(
                db,
                severity=AnomalySeverity.low,
                status=AnomalyStatus.new,
                suffix="list-sev-low",
            )
            high = _make_anomaly(
                db,
                severity=AnomalySeverity.high,
                status=AnomalyStatus.new,
                suffix="list-sev-high",
            )
            # Capture IDs while session is still open (avoids DetachedInstanceError)
            low_id = low.id
            high_id = high.id

        resp = client.get(f"{BASE}/anomalies?severity=low")
        assert resp.status_code == 200
        ids = [i["id"] for i in resp.json()]
        assert low_id in ids
        assert high_id not in ids
        for item in resp.json():
            assert item["severity"] == "low"

    def test_filter_by_status(self, client):
        from innovation_factory.backend.projects.adtech_intelligence.models import (
            AnomalySeverity,
            AnomalyStatus,
        )

        with _db_session(client) as db:
            new_a = _make_anomaly(
                db,
                severity=AnomalySeverity.medium,
                status=AnomalyStatus.new,
                suffix="list-stat-new",
            )
            resolved_a = _make_anomaly(
                db,
                severity=AnomalySeverity.medium,
                status=AnomalyStatus.resolved,
                suffix="list-stat-res",
            )
            # Capture IDs while session is still open (avoids DetachedInstanceError)
            new_a_id = new_a.id
            resolved_a_id = resolved_a.id

        resp = client.get(f"{BASE}/anomalies?status=new")
        assert resp.status_code == 200
        ids = [i["id"] for i in resp.json()]
        assert new_a_id in ids
        assert resolved_a_id not in ids

    def test_filter_by_type(self, client):
        from innovation_factory.backend.projects.adtech_intelligence.models import (
            AnomalyType,
        )

        with _db_session(client) as db:
            spike = _make_anomaly(
                db,
                anomaly_type=AnomalyType.impression_spike,
                suffix="list-type-spike",
            )
            spike_id = spike.id

        resp = client.get(f"{BASE}/anomalies?anomaly_type=impression_spike")
        assert resp.status_code == 200
        ids = [i["id"] for i in resp.json()]
        assert spike_id in ids

    def test_limit_respected(self, client):
        resp = client.get(f"{BASE}/anomalies?limit=2")
        assert resp.status_code == 200
        assert len(resp.json()) <= 2


# ---------------------------------------------------------------------------
# Anomaly detail
# ---------------------------------------------------------------------------


class TestAnomalyDetail:
    def test_get_404_for_nonexistent(self, client):
        assert client.get(f"{BASE}/anomalies/999999").status_code == 404

    def test_get_existing_anomaly(self, client):
        with _db_session(client) as db:
            a = _make_anomaly(db, suffix="detail-get")

        resp = client.get(f"{BASE}/anomalies/{a.id}")
        assert resp.status_code == 200
        data = resp.json()
        assert data["id"] == a.id
        assert data["metric_name"] == "ctr"

    def test_anomaly_response_shape(self, client):
        with _db_session(client) as db:
            a = _make_anomaly(db, suffix="detail-shape")

        resp = client.get(f"{BASE}/anomalies/{a.id}")
        data = resp.json()
        required = {
            "id", "anomaly_type", "severity", "title", "description",
            "status", "metric_name", "expected_value", "actual_value",
            "deviation_pct", "detected_at",
        }
        missing = required - set(data.keys())
        assert not missing, f"Missing fields in anomaly response: {missing}"


# ---------------------------------------------------------------------------
# Anomaly update — resolved_at side effect
# ---------------------------------------------------------------------------


class TestAnomalyUpdate:
    def test_update_404_for_nonexistent(self, client):
        resp = client.patch(f"{BASE}/anomalies/999999", json={"status": "resolved"})
        assert resp.status_code == 404

    def test_update_to_resolved_sets_resolved_at(self, client):
        """Resolving an anomaly must automatically stamp resolved_at."""
        with _db_session(client) as db:
            a = _make_anomaly(db, suffix="upd-resolve")

        assert a.resolved_at is None

        resp = client.patch(
            f"{BASE}/anomalies/{a.id}",
            json={"status": "resolved", "resolved_by": "ops@adtech.com"},
        )
        assert resp.status_code == 200
        data = resp.json()
        assert data["status"] == "resolved"
        assert data["resolved_at"] is not None, "resolved_at must be set when status=resolved"
        assert data["resolved_by"] == "ops@adtech.com"

    def test_update_to_dismissed_sets_resolved_at(self, client):
        """Dismissing an anomaly also stamps resolved_at (same code path)."""
        with _db_session(client) as db:
            a = _make_anomaly(db, suffix="upd-dismiss")

        resp = client.patch(f"{BASE}/anomalies/{a.id}", json={"status": "dismissed"})
        assert resp.status_code == 200
        data = resp.json()
        assert data["status"] == "dismissed"
        assert data["resolved_at"] is not None, (
            "resolved_at must be set when status=dismissed"
        )

    def test_update_to_acknowledged_does_not_set_resolved_at(self, client):
        """Acknowledging an anomaly must NOT stamp resolved_at — it's still open."""
        with _db_session(client) as db:
            a = _make_anomaly(db, suffix="upd-ack")

        resp = client.patch(f"{BASE}/anomalies/{a.id}", json={"status": "acknowledged"})
        assert resp.status_code == 200
        data = resp.json()
        assert data["status"] == "acknowledged"
        assert data["resolved_at"] is None, (
            "resolved_at must NOT be set for non-terminal statuses"
        )

    def test_partial_update_only_changes_given_fields(self, client):
        """PATCH must not reset unmentioned fields to defaults."""
        with _db_session(client) as db:
            a = _make_anomaly(db, suffix="upd-partial")

        # Only update resolved_by, leave status alone
        resp = client.patch(f"{BASE}/anomalies/{a.id}", json={"resolved_by": "alice@adtech.com"})
        assert resp.status_code == 200
        data = resp.json()
        assert data["status"] == "new"  # status unchanged
        assert data["resolved_by"] == "alice@adtech.com"


# ---------------------------------------------------------------------------
# Anomaly rules
# ---------------------------------------------------------------------------


class TestAnomalyRules:
    def test_list_rules_returns_200_list(self, client):
        resp = client.get(f"{BASE}/anomaly-rules")
        assert resp.status_code == 200
        assert isinstance(resp.json(), list)

    def test_seeded_rule_appears_in_list(self, client):
        from innovation_factory.backend.projects.adtech_intelligence.models import (
            AtAnomalyRule,
            RuleConditionType,
        )

        with _db_session(client) as db:
            rule = AtAnomalyRule(
                name="CTR Drop Detection",
                metric_name="ctr",
                condition_type=RuleConditionType.threshold,
                threshold_value=0.02,
                lookback_days=7,
            )
            db.add(rule)
            db.commit()
            db.refresh(rule)

        resp = client.get(f"{BASE}/anomaly-rules")
        assert resp.status_code == 200
        items = resp.json()
        ids = [i["id"] for i in items]
        assert rule.id in ids
