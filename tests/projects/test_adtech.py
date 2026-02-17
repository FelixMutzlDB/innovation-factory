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

    def test_databricks_resources(self, client):
        resp = client.get("/api/projects/adtech-intelligence/databricks-resources")
        assert resp.status_code == 200
        data = resp.json()
        assert "dashboard_embed_url" in data or "workspace_url" in data
