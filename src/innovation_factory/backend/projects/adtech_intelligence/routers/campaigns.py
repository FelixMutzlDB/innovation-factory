"""Campaign and placement CRUD routes for AdTech Intelligence."""
from typing import Annotated, Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlmodel import Session, func, select

from ....dependencies import get_session
from ..models import (
    AtCampaign,
    AtCampaignIn,
    AtCampaignOut,
    AtCampaignUpdate,
    AtPlacement,
    AtPlacementIn,
    AtPlacementOut,
    CampaignStatus,
    CampaignType,
    AtDashboardSummaryOut,
    AtAdInventory,
    AtAnomaly,
    AtPerformanceMetric,
    AnomalyStatus,
    InventoryStatus,
)

router = APIRouter(tags=["adtech-campaigns"])


# -- Dashboard Summary --------------------------------------------------


@router.get(
    "/dashboard/summary",
    response_model=AtDashboardSummaryOut,
    operation_id="at_getDashboardSummary",
)
def get_dashboard_summary(
    db: Annotated[Session, Depends(get_session)],
):
    """Return high-level KPIs for the AdTech dashboard."""
    total_campaigns = db.exec(select(func.count(AtCampaign.id))).one()
    active_campaigns = db.exec(
        select(func.count(AtCampaign.id)).where(AtCampaign.status == CampaignStatus.active)
    ).one()
    total_inventory = db.exec(select(func.count(AtAdInventory.id))).one()
    available_inventory = db.exec(
        select(func.count(AtAdInventory.id)).where(
            AtAdInventory.status == InventoryStatus.available
        )
    ).one()
    total_spend = db.exec(select(func.coalesce(func.sum(AtCampaign.spent), 0))).one()
    total_impressions = db.exec(
        select(func.coalesce(func.sum(AtPerformanceMetric.impressions), 0))
    ).one()
    avg_ctr = db.exec(
        select(func.coalesce(func.avg(AtPerformanceMetric.ctr), 0))
    ).one()
    active_anomalies = db.exec(
        select(func.count(AtAnomaly.id)).where(
            AtAnomaly.status.in_([AnomalyStatus.new, AnomalyStatus.acknowledged, AnomalyStatus.investigating])
        )
    ).one()
    critical_anomalies = db.exec(
        select(func.count(AtAnomaly.id)).where(
            AtAnomaly.severity == "critical",
            AtAnomaly.status.in_([AnomalyStatus.new, AnomalyStatus.acknowledged, AnomalyStatus.investigating]),
        )
    ).one()

    return AtDashboardSummaryOut(
        total_campaigns=total_campaigns,
        active_campaigns=active_campaigns,
        total_inventory=total_inventory,
        available_inventory=available_inventory,
        total_spend=round(float(total_spend), 2),
        total_impressions=int(total_impressions),
        avg_ctr=round(float(avg_ctr), 4),
        active_anomalies=active_anomalies,
        critical_anomalies=critical_anomalies,
    )


# -- Campaigns ----------------------------------------------------------


@router.get(
    "/campaigns",
    response_model=list[AtCampaignOut],
    operation_id="at_listCampaigns",
)
def list_campaigns(
    db: Annotated[Session, Depends(get_session)],
    status: Optional[CampaignStatus] = None,
    campaign_type: Optional[CampaignType] = None,
    advertiser_id: Optional[int] = None,
    limit: int = Query(default=50, le=200),
    offset: int = 0,
):
    """List campaigns with optional filters."""
    stmt = select(AtCampaign)
    if status:
        stmt = stmt.where(AtCampaign.status == status)
    if campaign_type:
        stmt = stmt.where(AtCampaign.campaign_type == campaign_type)
    if advertiser_id:
        stmt = stmt.where(AtCampaign.advertiser_id == advertiser_id)
    stmt = stmt.order_by(AtCampaign.created_at.desc()).offset(offset).limit(limit)
    return db.exec(stmt).all()


@router.get(
    "/campaigns/{campaign_id}",
    response_model=AtCampaignOut,
    operation_id="at_getCampaign",
)
def get_campaign(
    campaign_id: int,
    db: Annotated[Session, Depends(get_session)],
):
    campaign = db.get(AtCampaign, campaign_id)
    if not campaign:
        raise HTTPException(404, detail="Campaign not found")
    return campaign


@router.patch(
    "/campaigns/{campaign_id}",
    response_model=AtCampaignOut,
    operation_id="at_updateCampaign",
)
def update_campaign(
    campaign_id: int,
    body: AtCampaignUpdate,
    db: Annotated[Session, Depends(get_session)],
):
    campaign = db.get(AtCampaign, campaign_id)
    if not campaign:
        raise HTTPException(404, detail="Campaign not found")
    for key, value in body.model_dump(exclude_unset=True).items():
        setattr(campaign, key, value)
    db.add(campaign)
    db.commit()
    db.refresh(campaign)
    return campaign


# -- Placements ---------------------------------------------------------


@router.get(
    "/campaigns/{campaign_id}/placements",
    response_model=list[AtPlacementOut],
    operation_id="at_listPlacements",
)
def list_placements(
    campaign_id: int,
    db: Annotated[Session, Depends(get_session)],
):
    stmt = (
        select(AtPlacement)
        .where(AtPlacement.campaign_id == campaign_id)
        .order_by(AtPlacement.start_date)
    )
    return db.exec(stmt).all()


@router.get(
    "/placements/{placement_id}",
    response_model=AtPlacementOut,
    operation_id="at_getPlacement",
)
def get_placement(
    placement_id: int,
    db: Annotated[Session, Depends(get_session)],
):
    placement = db.get(AtPlacement, placement_id)
    if not placement:
        raise HTTPException(404, detail="Placement not found")
    return placement
