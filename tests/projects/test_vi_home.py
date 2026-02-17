"""ViHome One specific tests."""
import pytest
from innovation_factory.backend.projects.vi_home_one.models import (
    VhNeighborhood,
    VhHousehold,
)


class TestViHomeModels:
    def test_neighborhood_and_household(self, session):
        n = VhNeighborhood(
            name="Solar Valley",
            location="Munich",
            total_households=20,
        )
        session.add(n)
        session.flush()
        h = VhHousehold(
            neighborhood_id=n.id,
            owner_name="Max Mustermann",
            address="Solarstr. 1",
            has_pv=True,
            has_battery=True,
            has_ev=False,
            has_heat_pump=True,
        )
        session.add(h)
        session.flush()
        assert h.id is not None
        assert h.neighborhood_id == n.id


class TestViHomeAPI:
    def test_neighborhoods_list(self, client):
        resp = client.get("/api/projects/vi-home-one/neighborhoods")
        assert resp.status_code == 200

    def test_providers_list(self, client):
        resp = client.get("/api/projects/vi-home-one/providers")
        assert resp.status_code == 200
