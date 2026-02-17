"""Workforce and shift endpoints for the ASM Cockpit."""
from datetime import date, timedelta
from typing import Optional

from fastapi import APIRouter, Query
from sqlmodel import select

from ....dependencies import SessionDep
from ..models import (
    MacWorkforceShift,
    MacWorkforceShiftOut,
    MacIssue,
    MacIssueOut,
    MacCustomerProfile,
    MacCustomerProfileOut,
    MacCustomerContract,
    MacCustomerContractOut,
)

router = APIRouter(prefix="/workforce", tags=["mac-workforce"])


@router.get("/shifts", response_model=list[MacWorkforceShiftOut], operation_id="mac_listWorkforceShifts")
def list_shifts(
    session: SessionDep,
    station_id: Optional[int] = Query(None),
    days: int = Query(7, ge=1, le=90),
    limit: int = Query(500, ge=1, le=5000),
):
    """List workforce shift records."""
    cutoff = date.today() - timedelta(days=days)
    q = select(MacWorkforceShift).where(MacWorkforceShift.shift_date >= cutoff)
    if station_id is not None:
        q = q.where(MacWorkforceShift.station_id == station_id)
    q = q.order_by(MacWorkforceShift.shift_date.desc()).limit(limit)  # type: ignore[unresolved-attribute]
    return session.exec(q).all()


@router.get("/issues", response_model=list[MacIssueOut], operation_id="mac_listIssues")
def list_issues(
    session: SessionDep,
    station_id: Optional[int] = Query(None),
    status: Optional[str] = Query(None),
    category: Optional[str] = Query(None),
    limit: int = Query(100, ge=1, le=500),
):
    """List operational issues."""
    q = select(MacIssue)
    if station_id is not None:
        q = q.where(MacIssue.station_id == station_id)
    if status:
        q = q.where(MacIssue.status == status)
    if category:
        q = q.where(MacIssue.category == category)
    q = q.order_by(MacIssue.created_at.desc()).limit(limit)  # type: ignore[unresolved-attribute]
    return session.exec(q).all()


@router.get("/customers", response_model=list[MacCustomerProfileOut], operation_id="mac_listCustomerProfiles")
def list_customer_profiles(session: SessionDep):
    """List B2B customer profiles."""
    return session.exec(select(MacCustomerProfile).order_by(MacCustomerProfile.company_name)).all()


@router.get("/customers/{customer_id}/contracts", response_model=list[MacCustomerContractOut], operation_id="mac_listCustomerContracts")
def list_customer_contracts(customer_id: int, session: SessionDep):
    """List contracts for a customer."""
    return session.exec(
        select(MacCustomerContract)
        .where(MacCustomerContract.customer_id == customer_id)
        .order_by(MacCustomerContract.start_date.desc())  # type: ignore[unresolved-attribute]
    ).all()
