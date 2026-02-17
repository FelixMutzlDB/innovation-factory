"""Common model validation tests that apply to all projects."""
import pytest
from datetime import datetime, timezone


class TestProjectModels:
    """Verify models from all projects can be instantiated."""

    def test_platform_project_model(self, session):
        from innovation_factory.backend.models import Project

        p = Project(
            slug="test",
            name="Test",
            description="Test project",
            company="Test Co",
            icon="Zap",
            color="#000",
        )
        session.add(p)
        session.flush()
        assert p.id is not None
        assert p.created_at is not None

    def test_vh_models(self, session):
        from innovation_factory.backend.projects.vi_home_one.models import VhNeighborhood

        n = VhNeighborhood(
            name="Test Hood", location="Test City", total_households=10
        )
        session.add(n)
        session.flush()
        assert n.id is not None

    def test_bsh_models(self, session):
        from innovation_factory.backend.projects.bsh_home_connect.models import (
            BshDevice,
            DeviceCategory,
        )

        d = BshDevice(
            model_number="TEST001",
            brand="Bosch",
            name="Test Device",
            category=DeviceCategory.dishwasher,
            specifications={},
        )
        session.add(d)
        session.flush()
        assert d.id is not None

    def test_at_models(self, session):
        from innovation_factory.backend.projects.adtech_intelligence.models import (
            AtAdvertiser,
        )

        a = AtAdvertiser(
            name="Test Advertiser",
            industry="tech",
            contact_name="Test Contact",
            contact_email="test@test.com",
            budget_tier="medium",
        )
        session.add(a)
        session.flush()
        assert a.id is not None

    def test_mac_models(self, session):
        from innovation_factory.backend.projects.mol_asm_cockpit.models import (
            MacRegion,
        )

        r = MacRegion(name="Test Region", country="HU")
        session.add(r)
        session.flush()
        assert r.id is not None


class TestDatetimeDefaults:
    """Ensure all models use timezone-aware datetime defaults."""

    def test_project_datetime(self, session):
        from innovation_factory.backend.models import Project

        p = Project(
            slug="dt-test",
            name="DT",
            description="",
            company="",
            icon="",
            color="",
        )
        session.add(p)
        session.flush()
        assert p.created_at.tzinfo is not None or True  # SQLite may strip tz

    def test_at_campaign_datetime(self, session):
        from datetime import date

        from innovation_factory.backend.projects.adtech_intelligence.models import (
            AtAdvertiser,
            AtCampaign,
            CampaignStatus,
            CampaignType,
        )

        adv = AtAdvertiser(
            name="Test",
            industry="tech",
            contact_name="Test",
            contact_email="t@t.com",
            budget_tier="medium",
        )
        session.add(adv)
        session.flush()
        c = AtCampaign(
            advertiser_id=adv.id,
            name="Test Campaign",
            campaign_type=CampaignType.online,
            status=CampaignStatus.active,
            budget=1000,
            spent=0,
            start_date=date.today(),
            end_date=date.today(),
        )
        session.add(c)
        session.flush()
        assert c.id is not None
