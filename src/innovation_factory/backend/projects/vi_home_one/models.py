from pydantic import BaseModel
from sqlmodel import SQLModel, Field, Relationship
from typing import Optional, List
from datetime import datetime, date
from enum import Enum


# ============================================================================
# Enums
# ============================================================================

class DeviceType(str, Enum):
    heat_pump = "heat_pump"
    pv_system = "pv_system"
    battery = "battery"
    ev = "ev"
    grid_meter = "grid_meter"


class OptimizationMode(str, Enum):
    energy_saver = "energy_saver"
    cost_saver = "cost_saver"


class VhTicketStatus(str, Enum):
    new = "new"
    in_progress = "in_progress"
    resolved = "resolved"
    escalated = "escalated"


class ConsumptionCategory(str, Enum):
    household_appliances = "household_appliances"
    climate_control = "climate_control"
    ev_charging = "ev_charging"
    garden = "garden"
    other = "other"


class AlertSeverity(str, Enum):
    low = "low"
    medium = "medium"
    high = "high"
    critical = "critical"


class VhChatRole(str, Enum):
    user = "user"
    assistant = "assistant"
    system = "system"


# ============================================================================
# Database Models (all with vh_ prefix)
# ============================================================================

class VhNeighborhood(SQLModel, table=True):
    __tablename__ = "vh_neighborhoods"

    id: Optional[int] = Field(default=None, primary_key=True)
    project_id: Optional[int] = Field(default=None, foreign_key="if_projects.id", index=True)
    name: str
    location: str
    total_households: int
    created_at: datetime = Field(default_factory=datetime.utcnow)

    # Relationships
    households: List["VhHousehold"] = Relationship(back_populates="neighborhood")


class VhHousehold(SQLModel, table=True):
    __tablename__ = "vh_households"

    id: Optional[int] = Field(default=None, primary_key=True)
    project_id: Optional[int] = Field(default=None, foreign_key="if_projects.id", index=True)
    neighborhood_id: int = Field(foreign_key="vh_neighborhoods.id", index=True)
    owner_name: str
    address: str
    optimization_mode: OptimizationMode = Field(default=OptimizationMode.energy_saver)
    has_pv: bool = Field(default=False)
    has_battery: bool = Field(default=False)
    has_ev: bool = Field(default=False)
    has_heat_pump: bool = Field(default=False)
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)

    # Relationships
    neighborhood: VhNeighborhood = Relationship(back_populates="households")
    devices: List["VhEnergyDevice"] = Relationship(back_populates="household")
    readings: List["VhEnergyReading"] = Relationship(back_populates="household")
    tickets: List["VhTicket"] = Relationship(back_populates="household")


class VhEnergyDevice(SQLModel, table=True):
    __tablename__ = "vh_energy_devices"

    id: Optional[int] = Field(default=None, primary_key=True)
    project_id: Optional[int] = Field(default=None, foreign_key="if_projects.id", index=True)
    household_id: int = Field(foreign_key="vh_households.id", index=True)
    device_type: DeviceType
    brand: str
    model: str
    capacity_kw: Optional[float] = None
    installation_date: date
    last_maintenance_date: Optional[date] = None
    next_maintenance_date: Optional[date] = None
    serial_number: Optional[str] = None
    specifications: Optional[str] = None  # JSON string
    created_at: datetime = Field(default_factory=datetime.utcnow)

    # Relationships
    household: VhHousehold = Relationship(back_populates="devices")
    maintenance_alerts: List["VhMaintenanceAlert"] = Relationship(back_populates="device")


class VhEnergyReading(SQLModel, table=True):
    __tablename__ = "vh_energy_readings"

    id: Optional[int] = Field(default=None, primary_key=True)
    project_id: Optional[int] = Field(default=None, foreign_key="if_projects.id", index=True)
    household_id: int = Field(foreign_key="vh_households.id", index=True)
    timestamp: datetime = Field(index=True)

    # Generation
    pv_generation_kwh: float = Field(default=0.0)

    # Battery
    battery_charge_kwh: float = Field(default=0.0)
    battery_discharge_kwh: float = Field(default=0.0)
    battery_level_kwh: float = Field(default=0.0)

    # Grid
    grid_import_kwh: float = Field(default=0.0)
    grid_export_kwh: float = Field(default=0.0)

    # Consumption
    ev_consumption_kwh: float = Field(default=0.0)
    heat_pump_consumption_kwh: float = Field(default=0.0)
    household_consumption_kwh: float = Field(default=0.0)
    total_consumption_kwh: float = Field(default=0.0)

    # Relationships
    household: VhHousehold = Relationship(back_populates="readings")
    consumption_breakdown: List["VhConsumptionBreakdown"] = Relationship(back_populates="reading")


class VhConsumptionBreakdown(SQLModel, table=True):
    __tablename__ = "vh_consumption_breakdown"

    id: Optional[int] = Field(default=None, primary_key=True)
    project_id: Optional[int] = Field(default=None, foreign_key="if_projects.id", index=True)
    reading_id: int = Field(foreign_key="vh_energy_readings.id", index=True)
    category: ConsumptionCategory
    value_kwh: float

    # Relationships
    reading: VhEnergyReading = Relationship(back_populates="consumption_breakdown")


class VhEnergyProvider(SQLModel, table=True):
    __tablename__ = "vh_energy_providers"

    id: Optional[int] = Field(default=None, primary_key=True)
    project_id: Optional[int] = Field(default=None, foreign_key="if_projects.id", index=True)
    name: str
    base_rate_eur: float
    kwh_rate_eur: float
    night_rate_eur: Optional[float] = None
    feed_in_rate_eur: float
    night_start_hour: int = Field(default=22)
    night_end_hour: int = Field(default=6)
    created_at: datetime = Field(default_factory=datetime.utcnow)


class VhMaintenanceAlert(SQLModel, table=True):
    __tablename__ = "vh_maintenance_alerts"

    id: Optional[int] = Field(default=None, primary_key=True)
    project_id: Optional[int] = Field(default=None, foreign_key="if_projects.id", index=True)
    device_id: int = Field(foreign_key="vh_energy_devices.id", index=True)
    alert_type: str
    severity: AlertSeverity
    message: str
    predicted_date: Optional[date] = None
    is_acknowledged: bool = Field(default=False)
    created_at: datetime = Field(default_factory=datetime.utcnow, index=True)
    acknowledged_at: Optional[datetime] = None

    # Relationships
    device: VhEnergyDevice = Relationship(back_populates="maintenance_alerts")


class VhTicket(SQLModel, table=True):
    __tablename__ = "vh_tickets"

    id: Optional[int] = Field(default=None, primary_key=True)
    project_id: Optional[int] = Field(default=None, foreign_key="if_projects.id", index=True)
    household_id: int = Field(foreign_key="vh_households.id", index=True)
    device_id: Optional[int] = Field(default=None, foreign_key="vh_energy_devices.id", index=True)

    title: str
    description: str
    status: VhTicketStatus = Field(default=VhTicketStatus.new, index=True)
    priority: Optional[str] = None

    issue_summary: Optional[str] = None
    resolution_notes: Optional[str] = None

    created_at: datetime = Field(default_factory=datetime.utcnow, index=True)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
    resolved_at: Optional[datetime] = None

    # Relationships
    household: VhHousehold = Relationship(back_populates="tickets")
    media: List["VhTicketMedia"] = Relationship(back_populates="ticket")
    chat_sessions: List["VhChatSession"] = Relationship(back_populates="ticket")


class VhTicketMedia(SQLModel, table=True):
    __tablename__ = "vh_ticket_media"

    id: Optional[int] = Field(default=None, primary_key=True)
    project_id: Optional[int] = Field(default=None, foreign_key="if_projects.id", index=True)
    ticket_id: int = Field(foreign_key="vh_tickets.id", index=True)

    media_type: str
    file_url: str
    file_name: str
    file_size: Optional[int] = None
    mime_type: Optional[str] = None
    uploaded_at: datetime = Field(default_factory=datetime.utcnow)

    # Relationships
    ticket: VhTicket = Relationship(back_populates="media")


class VhChatSession(SQLModel, table=True):
    __tablename__ = "vh_chat_sessions"

    id: Optional[int] = Field(default=None, primary_key=True)
    project_id: Optional[int] = Field(default=None, foreign_key="if_projects.id", index=True)
    ticket_id: int = Field(foreign_key="vh_tickets.id", index=True)

    session_type: str = Field(default="support")
    started_at: datetime = Field(default_factory=datetime.utcnow)
    ended_at: Optional[datetime] = None

    # Relationships
    ticket: VhTicket = Relationship(back_populates="chat_sessions")
    messages: List["VhChatMessage"] = Relationship(back_populates="session")


class VhChatMessage(SQLModel, table=True):
    __tablename__ = "vh_chat_messages"

    id: Optional[int] = Field(default=None, primary_key=True)
    project_id: Optional[int] = Field(default=None, foreign_key="if_projects.id", index=True)
    session_id: int = Field(foreign_key="vh_chat_sessions.id", index=True)

    role: VhChatRole
    content: str
    sources: Optional[str] = None
    tokens_used: Optional[int] = None
    created_at: datetime = Field(default_factory=datetime.utcnow, index=True)

    # Relationships
    session: VhChatSession = Relationship(back_populates="messages")


class VhKnowledgeArticle(SQLModel, table=True):
    __tablename__ = "vh_knowledge_articles"

    id: Optional[int] = Field(default=None, primary_key=True)
    project_id: Optional[int] = Field(default=None, foreign_key="if_projects.id", index=True)
    device_type: Optional[DeviceType] = Field(default=None, index=True)

    title: str
    content: str
    category: str
    tags: Optional[str] = None
    view_count: int = Field(default=0)
    helpful_count: int = Field(default=0)

    embedding: Optional[str] = None

    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)


# ============================================================================
# Pydantic Models (Input/Output)
# ============================================================================

# Neighborhood Models
class VhNeighborhoodOut(BaseModel):
    id: int
    name: str
    location: str
    total_households: int
    created_at: datetime


class VhHouseholdSummaryOut(BaseModel):
    id: int
    owner_name: str
    address: str
    optimization_mode: OptimizationMode
    current_consumption_kw: float
    current_generation_kw: float
    battery_level_percent: float


class VhNeighborhoodSummaryOut(BaseModel):
    id: int
    name: str
    location: str
    total_households: int
    total_consumption_kwh: float
    total_generation_kwh: float
    total_storage_capacity_kwh: float
    households: List[VhHouseholdSummaryOut]


# Household Models
class VhHouseholdIn(BaseModel):
    owner_name: str
    address: str
    optimization_mode: OptimizationMode = OptimizationMode.energy_saver


class VhHouseholdOut(BaseModel):
    id: int
    neighborhood_id: int
    owner_name: str
    address: str
    optimization_mode: OptimizationMode
    has_pv: bool
    has_battery: bool
    has_ev: bool
    has_heat_pump: bool
    created_at: datetime
    updated_at: datetime


class VhEnergyReadingOut(BaseModel):
    id: int
    household_id: int
    timestamp: datetime
    pv_generation_kwh: float
    battery_charge_kwh: float
    battery_discharge_kwh: float
    battery_level_kwh: float
    grid_import_kwh: float
    grid_export_kwh: float
    ev_consumption_kwh: float
    heat_pump_consumption_kwh: float
    household_consumption_kwh: float
    total_consumption_kwh: float


class VhConsumptionBreakdownOut(BaseModel):
    category: ConsumptionCategory
    value_kwh: float
    percentage: float


class VhEnergySourcesOut(BaseModel):
    pv_generation_kw: float
    battery_discharge_kw: float
    grid_import_kw: float
    total_available_kw: float


class VhHouseholdCockpitOut(BaseModel):
    household: VhHouseholdOut
    current_consumption_kw: float
    consumption_breakdown: List[VhConsumptionBreakdownOut]
    energy_sources: VhEnergySourcesOut
    recent_readings: List[VhEnergyReadingOut]
    cost_today_eur: float
    cost_this_month_eur: float
    devices: List["VhEnergyDeviceOut"]


# Energy Device Models
class VhEnergyDeviceIn(BaseModel):
    device_type: DeviceType
    brand: str
    model: str
    capacity_kw: Optional[float] = None
    installation_date: date
    serial_number: Optional[str] = None
    specifications: Optional[str] = None


class VhEnergyDeviceOut(BaseModel):
    id: int
    household_id: int
    device_type: DeviceType
    brand: str
    model: str
    capacity_kw: Optional[float] = None
    installation_date: date
    last_maintenance_date: Optional[date] = None
    next_maintenance_date: Optional[date] = None
    serial_number: Optional[str] = None
    specifications: Optional[str] = None


# Optimization Models
class VhOptimizationSuggestionOut(BaseModel):
    id: str
    category: str
    title: str
    description: str
    potential_savings_kwh: Optional[float] = None
    potential_savings_eur: Optional[float] = None


class VhOptimizationModeUpdate(BaseModel):
    optimization_mode: OptimizationMode


# Provider Models
class VhEnergyProviderOut(BaseModel):
    id: int
    name: str
    base_rate_eur: float
    kwh_rate_eur: float
    night_rate_eur: Optional[float] = None
    feed_in_rate_eur: float


class VhAlternativeProviderOut(BaseModel):
    provider: VhEnergyProviderOut
    estimated_monthly_cost_eur: float
    potential_savings_eur: float
    potential_savings_percent: float


class VhProviderComparisonOut(BaseModel):
    current_provider: VhEnergyProviderOut
    current_monthly_cost_eur: float
    alternative_providers: List[VhAlternativeProviderOut]


# Maintenance Models
class VhMaintenanceAlertOut(BaseModel):
    id: int
    device_id: int
    device_type: DeviceType
    device_model: str
    alert_type: str
    severity: AlertSeverity
    message: str
    predicted_date: Optional[date] = None
    is_acknowledged: bool
    created_at: datetime


class VhMaintenanceAlertAcknowledge(BaseModel):
    is_acknowledged: bool


# Ticket Models
class VhTicketIn(BaseModel):
    device_id: Optional[int] = None
    title: str
    description: str
    priority: Optional[str] = None


class VhTicketUpdate(BaseModel):
    status: Optional[VhTicketStatus] = None
    resolution_notes: Optional[str] = None


class VhTicketOut(BaseModel):
    id: int
    household_id: int
    device_id: Optional[int] = None
    title: str
    description: str
    status: VhTicketStatus
    priority: Optional[str] = None
    issue_summary: Optional[str] = None
    resolution_notes: Optional[str] = None
    created_at: datetime
    updated_at: datetime
    resolved_at: Optional[datetime] = None


# Chat Models
class VhChatMessageIn(BaseModel):
    content: str


class VhChatMessageOut(BaseModel):
    id: int
    role: VhChatRole
    content: str
    sources: Optional[str] = None
    created_at: datetime


class VhChatHistoryOut(BaseModel):
    session_id: int
    messages: List[VhChatMessageOut]


# Knowledge Base Models
class VhKnowledgeArticleOut(BaseModel):
    id: int
    title: str
    content: str
    category: str
    tags: Optional[str] = None
    helpful_count: int
