"""AdTech Intelligence specific tests."""
import pytest
from datetime import date

from innovation_factory.backend.projects.adtech_intelligence.models import (
    AtAdvertiser,
    AtCampaign,
    CampaignStatus,
    CampaignType,
)


class TestAdTechModels:
    def test_advertiser_creation(self, session):
        adv = AtAdvertiser(
            name="Test Corp",
            industry="tech",
            contact_name="Test Contact",
            contact_email="test@corp.com",
            budget_tier="premium",
        )
        session.add(adv)
        session.flush()
        assert adv.id is not None

    def test_campaign_with_advertiser(self, session):
        adv = AtAdvertiser(
            name="Corp2",
            industry="retail",
            contact_name="Corp2 Contact",
            contact_email="c2@corp.com",
            budget_tier="standard",
        )
        session.add(adv)
        session.flush()
        camp = AtCampaign(
            advertiser_id=adv.id,
            name="Summer Sale",
            campaign_type=CampaignType.online,
            status=CampaignStatus.active,
            budget=50000,
            spent=10000,
            start_date=date.today(),
            end_date=date.today(),
        )
        session.add(camp)
        session.flush()
        assert camp.id is not None
        assert camp.advertiser_id == adv.id


class TestAdTechAPI:
    def test_dashboard_summary(self, client):
        resp = client.get("/api/projects/adtech-intelligence/dashboard/summary")
        assert resp.status_code == 200

    def test_anomaly_counts(self, client):
        resp = client.get("/api/projects/adtech-intelligence/anomalies/counts")
        assert resp.status_code == 200

    def test_databricks_resources_unset_returns_empty_and_unconfigured(self, client):
        # Mirror the AECO-hub test pattern: without env vars set, the endpoint
        # must respond 200 with empty values and `configured=False` — not
        # raise, not 500, not synthesize bogus URLs.
        resp = client.get("/api/projects/adtech-intelligence/databricks-resources")
        assert resp.status_code == 200
        data = resp.json()
        assert data["workspace_url"] == ""
        assert data["dashboard_id"] == ""
        assert data["genie_space_id"] == ""
        assert data["dashboard_embed_url"] == ""
        assert data["configured"] is False

    def test_databricks_resources_embed_url_composition(self, client, monkeypatch):
        # When workspace_url + dashboard_id are configured, the embed URL must
        # be well-formed: https://, /embed/dashboardsv3/, dashboard_id present.
        # Patches the router-module bindings (the `from … import WORKSPACE_URL`
        # style copies the value into the importing module's namespace).
        router_mod = "innovation_factory.backend.projects.adtech_intelligence.router"
        monkeypatch.setattr(f"{router_mod}.WORKSPACE_URL", "test-ws.cloud.databricks.com")
        monkeypatch.setattr(f"{router_mod}.DASHBOARD_ID", "dash-test-123")
        monkeypatch.setattr(f"{router_mod}.GENIE_SPACE_ID", "genie-test-456")

        resp = client.get("/api/projects/adtech-intelligence/databricks-resources")
        assert resp.status_code == 200
        data = resp.json()
        assert data["workspace_url"] == "test-ws.cloud.databricks.com"
        assert data["dashboard_id"] == "dash-test-123"
        assert data["genie_space_id"] == "genie-test-456"
        assert data["dashboard_embed_url"].startswith("https://")
        assert "/embed/dashboardsv3/" in data["dashboard_embed_url"]
        assert data["dashboard_id"] in data["dashboard_embed_url"]
        assert data["configured"] is True
