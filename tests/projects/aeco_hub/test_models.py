"""Unit tests for AECO Hub Pydantic output models and enum naming conventions.

Complements ``tests/projects/test_aeco_hub.py``, which covers SQLModel
table models and CRUD routers.  These tests focus on:

- All public enums in ``models.py`` carry the ``Aeco`` prefix (OpenAPI
  collision guard — plan §13).
- Pydantic output-model shapes (field presence, serialisation round-trips).
- Aggregate model invariants (variance, truncated flag, nested twin tree).
"""
from __future__ import annotations

import inspect
from datetime import date, datetime, timezone
from enum import Enum

import pytest

import innovation_factory.backend.projects.aeco_hub.models as aeco_models
from innovation_factory.backend.projects.aeco_hub.models import (
    AecoBuildingType,
    AecoChatRole,
    AecoCostStatus,
    AecoIssueSeverity,
    AecoIssueStatus,
    AecoIssueCategory,
    AecoLeaseStatus,
    AecoLifecycleSegment,
    AecoMaintenancePriority,
    AecoMaintenanceStatus,
    AecoProjectPhase,
    AecoProjectStatus,
    AecoRelationshipType,
    AecoSensorType,
    AecoSpaceType,
    DtChatHistoryOut,
    DtChatMessageOut,
    DtChatSessionOut,
    DtCostSummaryOut,
    DtEnergyDailyPointOut,
    DtIssueStatsOut,
    DtLiveReadingPointOut,
    DtLiveSensorSeriesOut,
    DtLiveSensorsOut,
    DtPortfolioStatsOut,
    DtProjectKpiOut,
    DtRelationshipEdgeOut,
    DtRelationshipGraphOut,
    DtRelationshipNodeOut,
    DtScheduleSummaryOut,
    DtTwinBuildingOut,
    DtTwinFloorOut,
    DtTwinOut,
    DtTwinSpaceOut,
)


# ---------------------------------------------------------------------------
# Enum naming conventions
# ---------------------------------------------------------------------------


class TestEnumNamingConventions:
    """All public enums in models.py must carry the ``Aeco`` prefix so the
    OpenAPI schema does not collide with sibling accelerators (e.g.
    ``IssueStatus`` → ``AecoIssueStatus`` vs ``MacIssueStatus``)."""

    def _public_enums(self):
        return [
            (name, obj)
            for name, obj in inspect.getmembers(aeco_models)
            if (
                inspect.isclass(obj)
                and issubclass(obj, Enum)
                and obj is not Enum  # skip the imported Enum base itself
                and not name.startswith("_")
                and obj.__module__ == aeco_models.__name__  # defined in this module
            )
        ]

    def test_all_public_enums_have_aeco_prefix(self):
        enums = self._public_enums()
        assert enums, "Expected at least one public enum in aeco_models"
        bad = [name for name, _ in enums if not name.startswith("Aeco")]
        assert not bad, f"Enums missing 'Aeco' prefix: {bad}"

    def test_known_enums_present(self):
        expected = {
            "AecoProjectPhase",
            "AecoProjectStatus",
            "AecoBuildingType",
            "AecoSpaceType",
            "AecoAssetCategory",
            "AecoMemberRole",
            "AecoIssueSeverity",
            "AecoIssueStatus",
            "AecoIssueCategory",
            "AecoDocumentType",
            "AecoBimDiscipline",
            "AecoBimLod",
            "AecoSensorType",
            "AecoMaintenancePriority",
            "AecoMaintenanceStatus",
            "AecoCostStatus",
            "AecoChangeOrderStatus",
            "AecoScheduleStatus",
            "AecoSiteReportType",
            "AecoLeaseStatus",
            "AecoIntegrationStatus",
            "AecoRelationshipType",
            "AecoLifecycleSegment",
            "AecoChatRole",
        }
        for name in expected:
            assert hasattr(aeco_models, name), f"Enum {name!r} missing from aeco_models"

    def test_no_bare_issue_status_without_prefix(self):
        """Regression: bare ``IssueStatus`` would silently collide."""
        assert not hasattr(aeco_models, "IssueStatus")
        assert not hasattr(aeco_models, "IssueSeverity")
        assert not hasattr(aeco_models, "RelationshipType")

    def test_relationship_type_values_complete(self):
        expected_values = {
            "contains", "feeds_data_to", "depends_on", "maintained_by",
            "designed_by", "supplied_by", "monitors", "controls",
        }
        actual_values = {e.value for e in AecoRelationshipType}
        assert expected_values == actual_values

    def test_lifecycle_segment_values(self):
        expected = {"design", "qa_qc", "requirements", "build", "operate", "visualize"}
        assert {e.value for e in AecoLifecycleSegment} == expected

    def test_chat_role_values(self):
        assert {e.value for e in AecoChatRole} == {"user", "assistant", "system"}


# ---------------------------------------------------------------------------
# DtRelationshipNodeOut / DtRelationshipEdgeOut / DtRelationshipGraphOut
# ---------------------------------------------------------------------------


class TestRelationshipModels:
    """Graph-view output models for the Phase 5 force-directed view."""

    def test_node_out_id_is_composite(self):
        node = DtRelationshipNodeOut(
            id="project:42",
            type="project",
            ref_id=42,
            label="My Project",
        )
        assert node.id == "project:42"
        assert ":" in node.id

    def test_node_out_accepts_any_type_string(self):
        for node_type in ("project", "building", "floor", "space", "sensor", "member"):
            node = DtRelationshipNodeOut(
                id=f"{node_type}:1",
                type=node_type,
                ref_id=1,
                label=f"Label for {node_type}",
            )
            assert node.type == node_type

    def test_edge_out_source_target_composite_format(self):
        edge = DtRelationshipEdgeOut(
            id=1,
            source="project:1",
            target="building:3",
            relationship_type=AecoRelationshipType.contains,
            label="contains",
        )
        assert edge.source == "project:1"
        assert edge.target == "building:3"
        assert ":" in edge.source
        assert ":" in edge.target

    def test_graph_out_truncated_false_when_all_edges_returned(self):
        edges = [
            DtRelationshipEdgeOut(
                id=i,
                source=f"project:{i}",
                target=f"building:{i}",
                relationship_type=AecoRelationshipType.contains,
                label="",
            )
            for i in range(3)
        ]
        nodes = [
            DtRelationshipNodeOut(id=f"project:{i}", type="project", ref_id=i, label="")
            for i in range(3)
        ]
        graph = DtRelationshipGraphOut(
            project_id=1,
            nodes=nodes,
            edges=edges,
            total_edges=3,
            truncated=False,
        )
        assert graph.truncated is False
        assert graph.total_edges == len(graph.edges)

    def test_graph_out_truncated_true_when_total_exceeds_returned(self):
        edges = [
            DtRelationshipEdgeOut(
                id=1,
                source="project:1",
                target="building:1",
                relationship_type=AecoRelationshipType.contains,
                label="",
            )
        ]
        graph = DtRelationshipGraphOut(
            project_id=1,
            nodes=[],
            edges=edges,
            total_edges=500,
            truncated=True,
        )
        assert graph.truncated is True
        assert graph.total_edges > len(graph.edges)

    def test_graph_out_empty_graph(self):
        graph = DtRelationshipGraphOut(
            project_id=7,
            nodes=[],
            edges=[],
            total_edges=0,
            truncated=False,
        )
        assert graph.nodes == []
        assert graph.edges == []
        assert graph.total_edges == 0
        assert graph.truncated is False


# ---------------------------------------------------------------------------
# DtTwinOut (spatial hierarchy)
# ---------------------------------------------------------------------------


class TestTwinModels:
    def test_twin_out_nested_structure(self):
        space = DtTwinSpaceOut(
            id=10,
            name="G.01",
            space_type=AecoSpaceType.office,
            area_sqm=25.0,
            capacity=4,
            room_number="A-001",
        )
        floor = DtTwinFloorOut(id=5, name="Ground", level=0, area_sqm=500.0, spaces=[space])
        building = DtTwinBuildingOut(
            id=2,
            name="Block A",
            building_type=AecoBuildingType.office,
            floor_count=1,
            gross_floor_area_sqm=500.0,
            floors=[floor],
        )
        twin = DtTwinOut(
            project_id=1,
            project_name="Test Tower",
            project_phase=AecoProjectPhase.operate,
            buildings=[building],
        )
        assert len(twin.buildings) == 1
        assert len(twin.buildings[0].floors) == 1
        assert len(twin.buildings[0].floors[0].spaces) == 1
        assert twin.buildings[0].floors[0].spaces[0].room_number == "A-001"

    def test_twin_out_empty_buildings(self):
        twin = DtTwinOut(
            project_id=99,
            project_name="Ghost",
            project_phase=AecoProjectPhase.design,
            buildings=[],
        )
        assert twin.buildings == []

    def test_twin_floor_out_empty_spaces(self):
        floor = DtTwinFloorOut(id=1, name="L1", level=1, area_sqm=100.0, spaces=[])
        assert floor.spaces == []

    def test_twin_round_trip_json(self):
        space = DtTwinSpaceOut(
            id=1, name="S1", space_type=AecoSpaceType.corridor, area_sqm=10.0, capacity=0, room_number=""
        )
        floor = DtTwinFloorOut(id=1, name="G", level=0, area_sqm=100.0, spaces=[space])
        building = DtTwinBuildingOut(
            id=1, name="B", building_type=AecoBuildingType.residential,
            floor_count=1, gross_floor_area_sqm=100.0, floors=[floor],
        )
        twin = DtTwinOut(
            project_id=1, project_name="T",
            project_phase=AecoProjectPhase.build, buildings=[building],
        )
        serialised = twin.model_dump()
        assert serialised["buildings"][0]["floors"][0]["spaces"][0]["space_type"] == "corridor"


# ---------------------------------------------------------------------------
# Aggregate output models
# ---------------------------------------------------------------------------


class TestAggregateModels:
    def test_portfolio_stats_fields(self):
        stats = DtPortfolioStatsOut(
            total_projects=5,
            active_projects=4,
            operating_projects=2,
            constructing_projects=1,
            design_projects=1,
            total_budget_eur=100_000.0,
            total_actual_cost_eur=80_000.0,
            total_buildings=8,
        )
        assert stats.total_projects == 5
        assert stats.total_buildings == 8

    def test_project_kpi_out_fields(self):
        kpi = DtProjectKpiOut(
            project_id=1,
            building_count=2,
            floor_count=10,
            space_count=120,
            member_count=7,
            open_issues=3,
            documents_count=10,
            progress_pct=65.0,
            budget_eur=1_000_000.0,
            actual_cost_eur=650_000.0,
            cost_variance_pct=-35.0,
        )
        assert kpi.cost_variance_pct == -35.0
        assert kpi.member_count == 7

    def test_issue_stats_by_category_sums_to_total(self):
        by_cat = {"clash": 2, "rfi": 1, "defect": 3, "safety": 1}
        stats = DtIssueStatsOut(
            project_id=1,
            total=7,
            open=4,
            in_progress=2,
            resolved=1,
            critical=1,
            by_category=by_cat,
        )
        assert sum(stats.by_category.values()) == stats.total

    def test_issue_stats_empty_categories(self):
        stats = DtIssueStatsOut(
            project_id=1, total=0, open=0,
            in_progress=0, resolved=0, critical=0, by_category={},
        )
        assert stats.by_category == {}
        assert stats.total == 0

    def test_cost_summary_variance_math(self):
        """DtCostSummaryOut: variance_eur = actual - estimated."""
        summary = DtCostSummaryOut(
            project_id=1,
            total_estimated_eur=100_000.0,
            total_actual_eur=115_000.0,
            variance_eur=15_000.0,
            variance_pct=15.0,
            item_count=30,
            by_category={"Structure": 40_000.0, "MEP": 60_000.0},
        )
        assert abs(summary.variance_eur - (summary.total_actual_eur - summary.total_estimated_eur)) < 0.01

    def test_cost_summary_negative_variance(self):
        """Under-budget: variance is negative."""
        summary = DtCostSummaryOut(
            project_id=1,
            total_estimated_eur=100_000.0,
            total_actual_eur=90_000.0,
            variance_eur=-10_000.0,
            variance_pct=-10.0,
            item_count=10,
            by_category={},
        )
        assert summary.variance_eur < 0

    def test_schedule_summary_totals_consistent(self):
        summary = DtScheduleSummaryOut(
            project_id=1,
            total=25,
            not_started=5,
            in_progress=10,
            completed=8,
            delayed=2,
            avg_progress_pct=48.0,
        )
        assert summary.total == (
            summary.not_started + summary.in_progress
            + summary.completed + summary.delayed
        )


# ---------------------------------------------------------------------------
# Live sensor output models
# ---------------------------------------------------------------------------


class TestLiveSensorModels:
    _now = datetime.now(timezone.utc)

    def test_live_reading_point(self):
        pt = DtLiveReadingPointOut(ts=self._now, value=21.3)
        assert pt.value == pytest.approx(21.3)

    def test_live_sensor_series_out(self):
        pts = [DtLiveReadingPointOut(ts=self._now, value=float(v)) for v in range(5)]
        series = DtLiveSensorSeriesOut(
            sensor_code="S-001-LIVE-01",
            sensor_type=AecoSensorType.zone_temp,
            unit="C",
            points=pts,
        )
        assert len(series.points) == 5
        assert series.sensor_type == AecoSensorType.zone_temp

    def test_live_sensors_out_empty_series(self):
        out = DtLiveSensorsOut(
            project_id=3,
            generated_at=self._now,
            series=[],
        )
        assert out.series == []
        assert out.project_id == 3

    def test_live_sensors_out_with_series(self):
        pts = [DtLiveReadingPointOut(ts=self._now, value=700.0)]
        series = [DtLiveSensorSeriesOut(
            sensor_code="S-003-LIVE-01",
            sensor_type=AecoSensorType.co2_concentration,
            unit="ppm",
            points=pts,
        )]
        out = DtLiveSensorsOut(project_id=3, generated_at=self._now, series=series)
        assert len(out.series) == 1
        assert out.series[0].unit == "ppm"


# ---------------------------------------------------------------------------
# Chat output models
# ---------------------------------------------------------------------------


class TestChatModels:
    _now = datetime.now(timezone.utc)

    def test_chat_session_out(self):
        s = DtChatSessionOut(id=1, project_id=42, agent_kind="mas", created_at=self._now)
        assert s.agent_kind == "mas"
        assert s.project_id == 42

    def test_chat_session_out_optional_project_id(self):
        s = DtChatSessionOut(id=2, project_id=None, agent_kind="ka", created_at=self._now)
        assert s.project_id is None

    def test_chat_message_out(self):
        msg = DtChatMessageOut(
            id=10,
            session_id=1,
            role=AecoChatRole.assistant,
            content="Hello!",
            sources_json={"sources": [{"type": "mas"}]},
            created_at=self._now,
        )
        assert msg.role == AecoChatRole.assistant
        assert msg.sources_json is not None

    def test_chat_message_out_no_sources(self):
        msg = DtChatMessageOut(
            id=11, session_id=1, role=AecoChatRole.user,
            content="Question", sources_json=None, created_at=self._now,
        )
        assert msg.sources_json is None

    def test_chat_history_out(self):
        session_out = DtChatSessionOut(
            id=1, project_id=5, agent_kind="mas", created_at=self._now
        )
        msgs = [
            DtChatMessageOut(
                id=1, session_id=1, role=AecoChatRole.user,
                content="Q", sources_json=None, created_at=self._now,
            ),
            DtChatMessageOut(
                id=2, session_id=1, role=AecoChatRole.assistant,
                content="A", sources_json=None, created_at=self._now,
            ),
        ]
        history = DtChatHistoryOut(session=session_out, messages=msgs)
        assert len(history.messages) == 2
        assert history.session.id == 1

    def test_chat_history_out_empty_messages(self):
        session_out = DtChatSessionOut(
            id=3, project_id=None, agent_kind="ka", created_at=self._now
        )
        history = DtChatHistoryOut(session=session_out, messages=[])
        assert history.messages == []


# ---------------------------------------------------------------------------
# Energy / IoT point models
# ---------------------------------------------------------------------------


class TestEnergyModels:
    _now = datetime.now(timezone.utc)

    def test_energy_daily_point_out(self):
        pt = DtEnergyDailyPointOut(
            period_start=self._now,
            kwh=1234.5,
            cost_eur=247.0,
        )
        assert pt.kwh == pytest.approx(1234.5)
        assert pt.cost_eur == pytest.approx(247.0)

    def test_energy_daily_point_zero_cost(self):
        pt = DtEnergyDailyPointOut(period_start=self._now, kwh=0.0, cost_eur=0.0)
        assert pt.kwh == 0.0
        assert pt.cost_eur == 0.0
