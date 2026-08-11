"""Unit tests for energy aggregation logic in the operate router.

Tests the ``get_energy_trend`` function directly (no HTTP) with
hand-crafted data to verify:

- Multi-record same-day summation (two meters on the same day → sum kwh).
- Records spanning multiple days produce one point per day, sorted ascending.
- Empty energy table → empty list (not error).
- ``get_energy_trend`` raises 404 for missing project.
- ``list_energy_consumption`` pagination (offset / limit) is honoured.
"""
from __future__ import annotations

from datetime import datetime, timedelta, timezone

import pytest
from sqlmodel import Session

from innovation_factory.backend.projects.aeco_hub.models import (
    AecoBuildingType,
    AecoProjectPhase,
    AecoProjectStatus,
    DtBuilding,
    DtEnergyConsumption,
    DtProject,
)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _add(session: Session, obj):
    session.add(obj)
    session.flush()
    return obj


def _make_project(session: Session, code: str = "EN-TEST") -> DtProject:
    p = DtProject(
        code=code, name="Energy Test", description="",
        phase=AecoProjectPhase.operate, status=AecoProjectStatus.active,
    )
    return _add(session, p)


def _make_building(session: Session, project_id: int | None) -> DtBuilding:
    assert project_id is not None
    b = DtBuilding(
        project_id=project_id, name="B", building_type=AecoBuildingType.office,
    )
    return _add(session, b)


def _make_energy_record(
    session: Session,
    building_id: int | None,
    day_offset: int,
    kwh: float,
    meter_code: str = "M-001",
) -> DtEnergyConsumption:
    """Create an energy record ``day_offset`` days in the past."""
    assert building_id is not None
    period_start = datetime.now(timezone.utc).replace(
        hour=0, minute=0, second=0, microsecond=0
    ) - timedelta(days=day_offset)
    period_end = period_start + timedelta(days=1)
    rec = DtEnergyConsumption(
        building_id=building_id,
        meter_code=meter_code,
        period_start=period_start,
        period_end=period_end,
        kwh=kwh,
        cost_eur=round(kwh * 0.25, 2),
    )
    session.add(rec)
    session.flush()
    return rec


# ---------------------------------------------------------------------------
# Tests
# ---------------------------------------------------------------------------


class TestGetEnergyTrend:
    def _call(self, session, project_id):
        from innovation_factory.backend.projects.aeco_hub.routers.operate import get_energy_trend
        return get_energy_trend(project_id=project_id, db=session)

    def test_empty_returns_empty_list(self, session):
        project = _make_project(session, "EN-EMPTY")
        _make_building(session, project.id)
        result = self._call(session, project.id)
        assert result == []

    def test_single_record_produces_one_point(self, session):
        project = _make_project(session, "EN-ONE")
        bldg = _make_building(session, project.id)
        _make_energy_record(session, bldg.id, day_offset=1, kwh=1000.0)
        result = self._call(session, project.id)
        assert len(result) == 1
        assert result[0].kwh == pytest.approx(1000.0, abs=1.0)

    def test_two_records_same_day_are_summed(self, session):
        """Two meters recording on the same day must be aggregated into one point."""
        project = _make_project(session, "EN-SUM")
        bldg = _make_building(session, project.id)
        _make_energy_record(session, bldg.id, day_offset=1, kwh=1000.0, meter_code="M-A")
        _make_energy_record(session, bldg.id, day_offset=1, kwh=500.0, meter_code="M-B")
        result = self._call(session, project.id)
        assert len(result) == 1
        assert result[0].kwh == pytest.approx(1500.0, abs=1.0)

    def test_records_on_different_days_produce_separate_points(self, session):
        project = _make_project(session, "EN-DAYS")
        bldg = _make_building(session, project.id)
        for day in (3, 2, 1):  # inserted out-of-order
            _make_energy_record(session, bldg.id, day_offset=day, kwh=float(day * 100))
        result = self._call(session, project.id)
        assert len(result) == 3

    def test_trend_sorted_ascending_by_date(self, session):
        """Energy trend must be sorted oldest-first (ascending)."""
        project = _make_project(session, "EN-SORT")
        bldg = _make_building(session, project.id)
        for day in [5, 1, 3, 2, 4]:
            _make_energy_record(session, bldg.id, day_offset=day, kwh=100.0)
        result = self._call(session, project.id)
        dates = [pt.period_start for pt in result]
        assert dates == sorted(dates), "Energy trend is not sorted ascending"

    def test_cost_is_aggregated_alongside_kwh(self, session):
        project = _make_project(session, "EN-COST")
        bldg = _make_building(session, project.id)
        # Two meters: 1000 kwh × 0.25 + 500 kwh × 0.25 = 250 + 125 = 375 cost
        _make_energy_record(session, bldg.id, day_offset=1, kwh=1000.0, meter_code="M-X")
        _make_energy_record(session, bldg.id, day_offset=1, kwh=500.0, meter_code="M-Y")
        result = self._call(session, project.id)
        assert result[0].cost_eur == pytest.approx(375.0, abs=1.0)

    def test_404_for_missing_project(self, session):
        from fastapi import HTTPException
        with pytest.raises(HTTPException) as exc_info:
            self._call(session, 99999)
        assert exc_info.value.status_code == 404

    def test_multiple_buildings_same_day_summed(self, session):
        """Energy from two buildings for the same project must be summed per day."""
        project = _make_project(session, "EN-2BLDG")
        bldg1 = _make_building(session, project.id)
        bldg2 = _make_building(session, project.id)
        # Give bldg2 a different project FK via a second building on the same project
        _make_energy_record(session, bldg1.id, day_offset=2, kwh=800.0)
        _make_energy_record(session, bldg2.id, day_offset=2, kwh=600.0)
        result = self._call(session, project.id)
        assert len(result) == 1
        assert result[0].kwh == pytest.approx(1400.0, abs=1.0)


class TestListEnergyConsumption:
    def _call(self, session, project_id, building_id=None, limit=100, offset=0):
        from innovation_factory.backend.projects.aeco_hub.routers.operate import list_energy_consumption
        return list_energy_consumption(
            project_id=project_id, db=session,
            building_id=building_id, limit=limit, offset=offset,
        )

    def test_returns_empty_list_for_project_with_no_records(self, session):
        project = _make_project(session, "LC-EMPTY")
        _make_building(session, project.id)
        result = self._call(session, project.id)
        assert result == []

    def test_limit_is_honoured(self, session):
        project = _make_project(session, "LC-LIM")
        bldg = _make_building(session, project.id)
        for day in range(10):
            _make_energy_record(session, bldg.id, day_offset=day + 1, kwh=100.0)
        result = self._call(session, project.id, limit=3)
        assert len(result) == 3

    def test_offset_paginates(self, session):
        project = _make_project(session, "LC-PAGE")
        bldg = _make_building(session, project.id)
        for day in range(5):
            _make_energy_record(session, bldg.id, day_offset=day + 1, kwh=float((day + 1) * 100))
        all_records = self._call(session, project.id, limit=5)
        page2 = self._call(session, project.id, limit=3, offset=2)
        # Page 2 should be the same as all_records[2:]
        assert [r.id for r in page2] == [r.id for r in all_records[2:5]]

    def test_building_id_filter(self, session):
        project = _make_project(session, "LC-BLDG")
        bldg1 = _make_building(session, project.id)
        bldg2 = _make_building(session, project.id)
        _make_energy_record(session, bldg1.id, day_offset=1, kwh=100.0)
        _make_energy_record(session, bldg2.id, day_offset=1, kwh=200.0)
        result = self._call(session, project.id, building_id=bldg1.id)
        assert all(r.building_id == bldg1.id for r in result)
        assert len(result) == 1

    def test_404_for_missing_project(self, session):
        from fastapi import HTTPException
        with pytest.raises(HTTPException) as exc_info:
            self._call(session, 99999)
        assert exc_info.value.status_code == 404
