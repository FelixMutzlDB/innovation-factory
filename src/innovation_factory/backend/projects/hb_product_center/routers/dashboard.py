"""Dashboard aggregation endpoints using Unity Catalog tables."""

from datetime import datetime, timedelta, timezone
from typing import Annotated

from databricks.sdk import WorkspaceClient
from fastapi import APIRouter, Depends

from ....dependencies import RuntimeDep
from ..databricks_config import UC_CATALOG, UC_SCHEMA, WAREHOUSE_ID
from ..models import HbDashboardSummary, HbTrendPoint
from ..services.uc_query_service import count_rows, avg_column, execute_query

router = APIRouter(prefix="/dashboard", tags=["hb-product-center"])


def get_ws(runtime: RuntimeDep) -> WorkspaceClient:
    """Get WorkspaceClient from runtime (uses app SP identity)."""
    return runtime.ws


WsDep = Annotated[WorkspaceClient, Depends(get_ws)]


@router.get("/summary", response_model=HbDashboardSummary, operation_id="hb_getDashboardSummary")
def get_dashboard_summary(ws: WsDep):
    """Get dashboard summary metrics from Unity Catalog tables."""
    # Products
    total_products = count_rows(ws, "hb_products")
    active_products = count_rows(ws, "hb_products", "status = 'active'")

    # Recognition jobs
    today_str = datetime.now(timezone.utc).strftime("%Y-%m-%d")
    jobs_today = count_rows(ws, "hb_recognition_jobs", f"created_at >= '{today_str}'")
    jobs_total = count_rows(ws, "hb_recognition_jobs")

    # Quality inspections
    avg_quality = round(avg_column(ws, "hb_quality_inspections", "overall_score", "overall_score > 0"), 1)
    pending_inspections = count_rows(ws, "hb_quality_inspections", "status = 'pending'")

    # Auth verifications
    total_verifications = count_rows(ws, "hb_auth_verifications")
    verified = count_rows(ws, "hb_auth_verifications", "status = 'verified'")
    auth_rate = round(verified / total_verifications * 100, 1) if total_verifications > 0 else 0.0

    # Auth alerts
    open_alerts = count_rows(ws, "hb_auth_alerts", "resolution = 'open'")

    # Supply chain
    sc_events = count_rows(ws, "hb_supply_chain_events")

    # Sustainability
    avg_sustainability = round(avg_column(ws, "hb_sustainability_metrics", "recycled_content_pct"), 1)

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
def get_dashboard_trends(ws: WsDep):
    """Return daily recognition job counts for the last 30 days from Unity Catalog."""
    table = f"{UC_CATALOG}.{UC_SCHEMA}.hb_recognition_jobs"
    now = datetime.now(timezone.utc)
    start_date = (now - timedelta(days=30)).strftime("%Y-%m-%d")

    # Single query to get all daily counts
    sql = f"""
        SELECT DATE(created_at) as day, COUNT(*) as cnt
        FROM {table}
        WHERE created_at >= '{start_date}'
        GROUP BY DATE(created_at)
        ORDER BY day
    """
    rows = execute_query(ws, sql)
    daily_counts = {row[0]: int(row[1]) for row in rows}

    # Build result with all 31 days (including today)
    points = []
    for i in range(30, -1, -1):
        day = now - timedelta(days=i)
        day_str = day.strftime("%Y-%m-%d")
        count = daily_counts.get(day_str, 0)
        points.append(HbTrendPoint(
            date=day_str,
            value=float(count),
            label="Recognition Jobs",
        ))
    return points
