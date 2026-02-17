"""SQLModel database models and Pydantic I/O models for the ASM Cockpit project.

All table names use the ``mac_`` prefix (mol-asm-cockpit).
"""

from datetime import date, datetime, timezone
from enum import Enum
from typing import Optional

from pydantic import BaseModel
from sqlmodel import Column, Field, JSON, SQLModel, Text


# ============================================================================
# Enums
# ============================================================================


class StationType(str, Enum):
    highway = "highway"
    urban = "urban"
    suburban = "suburban"


class FuelType(str, Enum):
    diesel = "diesel"
    premium_diesel = "premium_diesel"
    regular_95 = "regular_95"
    premium_98 = "premium_98"
    lpg = "lpg"


class NonfuelCategory(str, Enum):
    coffee = "coffee"
    hot_food = "hot_food"
    cold_food = "cold_food"
    bakery = "bakery"
    beverages = "beverages"
    tobacco = "tobacco"
    car_care = "car_care"
    convenience = "convenience"


class ShiftType(str, Enum):
    morning = "morning"
    afternoon = "afternoon"
    night = "night"


class ProductCategory(str, Enum):
    fuel = "fuel"
    coffee = "coffee"
    hot_food = "hot_food"
    cold_food = "cold_food"
    bakery = "bakery"
    beverages = "beverages"
    tobacco = "tobacco"
    car_care = "car_care"
    convenience = "convenience"


class MacAlertSeverity(str, Enum):
    low = "low"
    medium = "medium"
    high = "high"
    critical = "critical"


class MacAlertStatus(str, Enum):
    active = "active"
    acknowledged = "acknowledged"
    resolved = "resolved"
    dismissed = "dismissed"


class MacIssueStatus(str, Enum):
    open = "open"
    in_progress = "in_progress"
    resolved = "resolved"
    closed = "closed"


class MacIssueCategory(str, Enum):
    equipment = "equipment"
    supply_chain = "supply_chain"
    quality = "quality"
    customer_complaint = "customer_complaint"
    staffing = "staffing"
    safety = "safety"
    it_system = "it_system"


class LoyaltyTier(str, Enum):
    bronze = "bronze"
    silver = "silver"
    gold = "gold"
    platinum = "platinum"


class MacChatRole(str, Enum):
    user = "user"
    assistant = "assistant"
    system = "system"


# ============================================================================
# SQLModel Database Models (all table names prefixed with mac_)
# ============================================================================


class MacRegion(SQLModel, table=True):
    __tablename__ = "mac_regions"

    id: Optional[int] = Field(default=None, primary_key=True)
    name: str = Field(unique=True, index=True)
    country: str
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))


class MacStation(SQLModel, table=True):
    __tablename__ = "mac_stations"

    id: Optional[int] = Field(default=None, primary_key=True)
    station_code: str = Field(unique=True, index=True)
    name: str
    city: str
    region_id: int = Field(foreign_key="mac_regions.id", index=True)
    latitude: float
    longitude: float
    station_type: StationType
    has_fresh_corner: bool = Field(default=False)
    has_ev_charging: bool = Field(default=False)
    num_pumps: int = Field(default=6)
    shop_area_sqm: float = Field(default=80.0)
    opened_date: Optional[date] = None
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))


class MacFuelSale(SQLModel, table=True):
    __tablename__ = "mac_fuel_sales"

    id: Optional[int] = Field(default=None, primary_key=True)
    station_id: int = Field(foreign_key="mac_stations.id", index=True)
    sale_date: date = Field(index=True)
    fuel_type: FuelType
    volume_liters: float
    revenue: float
    unit_price: float
    margin: float


class MacNonfuelSale(SQLModel, table=True):
    __tablename__ = "mac_nonfuel_sales"

    id: Optional[int] = Field(default=None, primary_key=True)
    station_id: int = Field(foreign_key="mac_stations.id", index=True)
    sale_date: date = Field(index=True)
    category: NonfuelCategory
    quantity: int
    revenue: float
    margin: float


class MacLoyaltyMetric(SQLModel, table=True):
    __tablename__ = "mac_loyalty_metrics"

    id: Optional[int] = Field(default=None, primary_key=True)
    station_id: int = Field(foreign_key="mac_stations.id", index=True)
    month: date = Field(index=True)
    active_members: int
    new_signups: int
    points_redeemed: int
    loyalty_revenue_share: float


class MacWorkforceShift(SQLModel, table=True):
    __tablename__ = "mac_workforce_shifts"

    id: Optional[int] = Field(default=None, primary_key=True)
    station_id: int = Field(foreign_key="mac_stations.id", index=True)
    shift_date: date = Field(index=True)
    shift_type: ShiftType
    planned_headcount: int
    actual_headcount: int
    overtime_hours: float


class MacInventory(SQLModel, table=True):
    __tablename__ = "mac_inventory"

    id: Optional[int] = Field(default=None, primary_key=True)
    station_id: int = Field(foreign_key="mac_stations.id", index=True)
    record_date: date = Field(index=True)
    product_category: ProductCategory
    stock_level: int
    reorder_point: int
    spoilage_count: int
    stock_out_events: int
    delivery_scheduled: bool = Field(default=False)


class MacCompetitorPrice(SQLModel, table=True):
    __tablename__ = "mac_competitor_prices"

    id: Optional[int] = Field(default=None, primary_key=True)
    station_id: int = Field(foreign_key="mac_stations.id", index=True)
    price_date: date = Field(index=True)
    competitor_name: str
    fuel_type: FuelType
    price_per_liter: float


class MacPriceHistory(SQLModel, table=True):
    __tablename__ = "mac_price_history"

    id: Optional[int] = Field(default=None, primary_key=True)
    station_id: int = Field(foreign_key="mac_stations.id", index=True)
    price_date: date = Field(index=True)
    fuel_type: FuelType
    price_per_liter: float
    cost_per_liter: float


class MacAnomalyAlert(SQLModel, table=True):
    __tablename__ = "mac_anomaly_alerts"

    id: Optional[int] = Field(default=None, primary_key=True)
    station_id: int = Field(foreign_key="mac_stations.id", index=True)
    metric_type: str
    severity: MacAlertSeverity
    title: str
    description: str = Field(sa_column=Column(Text))
    suggested_action: str = Field(sa_column=Column(Text))
    status: MacAlertStatus = Field(default=MacAlertStatus.active)
    detected_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    resolved_at: Optional[datetime] = None


class MacIssue(SQLModel, table=True):
    __tablename__ = "mac_issues"

    id: Optional[int] = Field(default=None, primary_key=True)
    station_id: int = Field(foreign_key="mac_stations.id", index=True)
    category: MacIssueCategory
    title: str
    description: str = Field(sa_column=Column(Text))
    resolution: Optional[str] = Field(default=None, sa_column=Column(Text, nullable=True))
    status: MacIssueStatus = Field(default=MacIssueStatus.open)
    priority: int = Field(default=3)
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    resolved_at: Optional[datetime] = None


class MacCustomerProfile(SQLModel, table=True):
    __tablename__ = "mac_customer_profiles"

    id: Optional[int] = Field(default=None, primary_key=True)
    company_name: str
    contact_name: str
    contact_email: str = Field(unique=True, index=True)
    phone: Optional[str] = None
    fleet_size: int = Field(default=0)
    loyalty_tier: LoyaltyTier = Field(default=LoyaltyTier.bronze)
    contract_type: Optional[str] = None
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))


class MacCustomerContract(SQLModel, table=True):
    __tablename__ = "mac_customer_contracts"

    id: Optional[int] = Field(default=None, primary_key=True)
    customer_id: int = Field(foreign_key="mac_customer_profiles.id", index=True)
    contract_type: str
    monthly_volume_commitment: float
    discount_pct: float
    start_date: date
    end_date: Optional[date] = None
    notes: Optional[str] = Field(default=None, sa_column=Column(Text, nullable=True))
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))


class MacChatSession(SQLModel, table=True):
    __tablename__ = "mac_chat_sessions"

    id: Optional[int] = Field(default=None, primary_key=True)
    session_type: str = Field(default="issue_resolution")
    started_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    ended_at: Optional[datetime] = None


class MacChatMessage(SQLModel, table=True):
    __tablename__ = "mac_chat_messages"

    id: Optional[int] = Field(default=None, primary_key=True)
    session_id: int = Field(foreign_key="mac_chat_sessions.id", index=True)
    role: MacChatRole
    content: str = Field(sa_column=Column(Text))
    sources: Optional[list[dict]] = Field(default=None, sa_column=Column(JSON))
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))


# ============================================================================
# Pydantic Input/Output Models
# ============================================================================


class MacRegionOut(BaseModel):
    id: int
    name: str
    country: str


class MacStationOut(BaseModel):
    id: int
    station_code: str
    name: str
    city: str
    region_id: int
    latitude: float
    longitude: float
    station_type: StationType
    has_fresh_corner: bool
    has_ev_charging: bool
    num_pumps: int
    shop_area_sqm: float
    opened_date: Optional[date] = None


class MacStationKPI(BaseModel):
    station_id: int
    station_code: str
    station_name: str
    city: str
    region_name: str
    total_fuel_volume: float
    total_fuel_revenue: float
    total_fuel_margin: float
    total_nonfuel_revenue: float
    total_nonfuel_margin: float
    active_alerts: int


class MacFuelSaleOut(BaseModel):
    id: int
    station_id: int
    sale_date: date
    fuel_type: FuelType
    volume_liters: float
    revenue: float
    unit_price: float
    margin: float


class MacNonfuelSaleOut(BaseModel):
    id: int
    station_id: int
    sale_date: date
    category: NonfuelCategory
    quantity: int
    revenue: float
    margin: float


class MacLoyaltyMetricOut(BaseModel):
    id: int
    station_id: int
    month: date
    active_members: int
    new_signups: int
    points_redeemed: int
    loyalty_revenue_share: float


class MacWorkforceShiftOut(BaseModel):
    id: int
    station_id: int
    shift_date: date
    shift_type: ShiftType
    planned_headcount: int
    actual_headcount: int
    overtime_hours: float


class MacInventoryOut(BaseModel):
    id: int
    station_id: int
    record_date: date
    product_category: ProductCategory
    stock_level: int
    reorder_point: int
    spoilage_count: int
    stock_out_events: int
    delivery_scheduled: bool


class MacCompetitorPriceOut(BaseModel):
    id: int
    station_id: int
    price_date: date
    competitor_name: str
    fuel_type: FuelType
    price_per_liter: float


class MacPriceHistoryOut(BaseModel):
    id: int
    station_id: int
    price_date: date
    fuel_type: FuelType
    price_per_liter: float
    cost_per_liter: float


class MacAnomalyAlertOut(BaseModel):
    id: int
    station_id: int
    metric_type: str
    severity: MacAlertSeverity
    title: str
    description: str
    suggested_action: str
    status: MacAlertStatus
    detected_at: datetime
    resolved_at: Optional[datetime] = None


class MacAnomalyAlertUpdate(BaseModel):
    status: Optional[MacAlertStatus] = None
    resolved_at: Optional[datetime] = None


class MacIssueOut(BaseModel):
    id: int
    station_id: int
    category: MacIssueCategory
    title: str
    description: str
    resolution: Optional[str] = None
    status: MacIssueStatus
    priority: int
    created_at: datetime
    resolved_at: Optional[datetime] = None


class MacCustomerProfileOut(BaseModel):
    id: int
    company_name: str
    contact_name: str
    contact_email: str
    phone: Optional[str] = None
    fleet_size: int
    loyalty_tier: LoyaltyTier
    contract_type: Optional[str] = None


class MacCustomerContractOut(BaseModel):
    id: int
    customer_id: int
    contract_type: str
    monthly_volume_commitment: float
    discount_pct: float
    start_date: date
    end_date: Optional[date] = None
    notes: Optional[str] = None


class MacChatMessageIn(BaseModel):
    message: str
    session_type: str = "issue_resolution"


class MacChatMessageOut(BaseModel):
    id: int
    session_id: int
    role: MacChatRole
    content: str
    sources: Optional[list[dict]] = None
    created_at: datetime


class MacChatHistoryOut(BaseModel):
    session_id: int
    session_type: str
    started_at: datetime
    ended_at: Optional[datetime] = None
    messages: list[MacChatMessageOut]
