"""Unit tests for the AECO Hub relationship-graph helper functions.

Tests the pure functions in ``routers/relationships.py`` directly —
no HTTP overhead.  Complements the HTTP-level tests in
``tests/projects/test_aeco_hub.py`` (``TestPhase5Relationships``).

Covers:
- ``_node_id`` composite format.
- ``_resolve_nodes`` type dispatch (all six node types + unknown type).
- Member node label format includes role in parentheses.
- ``get_relationship_graph`` with an empty graph (no edges → empty payload,
  not 404).
- Edge source/target strings match composite format.
"""
from __future__ import annotations

import pytest
from sqlmodel import Session

from innovation_factory.backend.projects.aeco_hub.models import (
    AecoBuildingType,
    AecoMemberRole,
    AecoProjectPhase,
    AecoProjectStatus,
    AecoRelationshipType,
    AecoSensorType,
    AecoSpaceType,
    DtBuilding,
    DtFloor,
    DtProject,
    DtProjectMember,
    DtRelationship,
    DtSensorDevice,
    DtSpace,
)
from innovation_factory.backend.projects.aeco_hub.routers.relationships import (
    _node_id,
    _resolve_nodes,
    get_relationship_graph,
)


# ---------------------------------------------------------------------------
# Pure helper: _node_id
# ---------------------------------------------------------------------------


class TestNodeId:
    def test_basic_composite_format(self):
        assert _node_id("project", 1) == "project:1"

    def test_building_type(self):
        assert _node_id("building", 42) == "building:42"

    def test_floor_type(self):
        assert _node_id("floor", 7) == "floor:7"

    def test_space_type(self):
        assert _node_id("space", 100) == "space:100"

    def test_sensor_type(self):
        assert _node_id("sensor", 33) == "sensor:33"

    def test_member_type(self):
        assert _node_id("member", 5) == "member:5"

    def test_id_zero(self):
        assert _node_id("project", 0) == "project:0"

    def test_large_id(self):
        assert _node_id("building", 999999) == "building:999999"

    def test_custom_type_string(self):
        result = _node_id("widget", 3)
        assert result == "widget:3"
        assert ":" in result


# ---------------------------------------------------------------------------
# _resolve_nodes dispatch
# ---------------------------------------------------------------------------


def _add_flush(session: Session, obj):
    session.add(obj)
    session.flush()
    return obj


class TestResolveNodes:
    def test_unknown_type_falls_back_to_label_placeholder(self, session):
        """Unknown node types are NOT silently dropped — they return a
        placeholder label ``"{type}#{id}"`` so the graph can still render."""
        node_keys: set[tuple[str, int]] = {("unknown_type", 1)}
        result = _resolve_nodes(session, "unknown_type", node_keys)
        assert len(result) == 1
        assert "unknown_type" in result[0].label
        assert "1" in result[0].label

    def test_no_matching_keys_returns_empty(self, session):
        project = _add_flush(session, DtProject(
            code="RN-EMPTY", name="Empty", description="",
            phase=AecoProjectPhase.design, status=AecoProjectStatus.active,
        ))
        node_keys: set[tuple[str, int]] = {("building", 99999)}  # wrong type
        result = _resolve_nodes(session, "project", node_keys)
        assert result == []

    def test_resolve_project_node(self, session):
        project = _add_flush(session, DtProject(
            code="RN-PROJ", name="Resolve Test Tower", description="",
            phase=AecoProjectPhase.operate, status=AecoProjectStatus.active,
        ))
        session.flush()
        assert project.id is not None

        node_keys: set[tuple[str, int]] = {("project", project.id)}
        nodes = _resolve_nodes(session, "project", node_keys)
        assert len(nodes) == 1
        assert nodes[0].ref_id == project.id
        assert nodes[0].label == "Resolve Test Tower"
        assert nodes[0].id == f"project:{project.id}"

    def test_resolve_building_node(self, session):
        project = _add_flush(session, DtProject(
            code="RN-BLDG", name="P", description="",
        ))
        bldg = _add_flush(session, DtBuilding(
            project_id=project.id,
            name="North Block",
            building_type=AecoBuildingType.office,
        ))
        session.flush()

        node_keys: set[tuple[str, int]] = {("building", bldg.id)}
        nodes = _resolve_nodes(session, "building", node_keys)
        assert len(nodes) == 1
        assert nodes[0].label == "North Block"

    def test_resolve_floor_node(self, session):
        project = _add_flush(session, DtProject(code="RN-FLR", name="P", description=""))
        bldg = _add_flush(session, DtBuilding(
            project_id=project.id, name="B", building_type=AecoBuildingType.office,
        ))
        floor = _add_flush(session, DtFloor(building_id=bldg.id, name="Level 2", level=2))
        session.flush()

        nodes = _resolve_nodes(session, "floor", {("floor", floor.id)})
        assert len(nodes) == 1
        assert nodes[0].label == "Level 2"

    def test_resolve_space_node(self, session):
        project = _add_flush(session, DtProject(code="RN-SPC", name="P", description=""))
        bldg = _add_flush(session, DtBuilding(
            project_id=project.id, name="B", building_type=AecoBuildingType.office,
        ))
        floor = _add_flush(session, DtFloor(building_id=bldg.id, name="G", level=0))
        space = _add_flush(session, DtSpace(
            floor_id=floor.id, name="Meeting Room 1",
            space_type=AecoSpaceType.meeting_room,
        ))
        session.flush()

        nodes = _resolve_nodes(session, "space", {("space", space.id)})
        assert len(nodes) == 1
        assert nodes[0].label == "Meeting Room 1"

    def test_resolve_sensor_node_uses_sensor_code(self, session):
        project = _add_flush(session, DtProject(code="RN-SNS", name="P", description=""))
        bldg = _add_flush(session, DtBuilding(
            project_id=project.id, name="B", building_type=AecoBuildingType.industrial,
        ))
        sensor = _add_flush(session, DtSensorDevice(
            building_id=bldg.id,
            sensor_code="S-007-0042",
            sensor_type=AecoSensorType.co2_concentration,
        ))
        session.flush()

        nodes = _resolve_nodes(session, "sensor", {("sensor", sensor.id)})
        assert len(nodes) == 1
        assert nodes[0].label == "S-007-0042"

    def test_resolve_member_node_label_includes_role(self, session):
        project = _add_flush(session, DtProject(code="RN-MBR", name="P", description=""))
        member = _add_flush(session, DtProjectMember(
            project_id=project.id,
            name="Petra Vogel",
            role=AecoMemberRole.architect,
        ))
        session.flush()

        nodes = _resolve_nodes(session, "member", {("member", member.id)})
        assert len(nodes) == 1
        assert "Petra Vogel" in nodes[0].label
        assert "architect" in nodes[0].label  # role in parentheses

    def test_fallback_label_for_missing_row(self, session):
        """When an ID is in node_keys but not in the DB, the fallback label
        must be ``"{type}#{id}"`` — not an empty string or a crash."""
        node_keys: set[tuple[str, int]] = {("project", 98765)}
        nodes = _resolve_nodes(session, "project", node_keys)
        assert len(nodes) == 1
        assert "98765" in nodes[0].label

    def test_multiple_nodes_resolved_at_once(self, session):
        p1 = _add_flush(session, DtProject(code="RN-M1", name="Alpha Tower", description=""))
        p2 = _add_flush(session, DtProject(code="RN-M2", name="Beta Tower", description=""))
        session.flush()

        node_keys: set[tuple[str, int]] = {("project", p1.id), ("project", p2.id)}
        nodes = _resolve_nodes(session, "project", node_keys)
        assert len(nodes) == 2
        labels = {n.label for n in nodes}
        assert "Alpha Tower" in labels
        assert "Beta Tower" in labels


# ---------------------------------------------------------------------------
# get_relationship_graph with empty / minimal data
# ---------------------------------------------------------------------------


class TestRelationshipGraphEndpoint:
    def _call(self, session, project_id, limit: int = 200, **kwargs):
        """Call the route function directly.

        FastAPI's ``Query()`` annotation is not resolved when calling outside
        the HTTP layer — ``limit`` defaults to the annotated default value
        (``DEFAULT_EDGE_LIMIT``) only inside a real HTTP request.  We must
        pass it explicitly here.
        """
        return get_relationship_graph(
            project_id=project_id, db=session, limit=limit, **kwargs
        )

    def test_empty_graph_not_404(self, session):
        """A project with no relationships must return an empty graph, not raise 404."""
        project = _add_flush(session, DtProject(
            code="EMPTY-GRAPH", name="No Edges", description="",
            phase=AecoProjectPhase.design, status=AecoProjectStatus.active,
        ))
        session.flush()

        result = self._call(session, project.id)
        assert result.project_id == project.id
        assert result.nodes == []
        assert result.edges == []
        assert result.total_edges == 0
        assert result.truncated is False

    def test_single_edge_not_truncated(self, session):
        project = _add_flush(session, DtProject(
            code="SINGLE-EDGE", name="One Edge", description="",
        ))
        bldg = _add_flush(session, DtBuilding(
            project_id=project.id, name="B", building_type=AecoBuildingType.office,
        ))
        session.add(DtRelationship(
            project_id=project.id,
            source_type="project", source_id=project.id,
            target_type="building", target_id=bldg.id,
            relationship_type=AecoRelationshipType.contains,
            label="contains",
        ))
        session.flush()

        result = self._call(session, project.id)
        assert len(result.edges) == 1
        assert result.total_edges == 1
        assert result.truncated is False

    def test_404_for_unknown_project(self, session):
        from fastapi import HTTPException
        with pytest.raises(HTTPException) as exc_info:
            self._call(session, 99999)
        assert exc_info.value.status_code == 404

    def test_edge_source_target_match_node_ids(self, session):
        project = _add_flush(session, DtProject(
            code="EDGE-FORMAT", name="E", description="",
        ))
        bldg = _add_flush(session, DtBuilding(
            project_id=project.id, name="B", building_type=AecoBuildingType.office,
        ))
        session.add(DtRelationship(
            project_id=project.id,
            source_type="project", source_id=project.id,
            target_type="building", target_id=bldg.id,
            relationship_type=AecoRelationshipType.contains,
            label="test",
        ))
        session.flush()

        result = self._call(session, project.id)
        node_ids = {n.id for n in result.nodes}
        for edge in result.edges:
            assert edge.source in node_ids, f"orphan source: {edge.source}"
            assert edge.target in node_ids, f"orphan target: {edge.target}"

    def test_truncated_flag_when_limit_is_one(self, session):
        project = _add_flush(session, DtProject(
            code="TRUNC-FLAG", name="Truncation Test", description="",
        ))
        bldg1 = _add_flush(session, DtBuilding(
            project_id=project.id, name="B1", building_type=AecoBuildingType.office,
        ))
        bldg2 = _add_flush(session, DtBuilding(
            project_id=project.id, name="B2", building_type=AecoBuildingType.residential,
        ))
        for bldg in (bldg1, bldg2):
            session.add(DtRelationship(
                project_id=project.id,
                source_type="project", source_id=project.id,
                target_type="building", target_id=bldg.id,
                relationship_type=AecoRelationshipType.contains,
                label="",
            ))
        session.flush()

        result = self._call(session, project.id, limit=1)
        assert result.total_edges == 2
        assert len(result.edges) == 1
        assert result.truncated is True

    def test_relationship_type_filter(self, session):
        project = _add_flush(session, DtProject(
            code="REL-FILTER", name="Filter Test", description="",
        ))
        bldg = _add_flush(session, DtBuilding(
            project_id=project.id, name="B", building_type=AecoBuildingType.office,
        ))
        member = _add_flush(session, DtProjectMember(
            project_id=project.id, name="Anna Becker",
            role=AecoMemberRole.project_manager,
        ))
        # Two edges of different types
        session.add(DtRelationship(
            project_id=project.id,
            source_type="project", source_id=project.id,
            target_type="building", target_id=bldg.id,
            relationship_type=AecoRelationshipType.contains,
            label="",
        ))
        session.add(DtRelationship(
            project_id=project.id,
            source_type="member", source_id=member.id,
            target_type="project", target_id=project.id,
            relationship_type=AecoRelationshipType.depends_on,
            label="",
        ))
        session.flush()

        result = self._call(
            session, project.id,
            relationship_type=AecoRelationshipType.contains,
        )
        for edge in result.edges:
            assert edge.relationship_type == AecoRelationshipType.contains
