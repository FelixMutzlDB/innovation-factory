"""Support ticket management router for BSH Home Connect."""
from typing import Annotated, List
from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Form
from sqlmodel import Session, select
from databricks.sdk import WorkspaceClient
from datetime import datetime, timezone

from ....dependencies import get_obo_ws, get_session
from ..models import (
    BshTicket,
    BshTicketIn,
    BshTicketOut,
    BshTicketUpdate,
    BshTicketStatus,
    BshCustomerDevice,
    BshDevice,
    BshCustomer,
    BshCustomerOut,
    BshCustomerDeviceOut,
    BshDeviceOut,
    BshTechnician,
    BshTechnicianOut,
    BshTicketNote,
    BshTicketNoteIn,
    BshTicketNoteOut,
    BshTicketMedia,
    MediaType,
    UserRole,
)
from .users import get_or_create_customer, get_or_create_technician

router = APIRouter(tags=["bsh-tickets"])


def _build_ticket_out(ticket: BshTicket, db: Session) -> BshTicketOut:
    """Build BshTicketOut with relationships."""
    customer_device = db.get(BshCustomerDevice, ticket.customer_device_id)
    device = db.get(BshDevice, customer_device.device_id) if customer_device else None

    return BshTicketOut(
        id=ticket.id,  # type: ignore[invalid-argument-type]
        customer_id=ticket.customer_id,
        customer_device_id=ticket.customer_device_id,
        technician_id=ticket.technician_id,
        title=ticket.title, description=ticket.description,
        status=ticket.status, priority=ticket.priority,
        issue_summary=ticket.issue_summary,
        troubleshooting_attempted=ticket.troubleshooting_attempted,
        shipping_label_url=ticket.shipping_label_url,
        tracking_number=ticket.tracking_number,
        created_at=ticket.created_at, updated_at=ticket.updated_at,
        assigned_at=ticket.assigned_at, completed_at=ticket.completed_at,
        customer_device=BshCustomerDeviceOut(
            id=customer_device.id,  # type: ignore[invalid-argument-type]
            customer_id=customer_device.customer_id,
            device_id=customer_device.device_id,
            serial_number=customer_device.serial_number,
            purchase_date=customer_device.purchase_date,
            warranty_expiry_date=customer_device.warranty_expiry_date,
            batch_number=customer_device.batch_number,
            registered_at=customer_device.registered_at,
            device=BshDeviceOut.model_validate(device.model_dump()) if device else None,
        ) if customer_device else None,
    )


@router.post("/tickets", response_model=BshTicketOut, operation_id="bsh_createTicket")
def create_ticket(
    ticket_data: BshTicketIn,
    obo_ws: Annotated[WorkspaceClient, Depends(get_obo_ws)],
    db: Annotated[Session, Depends(get_session)],
):
    """Create a new support ticket."""
    databricks_user = obo_ws.current_user.me()
    customer = get_or_create_customer(db, databricks_user)

    customer_device = db.get(BshCustomerDevice, ticket_data.customer_device_id)
    if not customer_device or customer_device.customer_id != customer.id:
        raise HTTPException(status_code=404, detail="Device not found")

    ticket = BshTicket(
        customer_id=customer.id,
        customer_device_id=ticket_data.customer_device_id,
        title=ticket_data.title,
        description=ticket_data.description,
        priority=ticket_data.priority,
        status=BshTicketStatus.open,
    )
    db.add(ticket)
    db.commit()
    db.refresh(ticket)
    return _build_ticket_out(ticket, db)


@router.get("/tickets", response_model=List[BshTicketOut], operation_id="bsh_listTickets")
def list_tickets(
    obo_ws: Annotated[WorkspaceClient, Depends(get_obo_ws)],
    db: Annotated[Session, Depends(get_session)],
    status: BshTicketStatus | None = None,
    role: str | None = None,
):
    """List tickets filtered by role."""
    databricks_user = obo_ws.current_user.me()

    if not role:
        customer_statement = select(BshCustomer).where(BshCustomer.databricks_user_id == databricks_user.id)
        customer = db.exec(customer_statement).first()
        role = "customer" if customer else "technician"

    if role == "customer":
        customer = get_or_create_customer(db, databricks_user)
        statement = select(BshTicket).where(BshTicket.customer_id == customer.id)
    else:
        technician = get_or_create_technician(db, databricks_user)
        statement = select(BshTicket).where(BshTicket.technician_id == technician.id)

    if status:
        statement = statement.where(BshTicket.status == status)
    statement = statement.order_by(BshTicket.created_at.desc())  # type: ignore[unresolved-attribute]
    tickets = db.exec(statement).all()
    return [_build_ticket_out(t, db) for t in tickets]


@router.get("/tickets/{ticket_id}", response_model=BshTicketOut, operation_id="bsh_getTicket")
def get_ticket(
    ticket_id: int,
    obo_ws: Annotated[WorkspaceClient, Depends(get_obo_ws)],
    db: Annotated[Session, Depends(get_session)],
):
    """Get ticket details."""
    ticket = db.get(BshTicket, ticket_id)
    if not ticket:
        raise HTTPException(status_code=404, detail="Ticket not found")
    return _build_ticket_out(ticket, db)


@router.patch("/tickets/{ticket_id}", response_model=BshTicketOut, operation_id="bsh_updateTicket")
def update_ticket(
    ticket_id: int,
    ticket_update: BshTicketUpdate,
    obo_ws: Annotated[WorkspaceClient, Depends(get_obo_ws)],
    db: Annotated[Session, Depends(get_session)],
):
    """Update ticket status, assignment, shipping info."""
    ticket = db.get(BshTicket, ticket_id)
    if not ticket:
        raise HTTPException(status_code=404, detail="Ticket not found")

    for key, value in ticket_update.model_dump(exclude_unset=True).items():
        setattr(ticket, key, value)
    ticket.updated_at = datetime.now(timezone.utc)

    if ticket_update.technician_id and not ticket.assigned_at:
        ticket.assigned_at = datetime.now(timezone.utc)
    if ticket_update.status == BshTicketStatus.resolved and not ticket.completed_at:
        ticket.completed_at = datetime.now(timezone.utc)

    db.add(ticket)
    db.commit()
    db.refresh(ticket)
    return _build_ticket_out(ticket, db)


@router.post("/tickets/{ticket_id}/notes", response_model=BshTicketNoteOut, operation_id="bsh_addTicketNote")
def add_ticket_note(
    ticket_id: int,
    note_data: BshTicketNoteIn,
    obo_ws: Annotated[WorkspaceClient, Depends(get_obo_ws)],
    db: Annotated[Session, Depends(get_session)],
):
    """Add a note to a ticket."""
    databricks_user = obo_ws.current_user.me()
    ticket = db.get(BshTicket, ticket_id)
    if not ticket:
        raise HTTPException(status_code=404, detail="Ticket not found")

    customer_statement = select(BshCustomer).where(BshCustomer.databricks_user_id == databricks_user.id)
    customer = db.exec(customer_statement).first()

    if customer and ticket.customer_id == customer.id:
        role = UserRole.customer
        author_id = customer.id
    else:
        technician = get_or_create_technician(db, databricks_user)
        role = UserRole.technician
        author_id = technician.id

    note = BshTicketNote(
        ticket_id=ticket_id, content=note_data.content,
        author_role=role, author_id=author_id, is_internal=note_data.is_internal,
    )
    db.add(note)
    db.commit()
    db.refresh(note)
    return note


@router.get("/tickets/{ticket_id}/notes", response_model=List[BshTicketNoteOut], operation_id="bsh_listTicketNotes")
def list_ticket_notes(
    ticket_id: int,
    obo_ws: Annotated[WorkspaceClient, Depends(get_obo_ws)],
    db: Annotated[Session, Depends(get_session)],
):
    """List notes for a ticket."""
    databricks_user = obo_ws.current_user.me()
    ticket = db.get(BshTicket, ticket_id)
    if not ticket:
        raise HTTPException(status_code=404, detail="Ticket not found")

    customer_statement = select(BshCustomer).where(BshCustomer.databricks_user_id == databricks_user.id)
    customer = db.exec(customer_statement).first()
    is_customer = customer and ticket.customer_id == customer.id

    statement = select(BshTicketNote).where(BshTicketNote.ticket_id == ticket_id)
    if is_customer:
        statement = statement.where(BshTicketNote.is_internal == False)
    statement = statement.order_by(BshTicketNote.created_at.asc())  # type: ignore[unresolved-attribute]
    return list(db.exec(statement).all())


@router.post("/tickets/{ticket_id}/media", operation_id="bsh_uploadTicketMedia")
async def upload_ticket_media(
    ticket_id: int,
    file: UploadFile = File(...),
    media_type: str = Form(...),
    obo_ws: Annotated[WorkspaceClient, Depends(get_obo_ws)] = None,  # type: ignore[invalid-parameter-default]
    db: Annotated[Session, Depends(get_session)] = None,  # type: ignore[invalid-parameter-default]
):
    """Upload media to a ticket."""
    ticket = db.get(BshTicket, ticket_id)
    if not ticket:
        raise HTTPException(status_code=404, detail="Ticket not found")

    databricks_user = obo_ws.current_user.me()
    customer_statement = select(BshCustomer).where(BshCustomer.databricks_user_id == databricks_user.id)
    customer = db.exec(customer_statement).first()
    role = UserRole.customer if customer and ticket.customer_id == customer.id else UserRole.technician

    file_url = f"/uploads/tickets/{ticket_id}/{file.filename}"
    media = BshTicketMedia(
        ticket_id=ticket_id, media_type=MediaType(media_type),
        file_url=file_url, file_name=file.filename,
        file_size=file.size, mime_type=file.content_type,
        uploaded_by_role=role,
    )
    db.add(media)
    db.commit()
    return {"message": "Media uploaded successfully", "file_url": file_url}


@router.post("/tickets/{ticket_id}/shipping-label", operation_id="bsh_generateShippingLabel")
def generate_shipping_label(
    ticket_id: int,
    obo_ws: Annotated[WorkspaceClient, Depends(get_obo_ws)],
    db: Annotated[Session, Depends(get_session)],
):
    """Generate a shipping label for the ticket."""
    ticket = db.get(BshTicket, ticket_id)
    if not ticket:
        raise HTTPException(status_code=404, detail="Ticket not found")

    label_url = f"https://shipping.example.com/labels/{ticket_id}.pdf"
    tracking_number = f"BSH{ticket_id:08d}"

    ticket.shipping_label_url = label_url
    ticket.tracking_number = tracking_number
    ticket.status = BshTicketStatus.shipped_for_repair
    ticket.updated_at = datetime.now(timezone.utc)

    db.add(ticket)
    db.commit()
    return {"shipping_label_url": label_url, "tracking_number": tracking_number}
