"""Marketplace + tools-navigator endpoints.

Powers two front-end views:
- /projects/aeco-hub/tools       — partner tools grouped by lifecycle segment
- /projects/aeco-hub/marketplace — partner apps with integration status
"""
from typing import Optional

from fastapi import APIRouter, HTTPException, Query
from sqlmodel import select

from ....dependencies import SessionDep
from ..models import (
    AecoIntegrationStatus,
    AecoLifecycleSegment,
    DtMarketplaceApp,
    DtMarketplaceAppOut,
    DtMarketplacePartner,
    DtMarketplacePartnerOut,
    DtPartnerIntegration,
    DtPartnerIntegrationOut,
    DtProject,
)

router = APIRouter(tags=["aeco-hub"])


# -- Tools (partners) -------------------------------------------------


@router.get(
    "/tools",
    response_model=list[DtMarketplacePartnerOut],
    operation_id="aeco_listTools",
)
def list_tools(
    db: SessionDep,
    lifecycle_segment: Optional[AecoLifecycleSegment] = None,
):
    """List the AECO tooling ecosystem partners (used by the Tool Navigator)."""
    stmt = select(DtMarketplacePartner)
    if lifecycle_segment:
        stmt = stmt.where(DtMarketplacePartner.lifecycle_segment == lifecycle_segment)
    stmt = stmt.order_by(DtMarketplacePartner.lifecycle_segment, DtMarketplacePartner.name)
    return db.exec(stmt).all()


# -- Marketplace apps --------------------------------------------------


@router.get(
    "/marketplace/apps",
    response_model=list[DtMarketplaceAppOut],
    operation_id="aeco_listMarketplaceApps",
)
def list_marketplace_apps(
    db: SessionDep,
    lifecycle_segment: Optional[AecoLifecycleSegment] = None,
    featured_only: bool = False,
    limit: int = Query(default=100, ge=1, le=500),
    offset: int = Query(default=0, ge=0),
):
    """List apps, joined with their partner so we can show one row per app."""
    stmt = (
        select(DtMarketplaceApp, DtMarketplacePartner)
        .join(DtMarketplacePartner, DtMarketplaceApp.partner_id == DtMarketplacePartner.id)  # type: ignore[invalid-argument-type]
    )
    if lifecycle_segment:
        stmt = stmt.where(DtMarketplaceApp.lifecycle_segment == lifecycle_segment)
    if featured_only:
        stmt = stmt.where(DtMarketplaceApp.is_featured == True)  # noqa: E712
    stmt = (
        stmt.order_by(DtMarketplaceApp.is_featured.desc(), DtMarketplaceApp.name)  # type: ignore[unresolved-attribute]
        .offset(offset)
        .limit(limit)
    )
    rows = db.exec(stmt).all()
    return [
        DtMarketplaceAppOut(
            id=app.id or 0,
            partner_id=app.partner_id,
            partner_name=partner.name,
            name=app.name,
            description=app.description,
            lifecycle_segment=app.lifecycle_segment,
            logo_url=app.logo_url,
            is_featured=app.is_featured,
        )
        for app, partner in rows
    ]


# -- Integrations per project -----------------------------------------


@router.get(
    "/projects/{project_id}/integrations",
    response_model=list[DtPartnerIntegrationOut],
    operation_id="aeco_listProjectIntegrations",
)
def list_project_integrations(
    project_id: int,
    db: SessionDep,
    status: Optional[AecoIntegrationStatus] = None,
):
    """Apps integrated with a specific construction project."""
    if not db.get(DtProject, project_id):
        raise HTTPException(404, detail="Project not found")
    stmt = (
        select(DtPartnerIntegration, DtMarketplaceApp, DtMarketplacePartner)
        .join(DtMarketplaceApp, DtPartnerIntegration.app_id == DtMarketplaceApp.id)  # type: ignore[invalid-argument-type]
        .join(DtMarketplacePartner, DtMarketplaceApp.partner_id == DtMarketplacePartner.id)  # type: ignore[invalid-argument-type]
        .where(DtPartnerIntegration.project_id == project_id)
    )
    if status:
        stmt = stmt.where(DtPartnerIntegration.status == status)
    rows = db.exec(stmt).all()
    return [
        DtPartnerIntegrationOut(
            id=integration.id or 0,
            project_id=integration.project_id,
            app_id=integration.app_id,
            app_name=app.name,
            partner_name=partner.name,
            lifecycle_segment=app.lifecycle_segment,
            status=integration.status,
            activated_at=integration.activated_at,
            notes=integration.notes,
        )
        for integration, app, partner in rows
    ]
