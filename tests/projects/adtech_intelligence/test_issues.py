"""Issue, advertiser, and contract route tests for AdTech Intelligence.

Covers:
- /issues: list + filters (status, priority, category, campaign_id), 404 for get/patch
- PATCH /issues/{id}: update fields
- /advertisers: list, returns correct shape
- /contracts: list + advertiser_id filter
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


def _make_advertiser(db, *, suffix: str = ""):
    from innovation_factory.backend.projects.adtech_intelligence.models import AtAdvertiser

    adv = AtAdvertiser(
        name=f"Advertiser {suffix}",
        industry="retail",
        contact_name=f"Contact {suffix}",
        contact_email=f"issues{suffix}@adtech-test.com",
        budget_tier="standard",
    )
    db.add(adv)
    db.commit()
    db.refresh(adv)
    return adv


def _make_issue(db, *, status=None, priority=None, category=None,
                campaign_id=None, advertiser_id=None, suffix: str = ""):
    from innovation_factory.backend.projects.adtech_intelligence.models import (
        AtIssue,
        IssueCategory,
        IssuePriority,
        IssueStatus,
    )

    issue = AtIssue(
        title=f"Issue {suffix}",
        description=f"Description of issue {suffix}",
        category=category or IssueCategory.delivery,
        status=status or IssueStatus.open,
        priority=priority or IssuePriority.medium,
        campaign_id=campaign_id,
        advertiser_id=advertiser_id,
    )
    db.add(issue)
    db.commit()
    db.refresh(issue)
    return issue


BASE = "/api/projects/adtech-intelligence"


# ---------------------------------------------------------------------------
# Issue list
# ---------------------------------------------------------------------------


class TestIssueList:
    def test_returns_200_as_list(self, client):
        resp = client.get(f"{BASE}/issues")
        assert resp.status_code == 200
        assert isinstance(resp.json(), list)

    def test_filter_by_open_status(self, client):
        from innovation_factory.backend.projects.adtech_intelligence.models import (
            IssueStatus,
        )

        with _db_session(client) as db:
            open_issue = _make_issue(db, status=IssueStatus.open, suffix="list-open")
            closed_issue = _make_issue(db, status=IssueStatus.closed, suffix="list-closed")
            # Capture IDs while session is still open (avoids DetachedInstanceError)
            open_issue_id = open_issue.id
            closed_issue_id = closed_issue.id

        resp = client.get(f"{BASE}/issues?status=open")
        assert resp.status_code == 200
        items = resp.json()
        ids = [i["id"] for i in items]
        assert open_issue_id in ids
        assert closed_issue_id not in ids
        for item in items:
            assert item["status"] == "open"

    def test_filter_by_urgent_priority(self, client):
        from innovation_factory.backend.projects.adtech_intelligence.models import (
            IssuePriority,
        )

        with _db_session(client) as db:
            urgent_issue = _make_issue(
                db, priority=IssuePriority.urgent, suffix="list-urgent"
            )
            low_issue = _make_issue(db, priority=IssuePriority.low, suffix="list-low")
            urgent_id = urgent_issue.id
            low_id = low_issue.id

        resp = client.get(f"{BASE}/issues?priority=urgent")
        assert resp.status_code == 200
        ids = [i["id"] for i in resp.json()]
        assert urgent_id in ids
        assert low_id not in ids

    def test_filter_by_category(self, client):
        from innovation_factory.backend.projects.adtech_intelligence.models import (
            IssueCategory,
        )

        with _db_session(client) as db:
            billing_issue = _make_issue(
                db, category=IssueCategory.billing, suffix="list-billing"
            )
            technical_issue = _make_issue(
                db, category=IssueCategory.technical, suffix="list-technical"
            )
            billing_id = billing_issue.id
            technical_id = technical_issue.id

        resp = client.get(f"{BASE}/issues?category=billing")
        assert resp.status_code == 200
        ids = [i["id"] for i in resp.json()]
        assert billing_id in ids
        assert technical_id not in ids

    def test_limit_respected(self, client):
        resp = client.get(f"{BASE}/issues?limit=2")
        assert resp.status_code == 200
        assert len(resp.json()) <= 2


# ---------------------------------------------------------------------------
# Issue detail
# ---------------------------------------------------------------------------


class TestIssueDetail:
    def test_get_404_for_nonexistent(self, client):
        assert client.get(f"{BASE}/issues/999999").status_code == 404

    def test_get_existing_issue(self, client):
        with _db_session(client) as db:
            issue = _make_issue(db, suffix="detail-get")

        resp = client.get(f"{BASE}/issues/{issue.id}")
        assert resp.status_code == 200
        data = resp.json()
        assert data["id"] == issue.id
        assert data["title"] == issue.title

    def test_issue_response_shape(self, client):
        with _db_session(client) as db:
            issue = _make_issue(db, suffix="detail-shape")

        resp = client.get(f"{BASE}/issues/{issue.id}")
        data = resp.json()
        required = {
            "id", "title", "description", "category", "status", "priority",
            "created_at", "updated_at",
        }
        missing = required - set(data.keys())
        assert not missing, f"Missing fields in issue response: {missing}"

    def test_defaults_in_response(self, client):
        """resolution and assigned_to default to None; resolved_at defaults to None."""
        with _db_session(client) as db:
            issue = _make_issue(db, suffix="defaults")

        data = client.get(f"{BASE}/issues/{issue.id}").json()
        assert data["resolution"] is None
        assert data["assigned_to"] is None
        assert data["resolved_at"] is None


# ---------------------------------------------------------------------------
# Issue update (PATCH)
# ---------------------------------------------------------------------------


class TestIssueUpdate:
    def test_update_404_for_nonexistent(self, client):
        resp = client.patch(f"{BASE}/issues/999999", json={"status": "resolved"})
        assert resp.status_code == 404

    def test_update_status_to_in_progress(self, client):
        with _db_session(client) as db:
            issue = _make_issue(db, suffix="upd-status")

        resp = client.patch(f"{BASE}/issues/{issue.id}", json={"status": "in_progress"})
        assert resp.status_code == 200
        assert resp.json()["status"] == "in_progress"

    def test_update_priority(self, client):
        with _db_session(client) as db:
            issue = _make_issue(db, suffix="upd-priority")

        resp = client.patch(f"{BASE}/issues/{issue.id}", json={"priority": "high"})
        assert resp.status_code == 200
        assert resp.json()["priority"] == "high"

    def test_update_assigned_to(self, client):
        with _db_session(client) as db:
            issue = _make_issue(db, suffix="upd-assign")

        resp = client.patch(f"{BASE}/issues/{issue.id}", json={"assigned_to": "bob@adtech.com"})
        assert resp.status_code == 200
        assert resp.json()["assigned_to"] == "bob@adtech.com"

    def test_update_resolution_text(self, client):
        with _db_session(client) as db:
            issue = _make_issue(db, suffix="upd-resolution")

        resp = client.patch(
            f"{BASE}/issues/{issue.id}",
            json={
                "status": "resolved",
                "resolution": "Delivery pipeline restarted; impressions normalised.",
            },
        )
        assert resp.status_code == 200
        data = resp.json()
        assert data["status"] == "resolved"
        assert "restarted" in data["resolution"]

    def test_partial_update_preserves_other_fields(self, client):
        """Patching only priority must not change status."""
        with _db_session(client) as db:
            issue = _make_issue(db, suffix="upd-partial")
            original_status = issue.status

        resp = client.patch(f"{BASE}/issues/{issue.id}", json={"priority": "low"})
        assert resp.status_code == 200
        data = resp.json()
        assert data["priority"] == "low"
        assert data["status"] == original_status.value


# ---------------------------------------------------------------------------
# Advertiser list
# ---------------------------------------------------------------------------


class TestAdvertiserList:
    def test_returns_200_as_list(self, client):
        resp = client.get(f"{BASE}/advertisers")
        assert resp.status_code == 200
        assert isinstance(resp.json(), list)

    def test_advertiser_appears_in_list(self, client):
        with _db_session(client) as db:
            adv = _make_advertiser(db, suffix="list-adv-001")

        resp = client.get(f"{BASE}/advertisers")
        assert resp.status_code == 200
        ids = [a["id"] for a in resp.json()]
        assert adv.id in ids

    def test_advertiser_response_shape(self, client):
        with _db_session(client) as db:
            adv = _make_advertiser(db, suffix="adv-shape")

        resp = client.get(f"{BASE}/advertisers")
        assert resp.status_code == 200
        items = resp.json()
        target = next((a for a in items if a["id"] == adv.id), None)
        assert target is not None
        required = {
            "id", "name", "industry", "contact_name", "contact_email",
            "budget_tier", "created_at", "updated_at",
        }
        missing = required - set(target.keys())
        assert not missing, f"Missing fields in advertiser response: {missing}"

    def test_advertisers_ordered_by_name(self, client):
        """The route orders by name alphabetically; verify names in list are sorted."""
        resp = client.get(f"{BASE}/advertisers")
        assert resp.status_code == 200
        names = [a["name"] for a in resp.json()]
        assert names == sorted(names), "Advertisers should be alphabetically sorted"


# ---------------------------------------------------------------------------
# Contract list
# ---------------------------------------------------------------------------


class TestContractList:
    def test_returns_200_as_list(self, client):
        resp = client.get(f"{BASE}/contracts")
        assert resp.status_code == 200
        assert isinstance(resp.json(), list)

    def test_contract_appears_in_list(self, client):
        from innovation_factory.backend.projects.adtech_intelligence.models import (
            AtCustomerContract,
            ContractStatus,
        )

        with _db_session(client) as db:
            adv = _make_advertiser(db, suffix="contract-list")
            contract = AtCustomerContract(
                advertiser_id=adv.id,
                contract_number="CN-TEST-0001",
                contract_type="annual",
                start_date=date(2026, 1, 1),
                end_date=date(2026, 12, 31),
                total_value=500000.0,
                status=ContractStatus.active,
            )
            db.add(contract)
            db.commit()
            db.refresh(contract)

        resp = client.get(f"{BASE}/contracts")
        assert resp.status_code == 200
        ids = [c["id"] for c in resp.json()]
        assert contract.id in ids

    def test_filter_contracts_by_advertiser_id(self, client):
        from innovation_factory.backend.projects.adtech_intelligence.models import (
            AtCustomerContract,
            ContractStatus,
        )

        with _db_session(client) as db:
            adv1 = _make_advertiser(db, suffix="contr-adv1")
            adv2 = _make_advertiser(db, suffix="contr-adv2")
            c1 = AtCustomerContract(
                advertiser_id=adv1.id,
                contract_number="CN-ADV1-0001",
                contract_type="annual",
                start_date=date(2026, 1, 1),
                end_date=date(2026, 12, 31),
                total_value=200000.0,
            )
            c2 = AtCustomerContract(
                advertiser_id=adv2.id,
                contract_number="CN-ADV2-0001",
                contract_type="project",
                start_date=date(2026, 3, 1),
                end_date=date(2026, 9, 30),
                total_value=100000.0,
            )
            db.add(c1)
            db.add(c2)
            db.commit()
            db.refresh(c1)
            db.refresh(c2)
            # Capture IDs while session is still open (avoids DetachedInstanceError)
            adv1_id = adv1.id
            c1_id = c1.id
            c2_id = c2.id

        resp = client.get(f"{BASE}/contracts?advertiser_id={adv1_id}")
        assert resp.status_code == 200
        ids = [c["id"] for c in resp.json()]
        assert c1_id in ids
        assert c2_id not in ids

    def test_contract_response_shape(self, client):
        from innovation_factory.backend.projects.adtech_intelligence.models import (
            AtCustomerContract,
        )

        with _db_session(client) as db:
            adv = _make_advertiser(db, suffix="contr-shape")
            contract = AtCustomerContract(
                advertiser_id=adv.id,
                contract_number="CN-SHAPE-0001",
                contract_type="programmatic",
                start_date=date(2026, 1, 1),
                end_date=date(2026, 6, 30),
                total_value=75000.0,
            )
            db.add(contract)
            db.commit()
            db.refresh(contract)

        resp = client.get(f"{BASE}/contracts")
        items = resp.json()
        target = next((c for c in items if c["id"] == contract.id), None)
        assert target is not None
        required = {
            "id", "advertiser_id", "contract_number", "contract_type",
            "start_date", "end_date", "total_value", "status", "created_at",
        }
        missing = required - set(target.keys())
        assert not missing, f"Missing fields in contract response: {missing}"
