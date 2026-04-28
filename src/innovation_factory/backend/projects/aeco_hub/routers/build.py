"""Build-phase endpoints: schedule, cost, site reports, change orders."""
from collections import defaultdict
from typing import Optional

from fastapi import APIRouter, HTTPException, Query
from sqlmodel import func, select

from ....dependencies import SessionDep
from ..models import (
    AecoChangeOrderStatus,
    AecoCostStatus,
    AecoScheduleStatus,
    AecoSiteReportType,
    DtChangeOrder,
    DtChangeOrderOut,
    DtCostItem,
    DtCostItemOut,
    DtCostSummaryOut,
    DtProject,
    DtScheduleActivity,
    DtScheduleActivityOut,
    DtScheduleSummaryOut,
    DtSiteReport,
    DtSiteReportOut,
)

router = APIRouter(tags=["aeco-hub"])


# -- Schedule ---------------------------------------------------------


@router.get(
    "/projects/{project_id}/build/schedule",
    response_model=list[DtScheduleActivityOut],
    operation_id="aeco_listScheduleActivities",
)
def list_schedule_activities(
    project_id: int,
    db: SessionDep,
    status: Optional[AecoScheduleStatus] = None,
    limit: int = Query(default=100, ge=1, le=500),
    offset: int = Query(default=0, ge=0),
):
    if not db.get(DtProject, project_id):
        raise HTTPException(404, detail="Project not found")
    stmt = select(DtScheduleActivity).where(DtScheduleActivity.project_id == project_id)
    if status:
        stmt = stmt.where(DtScheduleActivity.status == status)
    stmt = stmt.order_by(DtScheduleActivity.start_date).offset(offset).limit(limit)  # type: ignore[invalid-argument-type]
    return db.exec(stmt).all()


@router.get(
    "/projects/{project_id}/build/schedule/summary",
    response_model=DtScheduleSummaryOut,
    operation_id="aeco_getScheduleSummary",
)
def get_schedule_summary(project_id: int, db: SessionDep) -> DtScheduleSummaryOut:
    if not db.get(DtProject, project_id):
        raise HTTPException(404, detail="Project not found")
    base = select(func.count(DtScheduleActivity.id)).where(DtScheduleActivity.project_id == project_id)
    total = db.exec(base).one()
    not_started = db.exec(base.where(DtScheduleActivity.status == AecoScheduleStatus.not_started)).one()
    in_progress = db.exec(base.where(DtScheduleActivity.status == AecoScheduleStatus.in_progress)).one()
    completed = db.exec(base.where(DtScheduleActivity.status == AecoScheduleStatus.completed)).one()
    delayed = db.exec(base.where(DtScheduleActivity.status == AecoScheduleStatus.delayed)).one()
    avg = db.exec(
        select(func.coalesce(func.avg(DtScheduleActivity.progress_pct), 0)).where(
            DtScheduleActivity.project_id == project_id
        )
    ).one()
    return DtScheduleSummaryOut(
        project_id=project_id,
        total=total,
        not_started=not_started,
        in_progress=in_progress,
        completed=completed,
        delayed=delayed,
        avg_progress_pct=round(float(avg), 1),
    )


# -- Cost -------------------------------------------------------------


@router.get(
    "/projects/{project_id}/build/costs",
    response_model=list[DtCostItemOut],
    operation_id="aeco_listCostItems",
)
def list_cost_items(
    project_id: int,
    db: SessionDep,
    status: Optional[AecoCostStatus] = None,
    category: Optional[str] = None,
    limit: int = Query(default=100, ge=1, le=500),
    offset: int = Query(default=0, ge=0),
):
    if not db.get(DtProject, project_id):
        raise HTTPException(404, detail="Project not found")
    stmt = select(DtCostItem).where(DtCostItem.project_id == project_id)
    if status:
        stmt = stmt.where(DtCostItem.status == status)
    if category:
        stmt = stmt.where(DtCostItem.category == category)
    stmt = stmt.order_by(DtCostItem.code).offset(offset).limit(limit)
    return db.exec(stmt).all()


@router.get(
    "/projects/{project_id}/build/costs/summary",
    response_model=DtCostSummaryOut,
    operation_id="aeco_getCostSummary",
)
def get_cost_summary(project_id: int, db: SessionDep) -> DtCostSummaryOut:
    if not db.get(DtProject, project_id):
        raise HTTPException(404, detail="Project not found")
    items = list(
        db.exec(select(DtCostItem).where(DtCostItem.project_id == project_id)).all()
    )
    total_estimated = sum(i.estimated_eur for i in items)
    total_actual = sum(i.actual_eur for i in items)
    variance = total_actual - total_estimated
    variance_pct = round((variance / total_estimated) * 100.0, 2) if total_estimated > 0 else 0.0
    by_category: dict[str, float] = defaultdict(float)
    for i in items:
        by_category[i.category or "Other"] += i.estimated_eur
    return DtCostSummaryOut(
        project_id=project_id,
        total_estimated_eur=round(total_estimated, 2),
        total_actual_eur=round(total_actual, 2),
        variance_eur=round(variance, 2),
        variance_pct=variance_pct,
        item_count=len(items),
        by_category={k: round(v, 2) for k, v in by_category.items()},
    )


# -- Site reports -----------------------------------------------------


@router.get(
    "/projects/{project_id}/build/site-reports",
    response_model=list[DtSiteReportOut],
    operation_id="aeco_listSiteReports",
)
def list_site_reports(
    project_id: int,
    db: SessionDep,
    report_type: Optional[AecoSiteReportType] = None,
    limit: int = Query(default=50, ge=1, le=200),
    offset: int = Query(default=0, ge=0),
):
    if not db.get(DtProject, project_id):
        raise HTTPException(404, detail="Project not found")
    stmt = select(DtSiteReport).where(DtSiteReport.project_id == project_id)
    if report_type:
        stmt = stmt.where(DtSiteReport.report_type == report_type)
    stmt = stmt.order_by(DtSiteReport.report_date.desc()).offset(offset).limit(limit)  # type: ignore[unresolved-attribute]
    return db.exec(stmt).all()


# -- Change orders ----------------------------------------------------


@router.get(
    "/projects/{project_id}/build/change-orders",
    response_model=list[DtChangeOrderOut],
    operation_id="aeco_listChangeOrders",
)
def list_change_orders(
    project_id: int,
    db: SessionDep,
    status: Optional[AecoChangeOrderStatus] = None,
    limit: int = Query(default=50, ge=1, le=200),
    offset: int = Query(default=0, ge=0),
):
    if not db.get(DtProject, project_id):
        raise HTTPException(404, detail="Project not found")
    stmt = select(DtChangeOrder).where(DtChangeOrder.project_id == project_id)
    if status:
        stmt = stmt.where(DtChangeOrder.status == status)
    stmt = stmt.order_by(DtChangeOrder.requested_at.desc()).offset(offset).limit(limit)  # type: ignore[unresolved-attribute]
    return db.exec(stmt).all()
