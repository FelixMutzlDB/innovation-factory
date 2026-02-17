"""MOL ASM Cockpit specific tests."""
import pytest
from innovation_factory.backend.projects.mol_asm_cockpit.models import (
    MacRegion,
    MacStation,
    MacAlertSeverity,
    MacAlertStatus,
    MacIssueStatus,
    StationType,
)


class TestMolAsmModels:
    def test_region_and_station(self, session):
        r = MacRegion(name="West Hungary", country="HU")
        session.add(r)
        session.flush()
        s = MacStation(
            station_code="HU-WH-001",
            name="Test Station",
            city="Győr",
            region_id=r.id,
            station_type=StationType.urban,
            has_fresh_corner=True,
            has_ev_charging=False,
            num_pumps=6,
            latitude=47.68,
            longitude=17.63,
        )
        session.add(s)
        session.flush()
        assert s.id is not None
        assert s.region_id == r.id

    def test_enum_values(self):
        assert MacAlertSeverity.critical == "critical"
        assert MacAlertStatus.active == "active"
        assert MacIssueStatus.open == "open"


class TestMolAsmAPI:
    def test_regions_list(self, client):
        resp = client.get("/api/projects/mol-asm-cockpit/stations/regions")
        assert resp.status_code == 200

    def test_stations_list(self, client):
        resp = client.get("/api/projects/mol-asm-cockpit/stations")
        assert resp.status_code == 200

    def test_dashboard_embed(self, client):
        resp = client.get("/api/projects/mol-asm-cockpit/dashboard/embed")
        assert resp.status_code == 200
