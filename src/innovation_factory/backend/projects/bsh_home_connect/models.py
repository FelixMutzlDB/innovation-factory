from datetime import date, datetime
from enum import Enum
from typing import Optional

from pydantic import BaseModel
from sqlmodel import Column, Field, JSON, Relationship, SQLModel, Text


# ============================================================================
# Enums
# ============================================================================


class BshTicketStatus(str, Enum):
    open = "open"
    in_progress = "in_progress"
    awaiting_parts = "awaiting_parts"
    awaiting_customer = "awaiting_customer"
    shipped_for_repair = "shipped_for_repair"
    in_repair = "in_repair"
    resolved = "resolved"
    closed = "closed"


class UserRole(str, Enum):
    customer = "customer"
    technician = "technician"
    system = "system"


class DeviceCategory(str, Enum):
    washing_machine = "washing_machine"
    dryer = "dryer"
    dishwasher = "dishwasher"
    refrigerator = "refrigerator"
    oven = "oven"
    cooktop = "cooktop"
    microwave = "microwave"
    coffee_machine = "coffee_machine"
    vacuum_cleaner = "vacuum_cleaner"
    other = "other"


class MediaType(str, Enum):
    image = "image"
    video = "video"
    document = "document"


class BshChatRole(str, Enum):
    user = "user"
    assistant = "assistant"
    system = "system"


# ============================================================================
# SQLModel Database Models (all table names prefixed with bsh_)
# ============================================================================


class BshCustomer(SQLModel, table=True):
    __tablename__ = "bsh_customers"

    id: Optional[int] = Field(default=None, primary_key=True)
    databricks_user_id: str = Field(unique=True, index=True)
    email: str = Field(unique=True, index=True)
    first_name: str
    last_name: str
    phone: Optional[str] = None
    address: Optional[str] = None
    city: Optional[str] = None
    postal_code: Optional[str] = None
    country: Optional[str] = None
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)

    devices: list["BshCustomerDevice"] = Relationship(back_populates="customer")
    tickets: list["BshTicket"] = Relationship(back_populates="customer")


class BshTechnician(SQLModel, table=True):
    __tablename__ = "bsh_technicians"

    id: Optional[int] = Field(default=None, primary_key=True)
    databricks_user_id: str = Field(unique=True, index=True)
    email: str = Field(unique=True, index=True)
    first_name: str
    last_name: str
    phone: Optional[str] = None
    specialization: Optional[str] = None
    certification_level: Optional[str] = None
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)

    tickets: list["BshTicket"] = Relationship(back_populates="technician")


class BshDevice(SQLModel, table=True):
    __tablename__ = "bsh_devices"

    id: Optional[int] = Field(default=None, primary_key=True)
    model_number: str = Field(unique=True, index=True)
    brand: str
    category: DeviceCategory
    name: str
    description: Optional[str] = Field(default=None, sa_column=Column(Text, nullable=True))
    specifications: Optional[dict] = Field(default=None, sa_column=Column(JSON))
    image_url: Optional[str] = None
    created_at: datetime = Field(default_factory=datetime.utcnow)

    customer_devices: list["BshCustomerDevice"] = Relationship(back_populates="device")
    knowledge_articles: list["BshKnowledgeArticle"] = Relationship(
        back_populates="device"
    )
    documents: list["BshDocument"] = Relationship(back_populates="device")


class BshCustomerDevice(SQLModel, table=True):
    __tablename__ = "bsh_customer_devices"

    id: Optional[int] = Field(default=None, primary_key=True)
    customer_id: int = Field(foreign_key="bsh_customers.id", index=True)
    device_id: int = Field(foreign_key="bsh_devices.id", index=True)
    serial_number: str
    purchase_date: Optional[date] = None
    warranty_expiry_date: Optional[date] = None
    batch_number: Optional[str] = None
    registered_at: datetime = Field(default_factory=datetime.utcnow)

    customer: Optional[BshCustomer] = Relationship(back_populates="devices")
    device: Optional[BshDevice] = Relationship(back_populates="customer_devices")
    tickets: list["BshTicket"] = Relationship(back_populates="customer_device")


class BshTicket(SQLModel, table=True):
    __tablename__ = "bsh_tickets"

    id: Optional[int] = Field(default=None, primary_key=True)
    customer_id: int = Field(foreign_key="bsh_customers.id", index=True)
    customer_device_id: int = Field(foreign_key="bsh_customer_devices.id", index=True)
    technician_id: Optional[int] = Field(
        default=None, foreign_key="bsh_technicians.id", index=True
    )
    title: str
    description: str = Field(sa_column=Column(Text))
    status: BshTicketStatus = Field(default=BshTicketStatus.open)
    priority: int = Field(default=3)
    issue_summary: Optional[str] = Field(
        default=None, sa_column=Column(Text, nullable=True)
    )
    troubleshooting_attempted: Optional[str] = Field(
        default=None, sa_column=Column(Text, nullable=True)
    )
    shipping_label_url: Optional[str] = None
    tracking_number: Optional[str] = None
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
    assigned_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None

    customer: Optional[BshCustomer] = Relationship(back_populates="tickets")
    customer_device: Optional[BshCustomerDevice] = Relationship(
        back_populates="tickets"
    )
    technician: Optional[BshTechnician] = Relationship(back_populates="tickets")
    media: list["BshTicketMedia"] = Relationship(back_populates="ticket")
    notes: list["BshTicketNote"] = Relationship(back_populates="ticket")
    chat_sessions: list["BshChatSession"] = Relationship(back_populates="ticket")


class BshTicketMedia(SQLModel, table=True):
    __tablename__ = "bsh_ticket_media"

    id: Optional[int] = Field(default=None, primary_key=True)
    ticket_id: int = Field(foreign_key="bsh_tickets.id", index=True)
    media_type: MediaType
    file_url: str
    file_name: str
    file_size: Optional[int] = None
    mime_type: Optional[str] = None
    uploaded_by_role: UserRole
    uploaded_at: datetime = Field(default_factory=datetime.utcnow)

    ticket: Optional[BshTicket] = Relationship(back_populates="media")


class BshTicketNote(SQLModel, table=True):
    __tablename__ = "bsh_ticket_notes"

    id: Optional[int] = Field(default=None, primary_key=True)
    ticket_id: int = Field(foreign_key="bsh_tickets.id", index=True)
    content: str = Field(sa_column=Column(Text))
    author_role: UserRole
    author_id: Optional[int] = None
    is_internal: bool = Field(default=False)
    created_at: datetime = Field(default_factory=datetime.utcnow)

    ticket: Optional[BshTicket] = Relationship(back_populates="notes")


class BshKnowledgeArticle(SQLModel, table=True):
    __tablename__ = "bsh_knowledge_articles"

    id: Optional[int] = Field(default=None, primary_key=True)
    device_id: Optional[int] = Field(
        default=None, foreign_key="bsh_devices.id", index=True
    )
    title: str
    content: str = Field(sa_column=Column(Text))
    category: DeviceCategory
    issue_type: Optional[str] = None
    tags: Optional[list[str]] = Field(default=None, sa_column=Column(JSON))
    view_count: int = Field(default=0)
    helpful_count: int = Field(default=0)
    embedding: Optional[list[float]] = Field(default=None, sa_column=Column(JSON))
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)

    device: Optional[BshDevice] = Relationship(back_populates="knowledge_articles")


class BshDocument(SQLModel, table=True):
    __tablename__ = "bsh_documents"

    id: Optional[int] = Field(default=None, primary_key=True)
    device_id: int = Field(foreign_key="bsh_devices.id", index=True)
    title: str
    document_type: str
    content: Optional[str] = Field(default=None, sa_column=Column(Text, nullable=True))
    file_url: Optional[str] = None
    language: str = Field(default="en")
    version: Optional[str] = None
    embedding: Optional[list[float]] = Field(default=None, sa_column=Column(JSON))
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)

    device: Optional[BshDevice] = Relationship(back_populates="documents")


class BshChatSession(SQLModel, table=True):
    __tablename__ = "bsh_chat_sessions"

    id: Optional[int] = Field(default=None, primary_key=True)
    ticket_id: int = Field(foreign_key="bsh_tickets.id", index=True)
    session_type: str = Field(default="troubleshooting")
    started_at: datetime = Field(default_factory=datetime.utcnow)
    ended_at: Optional[datetime] = None

    ticket: Optional[BshTicket] = Relationship(back_populates="chat_sessions")
    messages: list["BshChatMessage"] = Relationship(back_populates="session")


class BshChatMessage(SQLModel, table=True):
    __tablename__ = "bsh_chat_messages"

    id: Optional[int] = Field(default=None, primary_key=True)
    session_id: int = Field(foreign_key="bsh_chat_sessions.id", index=True)
    role: BshChatRole
    content: str = Field(sa_column=Column(Text))
    sources: Optional[list[dict]] = Field(default=None, sa_column=Column(JSON))
    tokens_used: Optional[int] = None
    created_at: datetime = Field(default_factory=datetime.utcnow)

    session: Optional[BshChatSession] = Relationship(back_populates="messages")


# ============================================================================
# Pydantic Input/Output Models (prefixed with Bsh)
# ============================================================================


class BshCustomerIn(BaseModel):
    first_name: str
    last_name: str
    phone: Optional[str] = None
    address: Optional[str] = None
    city: Optional[str] = None
    postal_code: Optional[str] = None
    country: Optional[str] = None


class BshCustomerOut(BaseModel):
    id: int
    databricks_user_id: str
    email: str
    first_name: str
    last_name: str
    phone: Optional[str] = None
    address: Optional[str] = None
    city: Optional[str] = None
    postal_code: Optional[str] = None
    country: Optional[str] = None
    created_at: datetime
    updated_at: datetime


class BshTechnicianOut(BaseModel):
    id: int
    databricks_user_id: str
    email: str
    first_name: str
    last_name: str
    phone: Optional[str] = None
    specialization: Optional[str] = None
    certification_level: Optional[str] = None
    created_at: datetime
    updated_at: datetime


class BshDeviceOut(BaseModel):
    id: int
    model_number: str
    brand: str
    category: DeviceCategory
    name: str
    description: Optional[str] = None
    specifications: Optional[dict] = None
    image_url: Optional[str] = None
    created_at: datetime


class BshCustomerDeviceIn(BaseModel):
    device_id: int
    serial_number: str
    purchase_date: Optional[date] = None
    warranty_expiry_date: Optional[date] = None
    batch_number: Optional[str] = None


class BshCustomerDeviceOut(BaseModel):
    id: int
    customer_id: int
    device_id: int
    serial_number: str
    purchase_date: Optional[date] = None
    warranty_expiry_date: Optional[date] = None
    batch_number: Optional[str] = None
    registered_at: datetime
    device: Optional[BshDeviceOut] = None


class BshTicketIn(BaseModel):
    customer_device_id: int
    title: str
    description: str
    priority: int = 3


class BshTicketUpdate(BaseModel):
    status: Optional[BshTicketStatus] = None
    priority: Optional[int] = None
    technician_id: Optional[int] = None
    issue_summary: Optional[str] = None
    troubleshooting_attempted: Optional[str] = None
    tracking_number: Optional[str] = None


class BshTicketNoteIn(BaseModel):
    content: str
    is_internal: bool = False


class BshTicketNoteOut(BaseModel):
    id: int
    ticket_id: int
    content: str
    author_role: UserRole
    author_id: Optional[int] = None
    is_internal: bool
    created_at: datetime


class BshTicketOut(BaseModel):
    id: int
    customer_id: int
    customer_device_id: int
    technician_id: Optional[int] = None
    title: str
    description: str
    status: BshTicketStatus
    priority: int
    issue_summary: Optional[str] = None
    troubleshooting_attempted: Optional[str] = None
    shipping_label_url: Optional[str] = None
    tracking_number: Optional[str] = None
    created_at: datetime
    updated_at: datetime
    assigned_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    customer_device: Optional[BshCustomerDeviceOut] = None
    notes: Optional[list[BshTicketNoteOut]] = None


class BshChatMessageIn(BaseModel):
    message: str
    session_type: str = "troubleshooting"


class BshChatMessageOut(BaseModel):
    id: int
    session_id: int
    role: BshChatRole
    content: str
    sources: Optional[list[dict]] = None
    tokens_used: Optional[int] = None
    created_at: datetime


class BshChatHistoryOut(BaseModel):
    session_id: int
    ticket_id: int
    session_type: str
    started_at: datetime
    ended_at: Optional[datetime] = None
    messages: list[BshChatMessageOut]


class BshKnowledgeArticleOut(BaseModel):
    id: int
    device_id: Optional[int] = None
    title: str
    content: str
    category: DeviceCategory
    issue_type: Optional[str] = None
    tags: Optional[list[str]] = None
    view_count: int
    helpful_count: int
    created_at: datetime
    updated_at: datetime


class BshDocumentOut(BaseModel):
    id: int
    device_id: int
    title: str
    document_type: str
    content: Optional[str] = None
    file_url: Optional[str] = None
    language: str
    version: Optional[str] = None
    created_at: datetime
    updated_at: datetime
