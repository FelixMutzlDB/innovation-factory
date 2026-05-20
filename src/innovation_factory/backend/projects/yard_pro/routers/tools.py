"""Tool CRUD for yard-pro.

Same RLS pattern as plants.py — filters by the caller's yard, returns
404 on cross-household access. Telemetry rollups (UC4) attach in P1 via
B2's telemetry_service; the readiness snapshot lives in
``yp_tool_readiness`` but is exposed through the cockpit payload, not
here.
"""
from __future__ import annotations

from fastapi import APIRouter, HTTPException, Request
from sqlmodel import select

from ....dependencies import SessionDep
from ....input_sanitize import sanitize_text
from ..models import YpTool, YpToolCreate, YpToolOut
from .yards import get_caller_yard

router = APIRouter(tags=["yard-pro"])


def _safe(text: str) -> str:
    """Sanitize and coerce to ``str`` — see plants.py for the rationale."""
    cleaned = sanitize_text(text)
    return cleaned if isinstance(cleaned, str) else ""


def _to_out(t: YpTool) -> YpToolOut:
    return YpToolOut(
        id=t.id or 0,
        yard_id=t.yard_id,
        kind=t.kind,
        display_name=t.display_name,
        model_year=t.model_year,
        battery_family=t.battery_family,
        last_serviced_at=t.last_serviced_at,
    )


@router.get(
    "/tools",
    response_model=list[YpToolOut],
    operation_id="yp_listTools",
)
def list_tools(request: Request, db: SessionDep) -> list[YpToolOut]:
    yard = get_caller_yard(request, db)
    rows = db.exec(
        select(YpTool).where(YpTool.yard_id == yard.id).order_by(YpTool.id)  # type: ignore[invalid-argument-type]
    ).all()
    return [_to_out(t) for t in rows]


@router.post(
    "/tools",
    response_model=YpToolOut,
    operation_id="yp_createTool",
    status_code=201,
)
def create_tool(
    request: Request, payload: YpToolCreate, db: SessionDep
) -> YpToolOut:
    yard = get_caller_yard(request, db)
    tool = YpTool(
        yard_id=yard.id or 0,
        kind=payload.kind,
        display_name=_safe(payload.display_name),
        model_year=payload.model_year,
        battery_family=payload.battery_family,
        last_serviced_at=payload.last_serviced_at,
    )
    db.add(tool)
    db.commit()
    db.refresh(tool)
    return _to_out(tool)


@router.patch(
    "/tools/{tool_id}",
    response_model=YpToolOut,
    operation_id="yp_updateTool",
)
def update_tool(
    tool_id: int, request: Request, payload: YpToolCreate, db: SessionDep
) -> YpToolOut:
    yard = get_caller_yard(request, db)
    tool = db.get(YpTool, tool_id)
    if tool is None or tool.yard_id != yard.id:
        raise HTTPException(status_code=404, detail="Tool not found")
    tool.kind = payload.kind
    tool.display_name = _safe(payload.display_name)
    tool.model_year = payload.model_year
    tool.battery_family = payload.battery_family
    tool.last_serviced_at = payload.last_serviced_at
    db.add(tool)
    db.commit()
    db.refresh(tool)
    return _to_out(tool)


@router.delete(
    "/tools/{tool_id}",
    response_model=dict[str, bool],
    operation_id="yp_deleteTool",
)
def delete_tool(
    tool_id: int, request: Request, db: SessionDep
) -> dict[str, bool]:
    yard = get_caller_yard(request, db)
    tool = db.get(YpTool, tool_id)
    if tool is None or tool.yard_id != yard.id:
        raise HTTPException(status_code=404, detail="Tool not found")
    db.delete(tool)
    db.commit()
    return {"ok": True}
