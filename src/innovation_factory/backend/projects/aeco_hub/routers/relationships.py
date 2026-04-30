"""Relationships graph endpoint for the Phase 5 force-directed view.

Bounded by ``MAX_EDGES`` to avoid streaming an unbounded edge list to the
frontend — the regression test ``test_relationships_pagination_caps_at_max``
enforces this. When the unbounded count exceeds the cap, the response
flags ``truncated: True`` so the UI can render a "showing N of M" hint.
"""
from typing import Optional

from fastapi import APIRouter, HTTPException, Query
from sqlmodel import func, select

from ....dependencies import SessionDep
from ..models import (
    AecoRelationshipType,
    DtBuilding,
    DtFloor,
    DtProject,
    DtProjectMember,
    DtRelationship,
    DtRelationshipEdgeOut,
    DtRelationshipGraphOut,
    DtRelationshipNodeOut,
    DtSensorDevice,
    DtSpace,
)

router = APIRouter(tags=["aeco-hub"])

MAX_EDGES = 1000
DEFAULT_EDGE_LIMIT = 200


def _node_id(node_type: str, ref_id: int) -> str:
    return f"{node_type}:{ref_id}"


@router.get(
    "/projects/{project_id}/relationships",
    response_model=DtRelationshipGraphOut,
    operation_id="aeco_getRelationshipGraph",
)
def get_relationship_graph(
    project_id: int,
    db: SessionDep,
    limit: int = Query(default=DEFAULT_EDGE_LIMIT, ge=1, le=MAX_EDGES),
    relationship_type: Optional[AecoRelationshipType] = None,
) -> DtRelationshipGraphOut:
    """Return the relationship graph (nodes + edges) for a project.

    Hard-capped at ``MAX_EDGES`` to keep the force-directed renderer
    responsive and to prevent any single query from accidentally
    streaming the whole table.
    """
    project = db.get(DtProject, project_id)
    if not project:
        raise HTTPException(404, detail="Project not found")

    base = select(DtRelationship).where(DtRelationship.project_id == project_id)
    if relationship_type:
        base = base.where(DtRelationship.relationship_type == relationship_type)

    total = db.exec(
        select(func.count(DtRelationship.id))
        .where(DtRelationship.project_id == project_id)
        .where(
            DtRelationship.relationship_type == relationship_type
            if relationship_type else True
        )
    ).one()
    edges = list(db.exec(base.order_by(DtRelationship.id).limit(limit)).all())  # type: ignore[invalid-argument-type]

    # Build node set from the actually-returned edges so we never return a
    # node that's not connected to anything in this response.
    node_keys: set[tuple[str, int]] = set()
    for e in edges:
        node_keys.add((e.source_type, e.source_id))
        node_keys.add((e.target_type, e.target_id))

    # Resolve node labels by type. Each lookup is bounded by the edge cap.
    nodes: list[DtRelationshipNodeOut] = []
    nodes.extend(_resolve_nodes(db, "project", node_keys))
    nodes.extend(_resolve_nodes(db, "building", node_keys))
    nodes.extend(_resolve_nodes(db, "floor", node_keys))
    nodes.extend(_resolve_nodes(db, "space", node_keys))
    nodes.extend(_resolve_nodes(db, "sensor", node_keys))
    nodes.extend(_resolve_nodes(db, "member", node_keys))

    return DtRelationshipGraphOut(
        project_id=project_id,
        nodes=nodes,
        edges=[
            DtRelationshipEdgeOut(
                id=e.id or 0,
                source=_node_id(e.source_type, e.source_id),
                target=_node_id(e.target_type, e.target_id),
                relationship_type=e.relationship_type,
                label=e.label,
            )
            for e in edges
        ],
        total_edges=total,
        truncated=total > len(edges),
    )


def _resolve_nodes(
    db: SessionDep,
    node_type: str,
    node_keys: set[tuple[str, int]],
) -> list[DtRelationshipNodeOut]:
    ids = [ref_id for (t, ref_id) in node_keys if t == node_type]
    if not ids:
        return []

    label_lookup: dict[int, str]
    if node_type == "project":
        rows = list(db.exec(select(DtProject).where(DtProject.id.in_(ids))).all())  # type: ignore[unresolved-attribute]
        label_lookup = {r.id or 0: r.name for r in rows}
    elif node_type == "building":
        rows = list(db.exec(select(DtBuilding).where(DtBuilding.id.in_(ids))).all())  # type: ignore[unresolved-attribute]
        label_lookup = {r.id or 0: r.name for r in rows}
    elif node_type == "floor":
        rows = list(db.exec(select(DtFloor).where(DtFloor.id.in_(ids))).all())  # type: ignore[unresolved-attribute]
        label_lookup = {r.id or 0: r.name for r in rows}
    elif node_type == "space":
        rows = list(db.exec(select(DtSpace).where(DtSpace.id.in_(ids))).all())  # type: ignore[unresolved-attribute]
        label_lookup = {r.id or 0: r.name for r in rows}
    elif node_type == "sensor":
        rows = list(db.exec(select(DtSensorDevice).where(DtSensorDevice.id.in_(ids))).all())  # type: ignore[unresolved-attribute]
        label_lookup = {r.id or 0: r.sensor_code for r in rows}
    elif node_type == "member":
        rows = list(db.exec(select(DtProjectMember).where(DtProjectMember.id.in_(ids))).all())  # type: ignore[unresolved-attribute]
        label_lookup = {r.id or 0: f"{r.name} ({r.role.value})" for r in rows}
    else:
        label_lookup = {}

    return [
        DtRelationshipNodeOut(
            id=_node_id(node_type, ref_id),
            type=node_type,
            ref_id=ref_id,
            label=label_lookup.get(ref_id, f"{node_type}#{ref_id}"),
        )
        for ref_id in ids
    ]
