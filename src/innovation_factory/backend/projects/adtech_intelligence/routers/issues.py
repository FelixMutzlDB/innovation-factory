"""Issue / support-ticket routes for AdTech Intelligence."""
from typing import Annotated, Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlmodel import Session, select

from ....dependencies import get_session
from ..models import (
    AtIssue,
    AtIssueIn,
    AtIssueOut,
    AtIssueUpdate,
    AtCustomerContract,
    AtCustomerContractOut,
    AtAdvertiser,
    AtAdvertiserOut,
    IssueCategory,
    IssuePriority,
    IssueStatus,
)

router = APIRouter(tags=["adtech-issues"])


# -- Issues --------------------------------------------------------------


@router.get(
    "/issues",
    response_model=list[AtIssueOut],
    operation_id="at_listIssues",
)
def list_issues(
    db: Annotated[Session, Depends(get_session)],
    status: Optional[IssueStatus] = None,
    priority: Optional[IssuePriority] = None,
    category: Optional[IssueCategory] = None,
    campaign_id: Optional[int] = None,
    limit: int = Query(default=50, le=200),
    offset: int = 0,
):
    stmt = select(AtIssue)
    if status:
        stmt = stmt.where(AtIssue.status == status)
    if priority:
        stmt = stmt.where(AtIssue.priority == priority)
    if category:
        stmt = stmt.where(AtIssue.category == category)
    if campaign_id:
        stmt = stmt.where(AtIssue.campaign_id == campaign_id)
    stmt = stmt.order_by(AtIssue.created_at.desc()).offset(offset).limit(limit)
    return db.exec(stmt).all()


@router.get(
    "/issues/{issue_id}",
    response_model=AtIssueOut,
    operation_id="at_getIssue",
)
def get_issue(
    issue_id: int,
    db: Annotated[Session, Depends(get_session)],
):
    issue = db.get(AtIssue, issue_id)
    if not issue:
        raise HTTPException(404, detail="Issue not found")
    return issue


@router.patch(
    "/issues/{issue_id}",
    response_model=AtIssueOut,
    operation_id="at_updateIssue",
)
def update_issue(
    issue_id: int,
    body: AtIssueUpdate,
    db: Annotated[Session, Depends(get_session)],
):
    issue = db.get(AtIssue, issue_id)
    if not issue:
        raise HTTPException(404, detail="Issue not found")
    for key, value in body.model_dump(exclude_unset=True).items():
        setattr(issue, key, value)
    db.add(issue)
    db.commit()
    db.refresh(issue)
    return issue


# -- Advertisers (read-only) --------------------------------------------


@router.get(
    "/advertisers",
    response_model=list[AtAdvertiserOut],
    operation_id="at_listAdvertisers",
)
def list_advertisers(
    db: Annotated[Session, Depends(get_session)],
):
    return db.exec(select(AtAdvertiser).order_by(AtAdvertiser.name)).all()


# -- Contracts (read-only) -----------------------------------------------


@router.get(
    "/contracts",
    response_model=list[AtCustomerContractOut],
    operation_id="at_listContracts",
)
def list_contracts(
    db: Annotated[Session, Depends(get_session)],
    advertiser_id: Optional[int] = None,
):
    stmt = select(AtCustomerContract)
    if advertiser_id:
        stmt = stmt.where(AtCustomerContract.advertiser_id == advertiser_id)
    stmt = stmt.order_by(AtCustomerContract.start_date.desc())
    return db.exec(stmt).all()
