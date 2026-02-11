"""API router for support tickets."""
from fastapi import APIRouter, HTTPException, UploadFile, File
from sqlmodel import select
from datetime import datetime

from ....dependencies import SessionDep
from ..models import (
    VhTicket,
    VhTicketStatus,
    VhTicketIn,
    VhTicketUpdate,
    VhTicketOut,
    VhTicketMedia,
    VhHousehold,
)

router = APIRouter(prefix="/tickets", tags=["vh-tickets"])


@router.get("", response_model=list[VhTicketOut], operation_id="vh_list_tickets")
def list_tickets(
    db: SessionDep,
    household_id: int | None = None,
    status: VhTicketStatus | None = None,
):
    """List support tickets with optional filters."""
    query = select(VhTicket)
    if household_id:
        query = query.where(VhTicket.household_id == household_id)
    if status:
        query = query.where(VhTicket.status == status)
    query = query.order_by(VhTicket.created_at.desc())
    tickets = db.exec(query).all()
    return list(tickets)


@router.post("", response_model=VhTicketOut, operation_id="vh_create_ticket")
def create_ticket(ticket_in: VhTicketIn, household_id: int, db: SessionDep):
    """Create a new support ticket."""
    household = db.get(VhHousehold, household_id)
    if not household:
        raise HTTPException(status_code=404, detail="Household not found")

    ticket = VhTicket(
        household_id=household_id,
        device_id=ticket_in.device_id,
        title=ticket_in.title,
        description=ticket_in.description,
        priority=ticket_in.priority,
        status=VhTicketStatus.new,
    )
    db.add(ticket)
    db.commit()
    db.refresh(ticket)
    return ticket


@router.get("/{ticket_id}", response_model=VhTicketOut, operation_id="vh_get_ticket")
def get_ticket(ticket_id: int, db: SessionDep):
    """Get ticket details."""
    ticket = db.get(VhTicket, ticket_id)
    if not ticket:
        raise HTTPException(status_code=404, detail="Ticket not found")
    return ticket


@router.patch("/{ticket_id}", response_model=VhTicketOut, operation_id="vh_update_ticket")
def update_ticket(ticket_id: int, ticket_update: VhTicketUpdate, db: SessionDep):
    """Update ticket status or notes."""
    ticket = db.get(VhTicket, ticket_id)
    if not ticket:
        raise HTTPException(status_code=404, detail="Ticket not found")

    if ticket_update.status:
        ticket.status = ticket_update.status
        if ticket_update.status == VhTicketStatus.resolved:
            ticket.resolved_at = datetime.utcnow()
    if ticket_update.resolution_notes:
        ticket.resolution_notes = ticket_update.resolution_notes
    ticket.updated_at = datetime.utcnow()

    db.add(ticket)
    db.commit()
    db.refresh(ticket)
    return ticket


@router.post("/{ticket_id}/media", operation_id="vh_upload_ticket_media")
async def upload_ticket_media(ticket_id: int, db: SessionDep, file: UploadFile = File(...)):
    """Upload media file for a ticket."""
    ticket = db.get(VhTicket, ticket_id)
    if not ticket:
        raise HTTPException(status_code=404, detail="Ticket not found")

    media = VhTicketMedia(
        ticket_id=ticket_id,
        media_type="image" if file.content_type and file.content_type.startswith("image") else "document",
        file_url=f"/uploads/{ticket_id}/{file.filename}",
        file_name=file.filename or "unknown",
        file_size=0,
        mime_type=file.content_type,
    )
    db.add(media)
    db.commit()
    return {"message": "Media uploaded successfully", "media_id": media.id}
