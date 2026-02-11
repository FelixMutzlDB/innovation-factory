"""User management router for BSH Home Connect."""
from typing import Annotated
from fastapi import APIRouter, Depends, HTTPException
from sqlmodel import Session, select
from databricks.sdk import WorkspaceClient
from databricks.sdk.service.iam import User as DatabricksUser

from ....dependencies import get_obo_ws, get_session
from ..models import (
    BshCustomer,
    BshCustomerOut,
    BshCustomerIn,
    BshTechnician,
    BshTechnicianOut,
)

router = APIRouter(tags=["bsh-users"])


def get_or_create_customer(db: Session, databricks_user: DatabricksUser) -> BshCustomer:
    """Get existing customer or create a new one from Databricks user."""
    user_id = databricks_user.id
    statement = select(BshCustomer).where(BshCustomer.databricks_user_id == user_id)
    customer = db.exec(statement).first()
    if customer:
        return customer

    email = databricks_user.emails[0].value if databricks_user.emails else f"{user_id}@unknown.com"
    given_name = databricks_user.name.given_name if databricks_user.name else "Unknown"
    family_name = databricks_user.name.family_name if databricks_user.name else "User"

    customer = BshCustomer(
        databricks_user_id=user_id, email=email,
        first_name=given_name, last_name=family_name,
    )
    db.add(customer)
    db.commit()
    db.refresh(customer)
    return customer


def get_or_create_technician(db: Session, databricks_user: DatabricksUser) -> BshTechnician:
    """Get existing technician or create a new one from Databricks user."""
    user_id = databricks_user.id
    statement = select(BshTechnician).where(BshTechnician.databricks_user_id == user_id)
    technician = db.exec(statement).first()
    if technician:
        return technician

    email = databricks_user.emails[0].value if databricks_user.emails else f"{user_id}@unknown.com"
    given_name = databricks_user.name.given_name if databricks_user.name else "Unknown"
    family_name = databricks_user.name.family_name if databricks_user.name else "Technician"

    technician = BshTechnician(
        databricks_user_id=user_id, email=email,
        first_name=given_name, last_name=family_name,
    )
    db.add(technician)
    db.commit()
    db.refresh(technician)
    return technician


@router.get("/customers/me", response_model=BshCustomerOut, operation_id="bsh_getCurrentCustomer")
def get_current_customer(
    obo_ws: Annotated[WorkspaceClient, Depends(get_obo_ws)],
    db: Annotated[Session, Depends(get_session)],
):
    """Get the current customer profile."""
    databricks_user = obo_ws.current_user.me()
    return get_or_create_customer(db, databricks_user)


@router.put("/customers/me", response_model=BshCustomerOut, operation_id="bsh_updateCurrentCustomer")
def update_current_customer(
    customer_update: BshCustomerIn,
    obo_ws: Annotated[WorkspaceClient, Depends(get_obo_ws)],
    db: Annotated[Session, Depends(get_session)],
):
    """Update the current customer profile."""
    databricks_user = obo_ws.current_user.me()
    customer = get_or_create_customer(db, databricks_user)
    for key, value in customer_update.model_dump(exclude_unset=True).items():
        setattr(customer, key, value)
    db.add(customer)
    db.commit()
    db.refresh(customer)
    return customer


@router.get("/technicians/me", response_model=BshTechnicianOut, operation_id="bsh_getCurrentTechnician")
def get_current_technician(
    obo_ws: Annotated[WorkspaceClient, Depends(get_obo_ws)],
    db: Annotated[Session, Depends(get_session)],
):
    """Get the current technician profile."""
    databricks_user = obo_ws.current_user.me()
    return get_or_create_technician(db, databricks_user)


@router.get("/technicians/{technician_id}", response_model=BshTechnicianOut, operation_id="bsh_getTechnician")
def get_technician(technician_id: int, db: Annotated[Session, Depends(get_session)]):
    """Get a technician by ID."""
    technician = db.get(BshTechnician, technician_id)
    if not technician:
        raise HTTPException(status_code=404, detail="Technician not found")
    return technician
