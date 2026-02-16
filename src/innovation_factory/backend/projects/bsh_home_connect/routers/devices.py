"""Device management router for BSH Home Connect."""
from typing import Annotated, List
from fastapi import APIRouter, Depends, HTTPException
from sqlmodel import Session, select
from databricks.sdk import WorkspaceClient

from ....dependencies import get_obo_ws, get_session
from ..models import (
    BshDevice,
    BshDeviceOut,
    BshCustomerDevice,
    BshCustomerDeviceIn,
    BshCustomerDeviceOut,
)
from .users import get_or_create_customer

router = APIRouter(tags=["bsh-devices"])


@router.get("/devices", response_model=List[BshDeviceOut], operation_id="bsh_listDevices")
def list_devices(db: Annotated[Session, Depends(get_session)], category: str | None = None):
    """List all available device types in the catalog."""
    statement = select(BshDevice)
    if category:
        statement = statement.where(BshDevice.category == category)
    devices = db.exec(statement).all()
    return list(devices)


@router.get("/customers/me/devices", response_model=List[BshCustomerDeviceOut], operation_id="bsh_listMyDevices")
def list_my_devices(
    obo_ws: Annotated[WorkspaceClient, Depends(get_obo_ws)],
    db: Annotated[Session, Depends(get_session)],
):
    """Get customer's registered devices."""
    databricks_user = obo_ws.current_user.me()
    customer = get_or_create_customer(db, databricks_user)
    statement = select(BshCustomerDevice).where(BshCustomerDevice.customer_id == customer.id)
    customer_devices = db.exec(statement).all()

    result = []
    for cd in customer_devices:
        device = db.get(BshDevice, cd.device_id)
        result.append(BshCustomerDeviceOut(
            id=cd.id,  # type: ignore[invalid-argument-type]
            customer_id=cd.customer_id, device_id=cd.device_id,
            serial_number=cd.serial_number, purchase_date=cd.purchase_date,
            warranty_expiry_date=cd.warranty_expiry_date, batch_number=cd.batch_number,
            registered_at=cd.registered_at,
            device=BshDeviceOut.model_validate(device.model_dump()) if device else None,
        ))
    return result


@router.post("/customers/me/devices", response_model=BshCustomerDeviceOut, operation_id="bsh_registerDevice")
def register_device(
    device_data: BshCustomerDeviceIn,
    obo_ws: Annotated[WorkspaceClient, Depends(get_obo_ws)],
    db: Annotated[Session, Depends(get_session)],
):
    """Register a new device for the current customer."""
    databricks_user = obo_ws.current_user.me()
    customer = get_or_create_customer(db, databricks_user)

    device = db.get(BshDevice, device_data.device_id)
    if not device:
        raise HTTPException(status_code=404, detail="Device not found")

    existing = db.exec(select(BshCustomerDevice).where(
        BshCustomerDevice.serial_number == device_data.serial_number
    )).first()
    if existing:
        raise HTTPException(status_code=400, detail="Serial number already registered")

    customer_device = BshCustomerDevice(
        customer_id=customer.id, device_id=device_data.device_id,
        serial_number=device_data.serial_number, purchase_date=device_data.purchase_date,
        warranty_expiry_date=device_data.warranty_expiry_date, batch_number=device_data.batch_number,
    )
    db.add(customer_device)
    db.commit()
    db.refresh(customer_device)

    device_fresh = db.get(BshDevice, device_data.device_id)
    return BshCustomerDeviceOut(
        id=customer_device.id,  # type: ignore[invalid-argument-type]
        customer_id=customer_device.customer_id,
        device_id=customer_device.device_id, serial_number=customer_device.serial_number,
        purchase_date=customer_device.purchase_date,
        warranty_expiry_date=customer_device.warranty_expiry_date,
        batch_number=customer_device.batch_number, registered_at=customer_device.registered_at,
        device=BshDeviceOut.model_validate(device_fresh.model_dump()) if device_fresh else None,
    )


@router.get("/customers/me/devices/{device_id}", response_model=BshCustomerDeviceOut, operation_id="bsh_getMyDevice")
def get_my_device(
    device_id: int,
    obo_ws: Annotated[WorkspaceClient, Depends(get_obo_ws)],
    db: Annotated[Session, Depends(get_session)],
):
    """Get details of a registered device."""
    databricks_user = obo_ws.current_user.me()
    customer = get_or_create_customer(db, databricks_user)

    customer_device = db.get(BshCustomerDevice, device_id)
    if not customer_device or customer_device.customer_id != customer.id:
        raise HTTPException(status_code=404, detail="Device not found")

    device = db.get(BshDevice, customer_device.device_id)
    return BshCustomerDeviceOut(
        id=customer_device.id,  # type: ignore[invalid-argument-type]
        customer_id=customer_device.customer_id,
        device_id=customer_device.device_id, serial_number=customer_device.serial_number,
        purchase_date=customer_device.purchase_date,
        warranty_expiry_date=customer_device.warranty_expiry_date,
        batch_number=customer_device.batch_number, registered_at=customer_device.registered_at,
        device=BshDeviceOut.model_validate(device.model_dump()) if device else None,
    )
