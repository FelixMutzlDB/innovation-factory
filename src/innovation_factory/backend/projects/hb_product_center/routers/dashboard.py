"""Dashboard aggregation endpoints."""

from datetime import datetime, timedelta, timezone

from fastapi import APIRouter
from sqlmodel import func, select

from ....dependencies import SessionDep
from ..models import (
    AlertResolution,
    HbAuthAlert,
    HbAuthVerification,
    HbDashboardSummary,
    HbProduct,
    HbQualityInspection,
    HbRecognitionJob,
    HbSupplyChainEvent,
    HbSustainabilityMetric,
    HbTrendPoint,
    InspectionStatus,
    ProductStatus,
    VerificationStatus,
)

router = APIRouter(prefix="/dashboard", tags=["hb-product-center"])


@router.get("/summary", response_model=HbDashboardSummary, operation_id="hb_getDashboardSummary")
def get_dashboard_summary(session: SessionDep):
    total_products = session.exec(select(func.count(HbProduct.id))).one()
    active_products = session.exec(
        select(func.count(HbProduct.id)).where(HbProduct.status == ProductStatus.active)
    ).one()

    today_start = datetime.now(timezone.utc).replace(hour=0, minute=0, second=0, microsecond=0)
    jobs_today = session.exec(
        select(func.count(HbRecognitionJob.id)).where(HbRecognitionJob.created_at >= today_start)
    ).one()
    jobs_total = session.exec(select(func.count(HbRecognitionJob.id))).one()

    scores = session.exec(
        select(HbQualityInspection.overall_score).where(HbQualityInspection.overall_score > 0)
    ).all()
    avg_quality = round(sum(scores) / len(scores), 1) if scores else 0.0

    pending_inspections = session.exec(
        select(func.count(HbQualityInspection.id)).where(HbQualityInspection.status == InspectionStatus.pending)
    ).one()

    total_verifications = session.exec(select(func.count(HbAuthVerification.id))).one()
    verified = session.exec(
        select(func.count(HbAuthVerification.id)).where(HbAuthVerification.status == VerificationStatus.verified)
    ).one()
    auth_rate = round(verified / total_verifications * 100, 1) if total_verifications > 0 else 0.0

    open_alerts = session.exec(
        select(func.count(HbAuthAlert.id)).where(HbAuthAlert.resolution == AlertResolution.open)
    ).one()

    sc_events = session.exec(select(func.count(HbSupplyChainEvent.id))).one()

    sustainability_scores = session.exec(select(HbSustainabilityMetric.recycled_content_pct)).all()
    avg_sustainability = round(sum(sustainability_scores) / len(sustainability_scores), 1) if sustainability_scores else 0.0

    return HbDashboardSummary(
        total_products=total_products,
        active_products=active_products,
        recognition_jobs_today=jobs_today,
        recognition_jobs_total=jobs_total,
        avg_quality_score=avg_quality,
        inspections_pending=pending_inspections,
        auth_success_rate=auth_rate,
        auth_alerts_open=open_alerts,
        supply_chain_events_total=sc_events,
        avg_sustainability_score=avg_sustainability,
    )


@router.get("/trends", response_model=list[HbTrendPoint], operation_id="hb_getDashboardTrends")
def get_dashboard_trends(session: SessionDep):
    """Return daily recognition job counts for the last 30 days."""
    now = datetime.now(timezone.utc)
    points = []
    for i in range(30, -1, -1):
        day = now - timedelta(days=i)
        day_start = day.replace(hour=0, minute=0, second=0, microsecond=0)
        day_end = day_start + timedelta(days=1)
        count = session.exec(
            select(func.count(HbRecognitionJob.id)).where(
                HbRecognitionJob.created_at >= day_start,
                HbRecognitionJob.created_at < day_end,
            )
        ).one()
        points.append(HbTrendPoint(
            date=day_start.strftime("%Y-%m-%d"),
            value=float(count),
            label="Recognition Jobs",
        ))
    return points
