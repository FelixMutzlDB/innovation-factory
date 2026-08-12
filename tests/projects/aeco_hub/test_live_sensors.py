"""Unit tests for the ``/operate/live-sensors`` endpoint.

The live-sensor endpoint synthesises readings without hitting Unity Catalog,
making it fully testable without a Databricks connection.

Covers:
- Phase gate: design / build / demolish projects return an empty series list.
- Operate project returns exactly 3 series (zone_temp, co2, humidity).
- Each series has 61 points (60 minutes back + the current minute).
- Sensor code format: ``S-{project_id:03d}-LIVE-{idx:02d}``.
- 404 for unknown project_id.
"""
from __future__ import annotations

import pytest
from sqlmodel import Session

from innovation_factory.backend.projects.aeco_hub.models import (
    AecoProjectPhase,
    AecoProjectStatus,
    AecoBuildingType,
    AecoSensorType,
    DtProject,
    DtBuilding,
    DtFloor,
    DtLiveSensorsOut,
)


# ---------------------------------------------------------------------------
# Fixture helper: project seeded in a given phase
# ---------------------------------------------------------------------------


def _create_project(session: Session, phase: AecoProjectPhase, code: str = "TEST") -> DtProject:
    project = DtProject(
        code=code,
        name=f"Test {phase.value}",
        description="",
        phase=phase,
        status=AecoProjectStatus.active,
    )
    session.add(project)
    session.flush()
    return project


def _seed_building(session: Session, project_id: int) -> DtBuilding:
    bldg = DtBuilding(
        project_id=project_id,
        name="Block A",
        building_type=AecoBuildingType.office,
    )
    session.add(bldg)
    session.flush()
    return bldg


# ---------------------------------------------------------------------------
# Direct function tests (no HTTP layer)
# ---------------------------------------------------------------------------


class TestLiveSensorFunction:
    """Call the router function directly with a mocked SessionDep."""

    def _call_get_live_sensors(self, session: Session, project_id: int | None) -> DtLiveSensorsOut:
        """Import and call the route function directly, bypassing HTTP."""
        assert project_id is not None
        from innovation_factory.backend.projects.aeco_hub.routers.operate import get_live_sensors
        return get_live_sensors(project_id=project_id, db=session)

    def test_operate_project_returns_three_series(self, session):
        project = _create_project(session, AecoProjectPhase.operate, "LS-OP")
        out = self._call_get_live_sensors(session, project.id)
        assert out.project_id == project.id
        assert len(out.series) == 3

    def test_operate_series_have_61_points(self, session):
        project = _create_project(session, AecoProjectPhase.operate, "LS-OP2")
        out = self._call_get_live_sensors(session, project.id)
        for series in out.series:
            assert len(series.points) == 61, (
                f"Expected 61 points for {series.sensor_type}, got {len(series.points)}"
            )

    def test_operate_series_sensor_types(self, session):
        project = _create_project(session, AecoProjectPhase.operate, "LS-OP3")
        out = self._call_get_live_sensors(session, project.id)
        found_types = {s.sensor_type for s in out.series}
        assert AecoSensorType.zone_temp in found_types
        assert AecoSensorType.co2_concentration in found_types
        assert AecoSensorType.relative_humidity in found_types

    def test_operate_sensor_code_format(self, session):
        project = _create_project(session, AecoProjectPhase.operate, "LS-OP4")
        out = self._call_get_live_sensors(session, project.id)
        for idx, series in enumerate(out.series):
            expected_code = f"S-{project.id:03d}-LIVE-{idx + 1:02d}"
            assert series.sensor_code == expected_code, (
                f"Expected sensor code {expected_code!r}, got {series.sensor_code!r}"
            )

    def test_operate_points_sorted_ascending(self, session):
        project = _create_project(session, AecoProjectPhase.operate, "LS-OP5")
        out = self._call_get_live_sensors(session, project.id)
        for series in out.series:
            timestamps = [pt.ts for pt in series.points]
            assert timestamps == sorted(timestamps), (
                f"Points not sorted ascending for {series.sensor_type}"
            )

    def test_design_project_returns_empty_series(self, session):
        project = _create_project(session, AecoProjectPhase.design, "LS-DES")
        out = self._call_get_live_sensors(session, project.id)
        assert out.series == []
        assert out.project_id == project.id

    def test_build_project_returns_empty_series(self, session):
        project = _create_project(session, AecoProjectPhase.build, "LS-BLD")
        out = self._call_get_live_sensors(session, project.id)
        assert out.series == []

    def test_demolish_project_returns_empty_series(self, session):
        project = _create_project(session, AecoProjectPhase.demolish, "LS-DEM")
        out = self._call_get_live_sensors(session, project.id)
        assert out.series == []

    def test_404_for_missing_project(self, session):
        from fastapi import HTTPException
        with pytest.raises(HTTPException) as exc_info:
            self._call_get_live_sensors(session, 99999)
        assert exc_info.value.status_code == 404

    def test_operate_values_in_plausible_range(self, session):
        """Synthesised readings should sit within ±3 × amplitude of baseline."""
        project = _create_project(session, AecoProjectPhase.operate, "LS-RNG")
        out = self._call_get_live_sensors(session, project.id)
        temp_series = next(
            s for s in out.series if s.sensor_type == AecoSensorType.zone_temp
        )
        for pt in temp_series.points:
            # Baseline=21 ± amplitude=1.5, with secondary wave amplitude*0.4=0.6
            # Total swing ≤ 1.5 + 0.6 = 2.1, so range is ~[18.9, 23.1]
            assert 15.0 <= pt.value <= 30.0, (
                f"Unexpected zone_temp reading: {pt.value}"
            )


# ---------------------------------------------------------------------------
# Via HTTP client
# ---------------------------------------------------------------------------


def _seed_aeco_for_client(client) -> None:
    """Seed AECO data into the client's in-memory DB (idempotent)."""
    from sqlmodel import Session, select
    from innovation_factory.backend.app import app
    from innovation_factory.backend.dependencies import get_session
    from innovation_factory.backend.projects.aeco_hub.models import DtProject
    from innovation_factory.backend.projects.aeco_hub.seed import seed_aeco_data

    override = app.dependency_overrides.get(get_session)
    assert override is not None
    gen = override()
    db = next(gen)
    try:
        if not db.exec(select(DtProject)).first():
            seed_aeco_data(db)
    finally:
        try:
            next(gen)
        except StopIteration:
            pass


class TestLiveSensorsViaClient:
    def test_live_sensors_404_for_unknown_project(self, client):
        r = client.get("/api/projects/aeco-hub/projects/999999/operate/live-sensors")
        assert r.status_code == 404

    def test_live_sensors_operate_project_has_three_series(self, client):
        _seed_aeco_for_client(client)
        # Find an operate-phase project
        projects = client.get(
            "/api/projects/aeco-hub/projects?phase=operate"
        ).json()
        assert projects, "Expected at least one operate-phase project in seeded data"
        pid = projects[0]["id"]
        r = client.get(f"/api/projects/aeco-hub/projects/{pid}/operate/live-sensors")
        assert r.status_code == 200
        data = r.json()
        assert data["project_id"] == pid
        assert len(data["series"]) == 3

    def test_live_sensors_design_project_has_empty_series(self, client):
        _seed_aeco_for_client(client)
        projects = client.get(
            "/api/projects/aeco-hub/projects?phase=design"
        ).json()
        assert projects, "Expected at least one design-phase project"
        pid = projects[0]["id"]
        r = client.get(f"/api/projects/aeco-hub/projects/{pid}/operate/live-sensors")
        assert r.status_code == 200
        data = r.json()
        assert data["series"] == []
