"""Campaign, placement, and dashboard-summary route tests for AdTech Intelligence.

Covers:
- Dashboard summary endpoint: shape, zero-state aggregation, non-zero aggregation
- Campaign list: empty state, status filter, type filter, advertiser filter
- Campaign get: 404 for unknown ID
- Campaign update: status patch, budget patch, 404 for unknown ID
- Placement list: empty list for campaign, 404 for unknown placement
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
    """Obtain the in-memory session that the test client uses for data setup."""
    from innovation_factory.backend.app import app
    from innovation_factory.backend.dependencies import get_session

    override = app.dependency_overrides.get(get_session)
    assert override is not None, "get_session override not set in client fixture"
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
        name=f"Test Corp {suffix}",
        industry="tech",
        contact_name=f"Contact {suffix}",
        contact_email=f"test{suffix}@adtech-test.com",
        budget_tier="standard",
    )
    db.add(adv)
    db.commit()
    db.refresh(adv)
    return adv


def _make_campaign(db, advertiser_id: int, *, status=None, campaign_type=None, suffix: str = ""):
    from innovation_factory.backend.projects.adtech_intelligence.models import (
        AtCampaign,
        CampaignStatus,
        CampaignType,
    )

    camp = AtCampaign(
        advertiser_id=advertiser_id,
        name=f"Campaign {suffix}",
        campaign_type=campaign_type or CampaignType.online,
        status=status or CampaignStatus.draft,
        budget=10000.0,
        spent=500.0,
        start_date=date(2026, 1, 1),
        end_date=date(2026, 12, 31),
    )
    db.add(camp)
    db.commit()
    db.refresh(camp)
    return camp


BASE = "/api/projects/adtech-intelligence"


# ---------------------------------------------------------------------------
# Dashboard summary
# ---------------------------------------------------------------------------


class TestDashboardSummary:
    def test_returns_200_with_correct_shape(self, client):
        resp = client.get(f"{BASE}/dashboard/summary")
        assert resp.status_code == 200
        data = resp.json()
        expected_fields = {
            "total_campaigns",
            "active_campaigns",
            "total_inventory",
            "available_inventory",
            "total_spend",
            "total_impressions",
            "avg_ctr",
            "active_anomalies",
            "critical_anomalies",
        }
        assert expected_fields <= set(data.keys()), (
            f"Missing fields: {expected_fields - set(data.keys())}"
        )

    def test_all_numeric_values(self, client):
        resp = client.get(f"{BASE}/dashboard/summary")
        assert resp.status_code == 200
        data = resp.json()
        for key in ("total_campaigns", "active_campaigns", "total_inventory",
                    "available_inventory", "total_impressions",
                    "active_anomalies", "critical_anomalies"):
            assert isinstance(data[key], int), f"{key} should be int, got {type(data[key])}"
        for key in ("total_spend", "avg_ctr"):
            assert isinstance(data[key], (int, float)), f"{key} should be numeric"

    def test_active_campaigns_subset_of_total(self, client):
        """active_campaigns must never exceed total_campaigns."""
        resp = client.get(f"{BASE}/dashboard/summary")
        assert resp.status_code == 200
        data = resp.json()
        assert data["active_campaigns"] <= data["total_campaigns"]

    def test_critical_anomalies_subset_of_active(self, client):
        """critical_anomalies is a subset of active_anomalies."""
        resp = client.get(f"{BASE}/dashboard/summary")
        assert resp.status_code == 200
        data = resp.json()
        assert data["critical_anomalies"] <= data["active_anomalies"]

    def test_active_campaign_counted_in_total(self, client):
        """After adding an active campaign, total_campaigns increases by at least 1."""
        before = client.get(f"{BASE}/dashboard/summary").json()
        total_before = before["total_campaigns"]
        active_before = before["active_campaigns"]

        with _db_session(client) as db:
            adv = _make_advertiser(db, suffix="sum-active")
            from innovation_factory.backend.projects.adtech_intelligence.models import CampaignStatus
            _make_campaign(db, adv.id, status=CampaignStatus.active, suffix="sum-act")

        after = client.get(f"{BASE}/dashboard/summary").json()
        assert after["total_campaigns"] >= total_before + 1
        assert after["active_campaigns"] >= active_before + 1


# ---------------------------------------------------------------------------
# Campaign list
# ---------------------------------------------------------------------------


class TestCampaignList:
    def test_returns_200_as_list(self, client):
        resp = client.get(f"{BASE}/campaigns")
        assert resp.status_code == 200
        assert isinstance(resp.json(), list)

    def test_filter_by_active_status(self, client):
        from innovation_factory.backend.projects.adtech_intelligence.models import CampaignStatus

        with _db_session(client) as db:
            adv = _make_advertiser(db, suffix="filt-active")
            camp = _make_campaign(db, adv.id, status=CampaignStatus.active, suffix="filt-act-001")

        resp = client.get(f"{BASE}/campaigns?status=active")
        assert resp.status_code == 200
        items = resp.json()
        ids = [i["id"] for i in items]
        assert camp.id in ids, "Active campaign not returned by status=active filter"
        # All returned items must have active status
        for item in items:
            assert item["status"] == "active"

    def test_filter_by_paused_excludes_active(self, client):
        from innovation_factory.backend.projects.adtech_intelligence.models import CampaignStatus

        with _db_session(client) as db:
            adv = _make_advertiser(db, suffix="filt-excl")
            active_camp = _make_campaign(db, adv.id, status=CampaignStatus.active, suffix="excl-act")

        resp = client.get(f"{BASE}/campaigns?status=paused")
        assert resp.status_code == 200
        ids = [i["id"] for i in resp.json()]
        assert active_camp.id not in ids, "Active campaign should not appear under status=paused"

    def test_filter_by_campaign_type(self, client):
        from innovation_factory.backend.projects.adtech_intelligence.models import CampaignType

        with _db_session(client) as db:
            adv = _make_advertiser(db, suffix="filt-outdoor")
            camp = _make_campaign(db, adv.id, campaign_type=CampaignType.outdoor, suffix="outdoor-001")

        resp = client.get(f"{BASE}/campaigns?campaign_type=outdoor")
        assert resp.status_code == 200
        items = resp.json()
        ids = [i["id"] for i in items]
        assert camp.id in ids
        for item in items:
            assert item["campaign_type"] == "outdoor"

    def test_filter_by_advertiser_id(self, client):
        with _db_session(client) as db:
            adv = _make_advertiser(db, suffix="filt-adv-id")
            camp = _make_campaign(db, adv.id, suffix="adv-filt-001")
            # Capture IDs while session is still open (avoids DetachedInstanceError)
            adv_id = adv.id
            camp_id = camp.id

        resp = client.get(f"{BASE}/campaigns?advertiser_id={adv_id}")
        assert resp.status_code == 200
        items = resp.json()
        assert len(items) >= 1
        ids = [i["id"] for i in items]
        assert camp_id in ids
        for item in items:
            assert item["advertiser_id"] == adv_id

    def test_limit_respected(self, client):
        resp = client.get(f"{BASE}/campaigns?limit=2")
        assert resp.status_code == 200
        assert len(resp.json()) <= 2

    def test_offset_pagination(self, client):
        resp_all = client.get(f"{BASE}/campaigns?limit=50")
        resp_paged = client.get(f"{BASE}/campaigns?limit=50&offset=1")
        assert resp_all.status_code == 200
        assert resp_paged.status_code == 200
        all_ids = [i["id"] for i in resp_all.json()]
        paged_ids = [i["id"] for i in resp_paged.json()]
        if len(all_ids) > 1:
            assert paged_ids == all_ids[1:], "Offset=1 should skip the first item"


# ---------------------------------------------------------------------------
# Campaign detail
# ---------------------------------------------------------------------------


class TestCampaignDetail:
    def test_get_existing_campaign(self, client):
        with _db_session(client) as db:
            adv = _make_advertiser(db, suffix="detail-get")
            camp = _make_campaign(db, adv.id, suffix="detail-001")

        resp = client.get(f"{BASE}/campaigns/{camp.id}")
        assert resp.status_code == 200
        data = resp.json()
        assert data["id"] == camp.id
        assert data["name"] == camp.name

    def test_get_404_for_nonexistent_campaign(self, client):
        resp = client.get(f"{BASE}/campaigns/999999")
        assert resp.status_code == 404

    def test_campaign_response_contains_expected_fields(self, client):
        with _db_session(client) as db:
            adv = _make_advertiser(db, suffix="detail-shape")
            camp = _make_campaign(db, adv.id, suffix="shape-001")

        resp = client.get(f"{BASE}/campaigns/{camp.id}")
        assert resp.status_code == 200
        data = resp.json()
        for field in ("id", "advertiser_id", "name", "campaign_type", "status",
                      "budget", "spent", "start_date", "end_date", "created_at", "updated_at"):
            assert field in data, f"Field '{field}' missing from campaign response"


# ---------------------------------------------------------------------------
# Campaign update (PATCH)
# ---------------------------------------------------------------------------


class TestCampaignUpdate:
    def test_update_status(self, client):
        from innovation_factory.backend.projects.adtech_intelligence.models import (
            CampaignStatus,
        )

        with _db_session(client) as db:
            adv = _make_advertiser(db, suffix="upd-status")
            camp = _make_campaign(db, adv.id, status=CampaignStatus.draft, suffix="upd-stat-001")

        resp = client.patch(
            f"{BASE}/campaigns/{camp.id}",
            json={"status": "active"},
        )
        assert resp.status_code == 200
        data = resp.json()
        assert data["status"] == "active"

    def test_update_budget(self, client):
        with _db_session(client) as db:
            adv = _make_advertiser(db, suffix="upd-budget")
            camp = _make_campaign(db, adv.id, suffix="upd-bud-001")

        resp = client.patch(
            f"{BASE}/campaigns/{camp.id}",
            json={"budget": 99999.0},
        )
        assert resp.status_code == 200
        assert resp.json()["budget"] == pytest.approx(99999.0)

    def test_update_spent(self, client):
        with _db_session(client) as db:
            adv = _make_advertiser(db, suffix="upd-spent")
            camp = _make_campaign(db, adv.id, suffix="upd-spent-001")

        resp = client.patch(
            f"{BASE}/campaigns/{camp.id}",
            json={"spent": 7500.0},
        )
        assert resp.status_code == 200
        assert resp.json()["spent"] == pytest.approx(7500.0)

    def test_update_404_for_nonexistent(self, client):
        resp = client.patch(f"{BASE}/campaigns/999999", json={"status": "active"})
        assert resp.status_code == 404

    def test_partial_update_does_not_clear_other_fields(self, client):
        """Patching only status must not zero out budget."""
        with _db_session(client) as db:
            adv = _make_advertiser(db, suffix="upd-partial")
            camp = _make_campaign(db, adv.id, suffix="upd-part-001")
            original_budget = camp.budget

        resp = client.patch(f"{BASE}/campaigns/{camp.id}", json={"status": "paused"})
        assert resp.status_code == 200
        data = resp.json()
        assert data["budget"] == pytest.approx(original_budget)
        assert data["status"] == "paused"


# ---------------------------------------------------------------------------
# Placements
# ---------------------------------------------------------------------------


class TestPlacements:
    def test_list_placements_empty_for_new_campaign(self, client):
        with _db_session(client) as db:
            adv = _make_advertiser(db, suffix="plcmt-empty")
            camp = _make_campaign(db, adv.id, suffix="plcmt-001")

        resp = client.get(f"{BASE}/campaigns/{camp.id}/placements")
        assert resp.status_code == 200
        assert resp.json() == []

    def test_get_placement_404(self, client):
        resp = client.get(f"{BASE}/placements/999999")
        assert resp.status_code == 404

    def test_placement_created_and_listed(self, client):
        from innovation_factory.backend.projects.adtech_intelligence.models import (
            AtAdInventory,
            AtPlacement,
            InventoryStatus,
            InventoryType,
            LocationType,
        )

        with _db_session(client) as db:
            adv = _make_advertiser(db, suffix="plcmt-list")
            camp = _make_campaign(db, adv.id, suffix="plcmt-list-001")
            inv = AtAdInventory(
                name="Test Screen Berlin",
                inventory_type=InventoryType.dooh_screen,
                location_type=LocationType.train_station,
                status=InventoryStatus.available,
                daily_impressions_est=50000,
                cpm_rate=12.50,
            )
            db.add(inv)
            db.commit()
            db.refresh(inv)
            placement = AtPlacement(
                campaign_id=camp.id,
                inventory_id=inv.id,
                start_date=date(2026, 3, 1),
                end_date=date(2026, 3, 31),
                daily_budget=500.0,
            )
            db.add(placement)
            db.commit()
            db.refresh(placement)
            # Capture IDs while session is still open (avoids DetachedInstanceError)
            camp_id = camp.id
            placement_id = placement.id

        resp = client.get(f"{BASE}/campaigns/{camp_id}/placements")
        assert resp.status_code == 200
        items = resp.json()
        assert len(items) == 1
        assert items[0]["id"] == placement_id
        assert items[0]["campaign_id"] == camp_id

    def test_get_placement_ok(self, client):
        from innovation_factory.backend.projects.adtech_intelligence.models import (
            AtAdInventory,
            AtPlacement,
            InventoryStatus,
            InventoryType,
            LocationType,
        )

        with _db_session(client) as db:
            adv = _make_advertiser(db, suffix="plcmt-get")
            camp = _make_campaign(db, adv.id, suffix="plcmt-get-001")
            inv = AtAdInventory(
                name="Test Billboard Hamburg",
                inventory_type=InventoryType.billboard,
                location_type=LocationType.highway,
                status=InventoryStatus.available,
                daily_impressions_est=20000,
                cpm_rate=8.0,
            )
            db.add(inv)
            db.commit()
            db.refresh(inv)
            placement = AtPlacement(
                campaign_id=camp.id,
                inventory_id=inv.id,
                start_date=date(2026, 4, 1),
                end_date=date(2026, 4, 30),
                daily_budget=200.0,
            )
            db.add(placement)
            db.commit()
            db.refresh(placement)

        resp = client.get(f"{BASE}/placements/{placement.id}")
        assert resp.status_code == 200
        data = resp.json()
        assert data["id"] == placement.id
        assert data["daily_budget"] == pytest.approx(200.0)
