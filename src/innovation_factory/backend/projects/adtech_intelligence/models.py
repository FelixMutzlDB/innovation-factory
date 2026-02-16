"""Data models for the AdTech Intelligence project.

Covers: advertisers, campaigns, ad inventory (online + OOH/DOOH across Germany),
placements, performance metrics, anomaly detection, issues/tickets,
customer contracts (CRM), and chat sessions for the issue-resolution agent.
"""

from datetime import date, datetime
from enum import Enum
from typing import Optional

from pydantic import BaseModel
from sqlmodel import Column, Field, JSON, Relationship, SQLModel, Text


# ============================================================================
# Enums
# ============================================================================


class CampaignType(str, Enum):
    online = "online"
    outdoor = "outdoor"
    crossmedia = "crossmedia"


class CampaignStatus(str, Enum):
    draft = "draft"
    active = "active"
    paused = "paused"
    completed = "completed"
    cancelled = "cancelled"


class InventoryType(str, Enum):
    display_banner = "display_banner"
    video = "video"
    native = "native"
    high_impact = "high_impact"
    dooh_screen = "dooh_screen"
    billboard = "billboard"
    transit_poster = "transit_poster"
    city_light = "city_light"
    mega_poster = "mega_poster"


class LocationType(str, Enum):
    online = "online"
    train_station = "train_station"
    mall = "mall"
    pedestrian_zone = "pedestrian_zone"
    highway = "highway"
    bus_stop = "bus_stop"
    airport = "airport"
    subway = "subway"


class InventoryStatus(str, Enum):
    available = "available"
    booked = "booked"
    maintenance = "maintenance"
    inactive = "inactive"


class PlacementStatus(str, Enum):
    scheduled = "scheduled"
    active = "active"
    paused = "paused"
    completed = "completed"
    cancelled = "cancelled"


class AnomalyType(str, Enum):
    performance_drop = "performance_drop"
    budget_overrun = "budget_overrun"
    ctr_anomaly = "ctr_anomaly"
    impression_spike = "impression_spike"
    viewability_drop = "viewability_drop"
    conversion_decline = "conversion_decline"
    inventory_underutilization = "inventory_underutilization"


class AnomalySeverity(str, Enum):
    low = "low"
    medium = "medium"
    high = "high"
    critical = "critical"


class AnomalyStatus(str, Enum):
    new = "new"
    acknowledged = "acknowledged"
    investigating = "investigating"
    resolved = "resolved"
    dismissed = "dismissed"


class RuleConditionType(str, Enum):
    threshold = "threshold"
    trend = "trend"
    deviation = "deviation"


class IssueCategory(str, Enum):
    delivery = "delivery"
    targeting = "targeting"
    creative = "creative"
    billing = "billing"
    technical = "technical"
    reporting = "reporting"
    inventory = "inventory"


class IssueStatus(str, Enum):
    open = "open"
    in_progress = "in_progress"
    waiting_on_customer = "waiting_on_customer"
    resolved = "resolved"
    closed = "closed"


class IssuePriority(str, Enum):
    low = "low"
    medium = "medium"
    high = "high"
    urgent = "urgent"


class ContractStatus(str, Enum):
    active = "active"
    expired = "expired"
    pending = "pending"
    terminated = "terminated"


class AtChatRole(str, Enum):
    user = "user"
    assistant = "assistant"
    system = "system"


# ============================================================================
# SQLModel Database Models (all table names prefixed with at_)
# ============================================================================


class AtAdvertiser(SQLModel, table=True):
    """Companies / brands purchasing ad space."""

    __tablename__ = "at_advertisers"

    id: Optional[int] = Field(default=None, primary_key=True)
    name: str = Field(index=True)
    industry: str
    contact_name: str
    contact_email: str = Field(index=True)
    phone: Optional[str] = None
    website: Optional[str] = None
    budget_tier: str = Field(default="standard")  # standard / premium / enterprise
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)

    campaigns: list["AtCampaign"] = Relationship(back_populates="advertiser")
    contracts: list["AtCustomerContract"] = Relationship(back_populates="advertiser")
    issues: list["AtIssue"] = Relationship(back_populates="advertiser")


class AtCampaign(SQLModel, table=True):
    """Advertising campaigns spanning online and/or outdoor channels."""

    __tablename__ = "at_campaigns"

    id: Optional[int] = Field(default=None, primary_key=True)
    advertiser_id: int = Field(foreign_key="at_advertisers.id", index=True)
    name: str
    description: Optional[str] = Field(default=None, sa_column=Column(Text, nullable=True))
    campaign_type: CampaignType
    status: CampaignStatus = Field(default=CampaignStatus.draft)
    budget: float
    spent: float = Field(default=0.0)
    start_date: date
    end_date: date
    target_audience: Optional[str] = None
    target_regions: Optional[list] = Field(default=None, sa_column=Column(JSON))
    kpi_targets: Optional[dict] = Field(default=None, sa_column=Column(JSON))
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)

    advertiser: Optional[AtAdvertiser] = Relationship(back_populates="campaigns")
    placements: list["AtPlacement"] = Relationship(back_populates="campaign")
    anomalies: list["AtAnomaly"] = Relationship(back_populates="campaign")
    issues: list["AtIssue"] = Relationship(back_populates="campaign")


class AtAdInventory(SQLModel, table=True):
    """Available ad spaces — both online formats and physical OOH locations."""

    __tablename__ = "at_ad_inventory"

    id: Optional[int] = Field(default=None, primary_key=True)
    name: str
    inventory_type: InventoryType
    location_type: LocationType
    city: Optional[str] = None
    region: Optional[str] = None
    latitude: Optional[float] = None
    longitude: Optional[float] = None
    format_spec: Optional[dict] = Field(default=None, sa_column=Column(JSON))
    daily_impressions_est: int = Field(default=0)
    cpm_rate: float = Field(default=0.0)
    status: InventoryStatus = Field(default=InventoryStatus.available)
    media_owner: Optional[str] = None
    created_at: datetime = Field(default_factory=datetime.utcnow)

    placements: list["AtPlacement"] = Relationship(back_populates="inventory")


class AtPlacement(SQLModel, table=True):
    """Links a campaign to a specific inventory slot for a date range."""

    __tablename__ = "at_placements"

    id: Optional[int] = Field(default=None, primary_key=True)
    campaign_id: int = Field(foreign_key="at_campaigns.id", index=True)
    inventory_id: int = Field(foreign_key="at_ad_inventory.id", index=True)
    start_date: date
    end_date: date
    daily_budget: float = Field(default=0.0)
    status: PlacementStatus = Field(default=PlacementStatus.scheduled)
    created_at: datetime = Field(default_factory=datetime.utcnow)

    campaign: Optional[AtCampaign] = Relationship(back_populates="placements")
    inventory: Optional[AtAdInventory] = Relationship(back_populates="placements")
    metrics: list["AtPerformanceMetric"] = Relationship(back_populates="placement")
    anomalies: list["AtAnomaly"] = Relationship(back_populates="placement")


class AtPerformanceMetric(SQLModel, table=True):
    """Daily performance data per placement."""

    __tablename__ = "at_performance_metrics"

    id: Optional[int] = Field(default=None, primary_key=True)
    placement_id: int = Field(foreign_key="at_placements.id", index=True)
    metric_date: date = Field(index=True)
    impressions: int = Field(default=0)
    clicks: int = Field(default=0)
    ctr: float = Field(default=0.0)
    conversions: int = Field(default=0)
    spend: float = Field(default=0.0)
    viewability_rate: float = Field(default=0.0)
    created_at: datetime = Field(default_factory=datetime.utcnow)

    placement: Optional[AtPlacement] = Relationship(back_populates="metrics")


# -- Anomaly Detection --


class AtAnomalyRule(SQLModel, table=True):
    """Configuration for automatic anomaly detection."""

    __tablename__ = "at_anomaly_rules"

    id: Optional[int] = Field(default=None, primary_key=True)
    name: str
    description: Optional[str] = Field(default=None, sa_column=Column(Text, nullable=True))
    metric_name: str
    condition_type: RuleConditionType
    threshold_value: float
    lookback_days: int = Field(default=7)
    enabled: bool = Field(default=True)
    created_at: datetime = Field(default_factory=datetime.utcnow)


class AtAnomaly(SQLModel, table=True):
    """Detected anomalies flagged by monitoring rules."""

    __tablename__ = "at_anomalies"

    id: Optional[int] = Field(default=None, primary_key=True)
    campaign_id: Optional[int] = Field(
        default=None, foreign_key="at_campaigns.id", index=True
    )
    placement_id: Optional[int] = Field(
        default=None, foreign_key="at_placements.id", index=True
    )
    rule_id: Optional[int] = Field(
        default=None, foreign_key="at_anomaly_rules.id", index=True
    )
    anomaly_type: AnomalyType
    severity: AnomalySeverity
    title: str
    description: str = Field(sa_column=Column(Text))
    detected_at: datetime = Field(default_factory=datetime.utcnow)
    status: AnomalyStatus = Field(default=AnomalyStatus.new)
    metric_name: str
    expected_value: float
    actual_value: float
    deviation_pct: float
    suggested_actions: Optional[list] = Field(default=None, sa_column=Column(JSON))
    resolved_at: Optional[datetime] = None
    resolved_by: Optional[str] = None

    campaign: Optional[AtCampaign] = Relationship(back_populates="anomalies")
    placement: Optional[AtPlacement] = Relationship(back_populates="anomalies")


# -- Issues / Support Tickets --


class AtIssue(SQLModel, table=True):
    """Support issues and tickets from advertisers / internal ops."""

    __tablename__ = "at_issues"

    id: Optional[int] = Field(default=None, primary_key=True)
    campaign_id: Optional[int] = Field(
        default=None, foreign_key="at_campaigns.id", index=True
    )
    advertiser_id: Optional[int] = Field(
        default=None, foreign_key="at_advertisers.id", index=True
    )
    title: str
    description: str = Field(sa_column=Column(Text))
    category: IssueCategory
    status: IssueStatus = Field(default=IssueStatus.open)
    priority: IssuePriority = Field(default=IssuePriority.medium)
    resolution: Optional[str] = Field(
        default=None, sa_column=Column(Text, nullable=True)
    )
    assigned_to: Optional[str] = None
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
    resolved_at: Optional[datetime] = None

    campaign: Optional[AtCampaign] = Relationship(back_populates="issues")
    advertiser: Optional[AtAdvertiser] = Relationship(back_populates="issues")


# -- CRM / Customer Contracts --


class AtCustomerContract(SQLModel, table=True):
    """Customer contracts and agreements from the CRM system."""

    __tablename__ = "at_customer_contracts"

    id: Optional[int] = Field(default=None, primary_key=True)
    advertiser_id: int = Field(foreign_key="at_advertisers.id", index=True)
    contract_number: str = Field(unique=True, index=True)
    contract_type: str  # annual / project / programmatic
    start_date: date
    end_date: date
    total_value: float
    status: ContractStatus = Field(default=ContractStatus.active)
    terms_summary: Optional[str] = Field(
        default=None, sa_column=Column(Text, nullable=True)
    )
    account_manager: Optional[str] = None
    created_at: datetime = Field(default_factory=datetime.utcnow)

    advertiser: Optional[AtAdvertiser] = Relationship(back_populates="contracts")


# -- Chat Sessions (Issue Resolution Agent) --


class AtChatSession(SQLModel, table=True):
    """Chat sessions for the issue-resolution agent."""

    __tablename__ = "at_chat_sessions"

    id: Optional[int] = Field(default=None, primary_key=True)
    user_id: Optional[str] = None
    session_type: str = Field(default="issue_resolution")
    started_at: datetime = Field(default_factory=datetime.utcnow)
    ended_at: Optional[datetime] = None

    messages: list["AtChatMessage"] = Relationship(back_populates="session")


class AtChatMessage(SQLModel, table=True):
    """Individual messages within a chat session."""

    __tablename__ = "at_chat_messages"

    id: Optional[int] = Field(default=None, primary_key=True)
    session_id: int = Field(foreign_key="at_chat_sessions.id", index=True)
    role: AtChatRole
    content: str = Field(sa_column=Column(Text))
    sources: Optional[list[dict]] = Field(default=None, sa_column=Column(JSON))
    tokens_used: Optional[int] = None
    created_at: datetime = Field(default_factory=datetime.utcnow)

    session: Optional[AtChatSession] = Relationship(back_populates="messages")


# ============================================================================
# Pydantic Input / Output Models
# ============================================================================


# -- Advertisers --


class AtAdvertiserOut(BaseModel):
    id: int
    name: str
    industry: str
    contact_name: str
    contact_email: str
    phone: Optional[str] = None
    website: Optional[str] = None
    budget_tier: str
    created_at: datetime
    updated_at: datetime


# -- Campaigns --


class AtCampaignIn(BaseModel):
    advertiser_id: int
    name: str
    description: Optional[str] = None
    campaign_type: CampaignType
    budget: float
    start_date: date
    end_date: date
    target_audience: Optional[str] = None
    target_regions: Optional[list] = None
    kpi_targets: Optional[dict] = None


class AtCampaignOut(BaseModel):
    id: int
    advertiser_id: int
    name: str
    description: Optional[str] = None
    campaign_type: CampaignType
    status: CampaignStatus
    budget: float
    spent: float
    start_date: date
    end_date: date
    target_audience: Optional[str] = None
    target_regions: Optional[list] = None
    kpi_targets: Optional[dict] = None
    created_at: datetime
    updated_at: datetime
    advertiser: Optional[AtAdvertiserOut] = None


class AtCampaignUpdate(BaseModel):
    status: Optional[CampaignStatus] = None
    budget: Optional[float] = None
    spent: Optional[float] = None
    target_audience: Optional[str] = None
    target_regions: Optional[list] = None
    kpi_targets: Optional[dict] = None


# -- Inventory --


class AtAdInventoryOut(BaseModel):
    id: int
    name: str
    inventory_type: InventoryType
    location_type: LocationType
    city: Optional[str] = None
    region: Optional[str] = None
    latitude: Optional[float] = None
    longitude: Optional[float] = None
    format_spec: Optional[dict] = None
    daily_impressions_est: int
    cpm_rate: float
    status: InventoryStatus
    media_owner: Optional[str] = None
    created_at: datetime


# -- Placements --


class AtPlacementIn(BaseModel):
    campaign_id: int
    inventory_id: int
    start_date: date
    end_date: date
    daily_budget: float = 0.0


class AtPlacementOut(BaseModel):
    id: int
    campaign_id: int
    inventory_id: int
    start_date: date
    end_date: date
    daily_budget: float
    status: PlacementStatus
    created_at: datetime
    inventory: Optional[AtAdInventoryOut] = None


# -- Performance Metrics --


class AtPerformanceMetricOut(BaseModel):
    id: int
    placement_id: int
    metric_date: date
    impressions: int
    clicks: int
    ctr: float
    conversions: int
    spend: float
    viewability_rate: float
    created_at: datetime


# -- Anomalies --


class AtAnomalyOut(BaseModel):
    id: int
    campaign_id: Optional[int] = None
    placement_id: Optional[int] = None
    rule_id: Optional[int] = None
    anomaly_type: AnomalyType
    severity: AnomalySeverity
    title: str
    description: str
    detected_at: datetime
    status: AnomalyStatus
    metric_name: str
    expected_value: float
    actual_value: float
    deviation_pct: float
    suggested_actions: Optional[list] = None
    resolved_at: Optional[datetime] = None
    resolved_by: Optional[str] = None


class AtAnomalyUpdate(BaseModel):
    status: Optional[AnomalyStatus] = None
    resolved_by: Optional[str] = None


class AtAnomalyRuleOut(BaseModel):
    id: int
    name: str
    description: Optional[str] = None
    metric_name: str
    condition_type: RuleConditionType
    threshold_value: float
    lookback_days: int
    enabled: bool
    created_at: datetime


# -- Issues --


class AtIssueIn(BaseModel):
    campaign_id: Optional[int] = None
    advertiser_id: Optional[int] = None
    title: str
    description: str
    category: IssueCategory
    priority: IssuePriority = IssuePriority.medium


class AtIssueOut(BaseModel):
    id: int
    campaign_id: Optional[int] = None
    advertiser_id: Optional[int] = None
    title: str
    description: str
    category: IssueCategory
    status: IssueStatus
    priority: IssuePriority
    resolution: Optional[str] = None
    assigned_to: Optional[str] = None
    created_at: datetime
    updated_at: datetime
    resolved_at: Optional[datetime] = None


class AtIssueUpdate(BaseModel):
    status: Optional[IssueStatus] = None
    priority: Optional[IssuePriority] = None
    resolution: Optional[str] = None
    assigned_to: Optional[str] = None


# -- Contracts --


class AtCustomerContractOut(BaseModel):
    id: int
    advertiser_id: int
    contract_number: str
    contract_type: str
    start_date: date
    end_date: date
    total_value: float
    status: ContractStatus
    terms_summary: Optional[str] = None
    account_manager: Optional[str] = None
    created_at: datetime


# -- Chat --


class AtChatMessageIn(BaseModel):
    message: str
    session_id: Optional[int] = None


class AtChatMessageOut(BaseModel):
    id: int
    session_id: int
    role: AtChatRole
    content: str
    sources: Optional[list[dict]] = None
    tokens_used: Optional[int] = None
    created_at: datetime


class AtChatHistoryOut(BaseModel):
    session_id: int
    session_type: str
    started_at: datetime
    ended_at: Optional[datetime] = None
    messages: list[AtChatMessageOut]


# -- Dashboard Summary --


class AtDashboardSummaryOut(BaseModel):
    total_campaigns: int
    active_campaigns: int
    total_inventory: int
    available_inventory: int
    total_spend: float
    total_impressions: int
    avg_ctr: float
    active_anomalies: int
    critical_anomalies: int
