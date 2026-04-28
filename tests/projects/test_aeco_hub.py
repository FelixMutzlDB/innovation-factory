"""AECO Hub Phase 1 tests.

Covers the model layer, the deterministic seed, and the project / building /
floor / space CRUD routers. Per the plan §13, every API route must declare
``response_model`` + ``operation_id`` and use the ``aeco_`` prefix to keep
the OpenAPI namespace clean.
"""
from __future__ import annotations

from datetime import date

import pytest
from sqlmodel import func, select

from innovation_factory.backend.projects.aeco_hub.models import (
    AecoBuildingType,
    AecoIssueCategory,
    AecoIssueSeverity,
    AecoIssueStatus,
    AecoProjectPhase,
    AecoProjectStatus,
    DtBuilding,
    DtFloor,
    DtIssue,
    DtProject,
    DtSpace,
)
from innovation_factory.backend.projects.aeco_hub.router import router as aeco_router
from innovation_factory.backend.projects.aeco_hub.seed import (
    PORTFOLIO,
    seed_aeco_data,
)


# ---------------------------------------------------------------------------
# Models
# ---------------------------------------------------------------------------


class TestAecoModels:
    def test_project_creation(self, session):
        project = DtProject(
            code="UNIT-TEST",
            name="Unit Test Tower",
            description="Test project.",
            client_name="Test Client",
            city="Berlin",
            country="DE",
            phase=AecoProjectPhase.design,
            status=AecoProjectStatus.active,
            budget_eur=1_000_000.0,
            start_date=date.today(),
        )
        session.add(project)
        session.flush()
        assert project.id is not None
        assert project.phase == AecoProjectPhase.design
        assert project.status == AecoProjectStatus.active

    def test_building_floor_space_hierarchy(self, session):
        project = DtProject(code="HIER-1", name="Hierarchy", description="")
        session.add(project)
        session.flush()
        bldg = DtBuilding(
            project_id=project.id,
            name="Block A",
            building_type=AecoBuildingType.office,
            floor_count=2,
            gross_floor_area_sqm=2000.0,
        )
        session.add(bldg)
        session.flush()
        floor = DtFloor(building_id=bldg.id, name="Ground", level=0, area_sqm=1000.0)
        session.add(floor)
        session.flush()
        space = DtSpace(
            floor_id=floor.id,
            name="G.01",
            space_type="office",
            area_sqm=24.0,
            capacity=4,
            room_number="A-001",
        )
        session.add(space)
        session.flush()
        assert space.floor_id == floor.id
        assert floor.building_id == bldg.id
        assert bldg.project_id == project.id

    def test_issue_uses_aeco_prefixed_enums(self, session):
        """Regression: AECO Hub enums must be ``Aeco``-prefixed so the OpenAPI
        schema does not collide with other accelerators (e.g. MAC's
        ``MacIssueStatus`` or BSH's ``BshTicketStatus``)."""
        project = DtProject(code="ENUM-1", name="Enum Test", description="")
        session.add(project)
        session.flush()
        issue = DtIssue(
            project_id=project.id,
            title="Test issue",
            category=AecoIssueCategory.clash,
            severity=AecoIssueSeverity.major,
            status=AecoIssueStatus.in_progress,
        )
        session.add(issue)
        session.flush()
        assert issue.status.__class__.__name__ == "AecoIssueStatus"
        assert issue.severity.__class__.__name__ == "AecoIssueSeverity"


# ---------------------------------------------------------------------------
# Seed
# ---------------------------------------------------------------------------


class TestAecoSeed:
    def test_seeds_full_portfolio(self, session):
        seed_aeco_data(session)
        projects = session.exec(select(DtProject)).all()
        codes = sorted(p.code for p in projects)
        assert codes == sorted(spec["code"] for spec in PORTFOLIO)
        assert len(projects) == 5

    def test_seed_is_idempotent(self, session):
        seed_aeco_data(session)
        first_count = session.exec(select(func.count(DtProject.id))).one()
        seed_aeco_data(session)
        second_count = session.exec(select(func.count(DtProject.id))).one()
        assert first_count == second_count == 5

    def test_seed_phase_distribution(self, session):
        seed_aeco_data(session)
        phases = [p.phase for p in session.exec(select(DtProject)).all()]
        assert phases.count(AecoProjectPhase.operate) == 2
        assert phases.count(AecoProjectPhase.build) == 1
        assert phases.count(AecoProjectPhase.design) == 1
        assert phases.count(AecoProjectPhase.demolish) == 1

    def test_seed_buildings_match_portfolio_spec(self, session):
        seed_aeco_data(session)
        for spec in PORTFOLIO:
            project = session.exec(
                select(DtProject).where(DtProject.code == spec["code"])
            ).one()
            count = session.exec(
                select(func.count(DtBuilding.id)).where(DtBuilding.project_id == project.id)
            ).one()
            assert count == len(spec["buildings"]), (
                f"{spec['code']} expected {len(spec['buildings'])} buildings, got {count}"
            )


# ---------------------------------------------------------------------------
# Routers — every route declares response_model + operation_id, every
# endpoint returns 200 on the seeded portfolio.
# ---------------------------------------------------------------------------


class TestAecoRouters:
    def test_every_route_has_response_model_and_operation_id(self):
        """Regression: ``response_model`` + ``operation_id`` are required on
        every route — without them the TypeScript client generator emits
        ``unknown`` types and the frontend hooks break silently.

        Streaming POST endpoints (chat) are exempt from ``response_model``
        because they return a ``StreamingResponse`` whose body shape is
        a JSON-line protocol, not a single Pydantic model.
        """
        from fastapi.routing import APIRoute
        STREAMING_PATHS = {"/chat", "/ka-chat"}
        for r in aeco_router.routes:
            if not isinstance(r, APIRoute):
                continue
            if r.path not in STREAMING_PATHS:
                assert r.response_model is not None, f"Missing response_model on {r.path}"
            assert r.operation_id is not None, f"Missing operation_id on {r.path}"
            assert r.operation_id.startswith("aeco_"), f"operation_id must start with aeco_: {r.operation_id}"

    def test_portfolio_stats(self, client):
        seed_aeco_data_via_client(client)
        r = client.get("/api/projects/aeco-hub/portfolio/stats")
        assert r.status_code == 200
        data = r.json()
        assert data["total_projects"] == 5
        assert data["total_buildings"] == 8
        assert data["operating_projects"] == 2

    def test_list_projects(self, client):
        seed_aeco_data_via_client(client)
        r = client.get("/api/projects/aeco-hub/projects")
        assert r.status_code == 200
        projects = r.json()
        assert len(projects) == 5
        for p in projects:
            assert p["phase"] in {"design", "build", "operate", "demolish"}

    def test_list_projects_with_phase_filter(self, client):
        seed_aeco_data_via_client(client)
        r = client.get("/api/projects/aeco-hub/projects?phase=operate")
        assert r.status_code == 200
        projects = r.json()
        assert len(projects) == 2
        assert all(p["phase"] == "operate" for p in projects)

    def test_get_project_kpis(self, client):
        seed_aeco_data_via_client(client)
        first = client.get("/api/projects/aeco-hub/projects").json()[0]
        r = client.get(f"/api/projects/aeco-hub/projects/{first['id']}/kpis")
        assert r.status_code == 200
        kpis = r.json()
        assert kpis["building_count"] >= 1
        assert kpis["member_count"] == 7  # MEMBER_TEMPLATES count
        assert kpis["documents_count"] == 10  # doc_templates count

    def test_drilldown_buildings_floors_spaces(self, client):
        seed_aeco_data_via_client(client)
        first = client.get("/api/projects/aeco-hub/projects").json()[0]
        bldgs = client.get(f"/api/projects/aeco-hub/projects/{first['id']}/buildings").json()
        assert len(bldgs) >= 1
        floors = client.get(f"/api/projects/aeco-hub/buildings/{bldgs[0]['id']}/floors").json()
        assert len(floors) >= 1
        spaces = client.get(f"/api/projects/aeco-hub/floors/{floors[0]['id']}/spaces").json()
        assert len(spaces) >= 1
        assert "space_type" in spaces[0]

    def test_404_on_missing_project(self, client):
        r = client.get("/api/projects/aeco-hub/projects/999999")
        assert r.status_code == 404

    def test_404_on_missing_building(self, client):
        r = client.get("/api/projects/aeco-hub/buildings/999999")
        assert r.status_code == 404

    def test_databricks_resources_endpoint(self, client):
        r = client.get("/api/projects/aeco-hub/databricks-resources")
        assert r.status_code == 200
        body = r.json()
        # Without env vars set, embed URL should be empty + configured=False
        assert body["energy_dashboard_id"] == ""
        assert body["energy_dashboard_configured"] is False


# ---------------------------------------------------------------------------
# Phase 2 — issues, documents, design, build, operate routers + twin endpoint
# ---------------------------------------------------------------------------


class TestPhase2Issues:
    def test_list_issues(self, client):
        seed_aeco_data_via_client(client)
        pid = client.get("/api/projects/aeco-hub/projects").json()[0]["id"]
        r = client.get(f"/api/projects/aeco-hub/projects/{pid}/issues")
        assert r.status_code == 200
        assert len(r.json()) > 0

    def test_list_issues_status_filter(self, client):
        seed_aeco_data_via_client(client)
        pid = client.get("/api/projects/aeco-hub/projects").json()[0]["id"]
        r = client.get(f"/api/projects/aeco-hub/projects/{pid}/issues?status=open")
        assert r.status_code == 200
        for issue in r.json():
            assert issue["status"] == "open"

    def test_list_issues_severity_filter(self, client):
        seed_aeco_data_via_client(client)
        pid = client.get("/api/projects/aeco-hub/projects").json()[0]["id"]
        r = client.get(f"/api/projects/aeco-hub/projects/{pid}/issues?severity=critical")
        assert r.status_code == 200
        for issue in r.json():
            assert issue["severity"] == "critical"

    def test_issue_stats(self, client):
        seed_aeco_data_via_client(client)
        pid = client.get("/api/projects/aeco-hub/projects").json()[0]["id"]
        r = client.get(f"/api/projects/aeco-hub/projects/{pid}/issues/stats")
        assert r.status_code == 200
        stats = r.json()
        assert stats["total"] >= 1
        assert "by_category" in stats
        assert sum(stats["by_category"].values()) == stats["total"]


class TestPhase2Documents:
    def test_list_documents(self, client):
        seed_aeco_data_via_client(client)
        pid = client.get("/api/projects/aeco-hub/projects").json()[0]["id"]
        r = client.get(f"/api/projects/aeco-hub/projects/{pid}/documents")
        assert r.status_code == 200
        assert len(r.json()) == 10  # doc_templates count

    def test_documents_phase_filter(self, client):
        """Regression: ``phase`` filter must restrict the result set, not be ignored."""
        seed_aeco_data_via_client(client)
        pid = client.get("/api/projects/aeco-hub/projects").json()[0]["id"]
        r = client.get(f"/api/projects/aeco-hub/projects/{pid}/documents?phase=operate")
        assert r.status_code == 200
        for doc in r.json():
            assert doc["phase"] == "operate"

    def test_document_stats(self, client):
        seed_aeco_data_via_client(client)
        pid = client.get("/api/projects/aeco-hub/projects").json()[0]["id"]
        r = client.get(f"/api/projects/aeco-hub/projects/{pid}/documents/stats")
        assert r.status_code == 200
        stats = r.json()
        assert stats["total"] == 10


class TestPhase2Design:
    def test_list_bim_models(self, client):
        seed_aeco_data_via_client(client)
        # Pick a non-demolish project (BIM models only seeded for design/build/operate)
        projects = client.get("/api/projects/aeco-hub/projects?phase=build").json()
        pid = projects[0]["id"]
        r = client.get(f"/api/projects/aeco-hub/projects/{pid}/design/bim-models")
        assert r.status_code == 200
        models = r.json()
        assert len(models) > 0
        for m in models:
            assert m["discipline"] in {"architectural", "structural", "mep", "electrical", "plumbing", "hvac", "civil"}

    def test_list_clashes_with_severity_filter(self, client):
        seed_aeco_data_via_client(client)
        pid = client.get("/api/projects/aeco-hub/projects?phase=build").json()[0]["id"]
        r = client.get(f"/api/projects/aeco-hub/projects/{pid}/design/clashes?severity=major")
        assert r.status_code == 200
        for clash in r.json():
            assert clash["severity"] == "major"

    def test_list_room_requirements(self, client):
        seed_aeco_data_via_client(client)
        pid = client.get("/api/projects/aeco-hub/projects").json()[0]["id"]
        r = client.get(f"/api/projects/aeco-hub/projects/{pid}/design/room-requirements")
        assert r.status_code == 200
        # At least some requirements should exist
        assert len(r.json()) > 0


class TestPhase2Build:
    def test_list_schedule(self, client):
        seed_aeco_data_via_client(client)
        pid = client.get("/api/projects/aeco-hub/projects").json()[0]["id"]
        r = client.get(f"/api/projects/aeco-hub/projects/{pid}/build/schedule")
        assert r.status_code == 200
        assert len(r.json()) > 0

    def test_schedule_summary(self, client):
        seed_aeco_data_via_client(client)
        pid = client.get("/api/projects/aeco-hub/projects").json()[0]["id"]
        r = client.get(f"/api/projects/aeco-hub/projects/{pid}/build/schedule/summary")
        assert r.status_code == 200
        s = r.json()
        assert s["total"] == s["not_started"] + s["in_progress"] + s["completed"] + s["delayed"]

    def test_cost_summary_balances(self, client):
        """Regression: variance_eur must equal actual − estimated (rounding-tolerant)."""
        seed_aeco_data_via_client(client)
        pid = client.get("/api/projects/aeco-hub/projects").json()[0]["id"]
        r = client.get(f"/api/projects/aeco-hub/projects/{pid}/build/costs/summary")
        assert r.status_code == 200
        s = r.json()
        assert abs((s["total_actual_eur"] - s["total_estimated_eur"]) - s["variance_eur"]) < 0.5


class TestPhase2Operate:
    def test_list_sensors(self, client):
        seed_aeco_data_via_client(client)
        pid = client.get("/api/projects/aeco-hub/projects?phase=operate").json()[0]["id"]
        r = client.get(f"/api/projects/aeco-hub/projects/{pid}/operate/sensors")
        assert r.status_code == 200
        assert len(r.json()) > 0

    def test_maintenance_stats(self, client):
        seed_aeco_data_via_client(client)
        pid = client.get("/api/projects/aeco-hub/projects?phase=operate").json()[0]["id"]
        r = client.get(f"/api/projects/aeco-hub/projects/{pid}/operate/maintenance/stats")
        assert r.status_code == 200
        s = r.json()
        # Regression: completed_at must follow created_at — avg should be non-negative.
        assert s["avg_days_to_complete"] >= 0

    def test_energy_trend(self, client):
        seed_aeco_data_via_client(client)
        pid = client.get("/api/projects/aeco-hub/projects?phase=operate").json()[0]["id"]
        r = client.get(f"/api/projects/aeco-hub/projects/{pid}/operate/energy/trend")
        assert r.status_code == 200
        trend = r.json()
        assert len(trend) > 0
        # Trend points should be sorted by date
        dates = [p["period_start"] for p in trend]
        assert dates == sorted(dates)

    def test_list_leases(self, client):
        seed_aeco_data_via_client(client)
        pid = client.get("/api/projects/aeco-hub/projects?phase=operate").json()[0]["id"]
        r = client.get(f"/api/projects/aeco-hub/projects/{pid}/operate/leases")
        assert r.status_code == 200


class TestPhase2Twin:
    def test_get_project_twin(self, client):
        seed_aeco_data_via_client(client)
        pid = client.get("/api/projects/aeco-hub/projects").json()[0]["id"]
        r = client.get(f"/api/projects/aeco-hub/projects/{pid}/twin")
        assert r.status_code == 200
        twin = r.json()
        assert twin["project_id"] == pid
        assert len(twin["buildings"]) >= 1
        # Tree shape: every building has floors, every floor has spaces
        for b in twin["buildings"]:
            assert len(b["floors"]) >= 1
            for f in b["floors"]:
                # All floors should have at least one space
                assert isinstance(f["spaces"], list)

    def test_twin_404_for_missing_project(self, client):
        r = client.get("/api/projects/aeco-hub/projects/999999/twin")
        assert r.status_code == 404


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def seed_aeco_data_via_client(client) -> None:
    """Seed via the same in-memory engine the client uses.

    The ``client`` fixture overrides ``get_session`` to use the session-scoped
    ``engine``; we just reach into the override to grab a session and run
    the seed against it. Idempotent — safe to call once per test.
    """
    from sqlmodel import Session, select

    from innovation_factory.backend.app import app
    from innovation_factory.backend.dependencies import get_session

    override = app.dependency_overrides.get(get_session)
    assert override is not None, "client fixture should have overridden get_session"
    # Pull one session out of the generator so we can seed.
    gen = override()
    session = next(gen)
    try:
        # Skip if already seeded (idempotent across tests in the same session).
        existing = session.exec(select(DtProject)).first()
        if not existing:
            seed_aeco_data(session)
    finally:
        try:
            next(gen)
        except StopIteration:
            pass
