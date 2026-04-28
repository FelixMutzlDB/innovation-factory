"""Data models for the AECO Hub digital-twin platform.

Covers the full building lifecycle: design (BIM, clash detection, room
requirements), build (cost, schedule, site reports, change orders), operate
(IoT, energy, maintenance, space utilization, leases), plus marketplace,
relationships graph, documents, and issues.

Naming:
- Tables use the ``dt_`` prefix (digital twin domain).
- Enums use the ``Aeco`` prefix to avoid OpenAPI schema collisions with other
  accelerators (e.g. ``AecoIssueStatus`` does not collide with
  ``MacIssueStatus``).
- The 3-model pattern is used for entities that are surfaced via the API:
  ``Dt<Entity>`` (SQLModel table) → ``Dt<Entity>Out`` (API response) →
  ``Dt<Entity>Create`` (API input).
"""

from datetime import date, datetime, timezone
from enum import Enum
from typing import Optional

from pydantic import BaseModel
from sqlmodel import Column, Field, JSON, SQLModel, Text


# ============================================================================
# Enums (Aeco-prefixed)
# ============================================================================


class AecoProjectPhase(str, Enum):
    design = "design"
    build = "build"
    operate = "operate"
    demolish = "demolish"


class AecoProjectStatus(str, Enum):
    planned = "planned"
    active = "active"
    on_hold = "on_hold"
    completed = "completed"
    cancelled = "cancelled"


class AecoBuildingType(str, Enum):
    residential = "residential"
    office = "office"
    retail = "retail"
    mixed_use = "mixed_use"
    industrial = "industrial"
    healthcare = "healthcare"
    education = "education"
    hospitality = "hospitality"
    infrastructure = "infrastructure"


class AecoSpaceType(str, Enum):
    office = "office"
    meeting_room = "meeting_room"
    apartment = "apartment"
    retail_unit = "retail_unit"
    corridor = "corridor"
    stairwell = "stairwell"
    bathroom = "bathroom"
    kitchen = "kitchen"
    technical = "technical"
    parking = "parking"
    storage = "storage"
    patient_room = "patient_room"
    operating_theatre = "operating_theatre"
    warehouse_zone = "warehouse_zone"
    common_area = "common_area"


class AecoAssetCategory(str, Enum):
    hvac = "hvac"
    electrical = "electrical"
    plumbing = "plumbing"
    lighting = "lighting"
    security = "security"
    fire_safety = "fire_safety"
    elevator = "elevator"
    appliance = "appliance"
    furniture = "furniture"
    sensor = "sensor"


class AecoMemberRole(str, Enum):
    project_manager = "project_manager"
    architect = "architect"
    engineer = "engineer"
    contractor = "contractor"
    owner = "owner"
    supplier = "supplier"
    facility_manager = "facility_manager"


class AecoIssueSeverity(str, Enum):
    minor = "minor"
    moderate = "moderate"
    major = "major"
    critical = "critical"


class AecoIssueStatus(str, Enum):
    open = "open"
    in_review = "in_review"
    in_progress = "in_progress"
    resolved = "resolved"
    closed = "closed"


class AecoIssueCategory(str, Enum):
    clash = "clash"
    rfi = "rfi"
    defect = "defect"
    change_request = "change_request"
    safety = "safety"
    design_issue = "design_issue"


class AecoDocumentType(str, Enum):
    bim = "bim"
    drawing = "drawing"
    report = "report"
    permit = "permit"
    contract = "contract"
    photo = "photo"
    cobie = "cobie"
    other = "other"


class AecoBimDiscipline(str, Enum):
    architectural = "architectural"
    structural = "structural"
    mep = "mep"
    electrical = "electrical"
    plumbing = "plumbing"
    hvac = "hvac"
    civil = "civil"


class AecoBimLod(str, Enum):
    lod_100 = "LOD_100"
    lod_200 = "LOD_200"
    lod_300 = "LOD_300"
    lod_400 = "LOD_400"
    lod_500 = "LOD_500"


class AecoSensorType(str, Enum):
    zone_temp = "zone_temp"
    supply_air_temp = "supply_air_temp"
    relative_humidity = "relative_humidity"
    co2_concentration = "co2_concentration"
    people_count = "people_count"
    active_power = "active_power"
    dimming_level = "dimming_level"
    damper_position = "damper_position"
    access_event = "access_event"


class AecoMaintenancePriority(str, Enum):
    low = "low"
    medium = "medium"
    high = "high"
    urgent = "urgent"


class AecoMaintenanceStatus(str, Enum):
    open = "open"
    scheduled = "scheduled"
    in_progress = "in_progress"
    completed = "completed"
    cancelled = "cancelled"


class AecoCostStatus(str, Enum):
    estimated = "estimated"
    committed = "committed"
    actual = "actual"
    paid = "paid"


class AecoChangeOrderStatus(str, Enum):
    proposed = "proposed"
    approved = "approved"
    rejected = "rejected"
    implemented = "implemented"


class AecoScheduleStatus(str, Enum):
    not_started = "not_started"
    in_progress = "in_progress"
    completed = "completed"
    delayed = "delayed"


class AecoSiteReportType(str, Enum):
    daily = "daily"
    weekly = "weekly"
    inspection = "inspection"
    safety = "safety"


class AecoLeaseStatus(str, Enum):
    active = "active"
    expired = "expired"
    pending = "pending"
    terminated = "terminated"


class AecoIntegrationStatus(str, Enum):
    connected = "connected"
    simulated = "simulated"
    planned = "planned"
    disconnected = "disconnected"


class AecoRelationshipType(str, Enum):
    contains = "contains"
    feeds_data_to = "feeds_data_to"
    depends_on = "depends_on"
    maintained_by = "maintained_by"
    designed_by = "designed_by"
    supplied_by = "supplied_by"
    monitors = "monitors"
    controls = "controls"


class AecoLifecycleSegment(str, Enum):
    """High-level lifecycle segment used by the Tool Navigator."""

    design = "design"
    qa_qc = "qa_qc"
    requirements = "requirements"
    build = "build"
    operate = "operate"
    visualize = "visualize"


# ============================================================================
# Core Entities
# ============================================================================


class DtProject(SQLModel, table=True):
    __tablename__ = "dt_projects"

    id: Optional[int] = Field(default=None, primary_key=True)
    code: str = Field(unique=True, index=True)
    name: str
    description: str = Field(default="", sa_column=Column(Text))
    client_name: str = Field(default="")
    city: str = Field(default="")
    country: str = Field(default="")
    phase: AecoProjectPhase = Field(default=AecoProjectPhase.design)
    status: AecoProjectStatus = Field(default=AecoProjectStatus.active)
    progress_pct: float = Field(default=0.0)
    budget_eur: float = Field(default=0.0)
    actual_cost_eur: float = Field(default=0.0)
    start_date: Optional[date] = None
    target_completion_date: Optional[date] = None
    actual_completion_date: Optional[date] = None
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))


class DtBuilding(SQLModel, table=True):
    __tablename__ = "dt_buildings"

    id: Optional[int] = Field(default=None, primary_key=True)
    project_id: int = Field(foreign_key="dt_projects.id", index=True)
    name: str
    building_type: AecoBuildingType
    floor_count: int = Field(default=1)
    gross_floor_area_sqm: float = Field(default=0.0)
    year_built: Optional[int] = None
    address: str = Field(default="")
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))


class DtFloor(SQLModel, table=True):
    __tablename__ = "dt_floors"

    id: Optional[int] = Field(default=None, primary_key=True)
    building_id: int = Field(foreign_key="dt_buildings.id", index=True)
    name: str
    level: int = Field(default=0)
    area_sqm: float = Field(default=0.0)
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))


class DtSpace(SQLModel, table=True):
    __tablename__ = "dt_spaces"

    id: Optional[int] = Field(default=None, primary_key=True)
    floor_id: int = Field(foreign_key="dt_floors.id", index=True)
    name: str
    space_type: AecoSpaceType
    area_sqm: float = Field(default=0.0)
    capacity: int = Field(default=0)
    room_number: str = Field(default="")
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))


class DtAsset(SQLModel, table=True):
    __tablename__ = "dt_assets"

    id: Optional[int] = Field(default=None, primary_key=True)
    space_id: Optional[int] = Field(default=None, foreign_key="dt_spaces.id", index=True)
    building_id: int = Field(foreign_key="dt_buildings.id", index=True)
    name: str
    category: AecoAssetCategory
    manufacturer: str = Field(default="")
    model: str = Field(default="")
    serial_number: str = Field(default="")
    install_date: Optional[date] = None
    warranty_expires: Optional[date] = None
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))


class DtProjectMember(SQLModel, table=True):
    __tablename__ = "dt_project_members"

    id: Optional[int] = Field(default=None, primary_key=True)
    project_id: int = Field(foreign_key="dt_projects.id", index=True)
    name: str
    organization: str = Field(default="")
    role: AecoMemberRole
    email: Optional[str] = None
    phone: Optional[str] = None
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))


# ============================================================================
# Lifecycle Tracking
# ============================================================================


class DtProjectPhase(SQLModel, table=True):
    __tablename__ = "dt_project_phases"

    id: Optional[int] = Field(default=None, primary_key=True)
    project_id: int = Field(foreign_key="dt_projects.id", index=True)
    phase: AecoProjectPhase
    started_on: Optional[date] = None
    ended_on: Optional[date] = None
    notes: str = Field(default="", sa_column=Column(Text))


class DtMilestone(SQLModel, table=True):
    __tablename__ = "dt_milestones"

    id: Optional[int] = Field(default=None, primary_key=True)
    project_id: int = Field(foreign_key="dt_projects.id", index=True)
    name: str
    phase: AecoProjectPhase
    target_date: date
    actual_date: Optional[date] = None
    completed: bool = Field(default=False)
    description: str = Field(default="", sa_column=Column(Text))


class DtDocument(SQLModel, table=True):
    __tablename__ = "dt_documents"

    id: Optional[int] = Field(default=None, primary_key=True)
    project_id: int = Field(foreign_key="dt_projects.id", index=True)
    title: str
    document_type: AecoDocumentType
    phase: AecoProjectPhase
    file_url: str = Field(default="")
    author: str = Field(default="")
    version: str = Field(default="")
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))


class DtIssue(SQLModel, table=True):
    __tablename__ = "dt_issues"

    id: Optional[int] = Field(default=None, primary_key=True)
    project_id: int = Field(foreign_key="dt_projects.id", index=True)
    title: str
    description: str = Field(default="", sa_column=Column(Text))
    category: AecoIssueCategory
    severity: AecoIssueSeverity = Field(default=AecoIssueSeverity.moderate)
    status: AecoIssueStatus = Field(default=AecoIssueStatus.open)
    raised_by: str = Field(default="")
    assigned_to: Optional[str] = None
    space_id: Optional[int] = Field(default=None, foreign_key="dt_spaces.id", index=True)
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    resolved_at: Optional[datetime] = None


# ============================================================================
# Design Phase
# ============================================================================


class DtBimModel(SQLModel, table=True):
    __tablename__ = "dt_bim_models"

    id: Optional[int] = Field(default=None, primary_key=True)
    project_id: int = Field(foreign_key="dt_projects.id", index=True)
    building_id: Optional[int] = Field(default=None, foreign_key="dt_buildings.id", index=True)
    name: str
    discipline: AecoBimDiscipline
    lod: AecoBimLod
    version: str = Field(default="1.0")
    file_url: str = Field(default="")
    file_size_mb: float = Field(default=0.0)
    element_count: int = Field(default=0)
    uploaded_by: str = Field(default="")
    uploaded_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))


class DtModelElement(SQLModel, table=True):
    __tablename__ = "dt_model_elements"

    id: Optional[int] = Field(default=None, primary_key=True)
    bim_model_id: int = Field(foreign_key="dt_bim_models.id", index=True)
    ifc_guid: str = Field(default="")
    element_type: str
    name: str = Field(default="")
    space_id: Optional[int] = Field(default=None, foreign_key="dt_spaces.id", index=True)
    properties_json: Optional[dict] = Field(default=None, sa_column=Column(JSON))


class DtClashReport(SQLModel, table=True):
    __tablename__ = "dt_clash_reports"

    id: Optional[int] = Field(default=None, primary_key=True)
    project_id: int = Field(foreign_key="dt_projects.id", index=True)
    bim_model_id: Optional[int] = Field(default=None, foreign_key="dt_bim_models.id", index=True)
    title: str
    discipline_a: AecoBimDiscipline
    discipline_b: AecoBimDiscipline
    severity: AecoIssueSeverity = Field(default=AecoIssueSeverity.moderate)
    status: AecoIssueStatus = Field(default=AecoIssueStatus.open)
    clash_count: int = Field(default=0)
    detected_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))


class DtRoomRequirement(SQLModel, table=True):
    __tablename__ = "dt_room_requirements"

    id: Optional[int] = Field(default=None, primary_key=True)
    space_id: int = Field(foreign_key="dt_spaces.id", index=True)
    requirement_type: str
    description: str = Field(default="", sa_column=Column(Text))
    spec_value: str = Field(default="")
    spec_unit: str = Field(default="")
    is_met: bool = Field(default=False)


# ============================================================================
# Build Phase
# ============================================================================


class DtCostItem(SQLModel, table=True):
    __tablename__ = "dt_cost_items"

    id: Optional[int] = Field(default=None, primary_key=True)
    project_id: int = Field(foreign_key="dt_projects.id", index=True)
    code: str = Field(default="")
    description: str
    category: str = Field(default="")
    quantity: float = Field(default=0.0)
    unit: str = Field(default="")
    unit_price_eur: float = Field(default=0.0)
    estimated_eur: float = Field(default=0.0)
    actual_eur: float = Field(default=0.0)
    status: AecoCostStatus = Field(default=AecoCostStatus.estimated)
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))


class DtScheduleActivity(SQLModel, table=True):
    __tablename__ = "dt_schedule_activities"

    id: Optional[int] = Field(default=None, primary_key=True)
    project_id: int = Field(foreign_key="dt_projects.id", index=True)
    name: str
    parent_activity_id: Optional[int] = Field(default=None, foreign_key="dt_schedule_activities.id", index=True)
    start_date: date
    end_date: date
    progress_pct: float = Field(default=0.0)
    status: AecoScheduleStatus = Field(default=AecoScheduleStatus.not_started)
    responsible_party: str = Field(default="")


class DtSiteReport(SQLModel, table=True):
    __tablename__ = "dt_site_reports"

    id: Optional[int] = Field(default=None, primary_key=True)
    project_id: int = Field(foreign_key="dt_projects.id", index=True)
    report_type: AecoSiteReportType
    report_date: date
    author: str = Field(default="")
    weather: str = Field(default="")
    workforce_count: int = Field(default=0)
    summary: str = Field(default="", sa_column=Column(Text))
    issues_count: int = Field(default=0)
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))


class DtChangeOrder(SQLModel, table=True):
    __tablename__ = "dt_change_orders"

    id: Optional[int] = Field(default=None, primary_key=True)
    project_id: int = Field(foreign_key="dt_projects.id", index=True)
    title: str
    description: str = Field(default="", sa_column=Column(Text))
    status: AecoChangeOrderStatus = Field(default=AecoChangeOrderStatus.proposed)
    cost_impact_eur: float = Field(default=0.0)
    schedule_impact_days: int = Field(default=0)
    requested_by: str = Field(default="")
    requested_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    decided_at: Optional[datetime] = None


# ============================================================================
# Operate Phase
# ============================================================================


class DtSensorDevice(SQLModel, table=True):
    __tablename__ = "dt_sensor_devices"

    id: Optional[int] = Field(default=None, primary_key=True)
    space_id: Optional[int] = Field(default=None, foreign_key="dt_spaces.id", index=True)
    building_id: int = Field(foreign_key="dt_buildings.id", index=True)
    sensor_code: str = Field(unique=True, index=True)
    sensor_type: AecoSensorType
    manufacturer: str = Field(default="")
    model: str = Field(default="")
    install_date: Optional[date] = None
    last_seen_at: Optional[datetime] = None


class DtMaintenanceOrder(SQLModel, table=True):
    __tablename__ = "dt_maintenance_orders"

    id: Optional[int] = Field(default=None, primary_key=True)
    asset_id: Optional[int] = Field(default=None, foreign_key="dt_assets.id", index=True)
    space_id: Optional[int] = Field(default=None, foreign_key="dt_spaces.id", index=True)
    building_id: int = Field(foreign_key="dt_buildings.id", index=True)
    title: str
    description: str = Field(default="", sa_column=Column(Text))
    priority: AecoMaintenancePriority = Field(default=AecoMaintenancePriority.medium)
    status: AecoMaintenanceStatus = Field(default=AecoMaintenanceStatus.open)
    assigned_technician: str = Field(default="")
    due_date: Optional[date] = None
    completed_at: Optional[datetime] = None
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))


class DtEnergyConsumption(SQLModel, table=True):
    """Aggregated energy data per meter / interval. Detailed sensor readings
    live in UC (see ``seed_uc_tables.py`` in Phase 3)."""

    __tablename__ = "dt_energy_consumption"

    id: Optional[int] = Field(default=None, primary_key=True)
    building_id: int = Field(foreign_key="dt_buildings.id", index=True)
    meter_code: str = Field(default="")
    period_start: datetime
    period_end: datetime
    kwh: float = Field(default=0.0)
    cost_eur: float = Field(default=0.0)


class DtSpaceUtilization(SQLModel, table=True):
    __tablename__ = "dt_space_utilization"

    id: Optional[int] = Field(default=None, primary_key=True)
    space_id: int = Field(foreign_key="dt_spaces.id", index=True)
    period_start: datetime
    period_end: datetime
    occupancy_pct: float = Field(default=0.0)
    peak_count: int = Field(default=0)


class DtLeaseContract(SQLModel, table=True):
    __tablename__ = "dt_lease_contracts"

    id: Optional[int] = Field(default=None, primary_key=True)
    space_id: int = Field(foreign_key="dt_spaces.id", index=True)
    tenant_name: str
    start_date: date
    end_date: date
    monthly_rent_eur: float = Field(default=0.0)
    status: AecoLeaseStatus = Field(default=AecoLeaseStatus.active)


# ============================================================================
# Marketplace
# ============================================================================


class DtMarketplacePartner(SQLModel, table=True):
    __tablename__ = "dt_marketplace_partners"

    id: Optional[int] = Field(default=None, primary_key=True)
    name: str = Field(unique=True, index=True)
    description: str = Field(default="", sa_column=Column(Text))
    website: str = Field(default="")
    logo_url: str = Field(default="")
    lifecycle_segment: AecoLifecycleSegment


class DtMarketplaceApp(SQLModel, table=True):
    __tablename__ = "dt_marketplace_apps"

    id: Optional[int] = Field(default=None, primary_key=True)
    partner_id: int = Field(foreign_key="dt_marketplace_partners.id", index=True)
    name: str
    description: str = Field(default="", sa_column=Column(Text))
    lifecycle_segment: AecoLifecycleSegment
    logo_url: str = Field(default="")
    is_featured: bool = Field(default=False)


class DtPartnerIntegration(SQLModel, table=True):
    __tablename__ = "dt_partner_integrations"

    id: Optional[int] = Field(default=None, primary_key=True)
    project_id: int = Field(foreign_key="dt_projects.id", index=True)
    app_id: int = Field(foreign_key="dt_marketplace_apps.id", index=True)
    status: AecoIntegrationStatus = Field(default=AecoIntegrationStatus.simulated)
    activated_at: Optional[datetime] = None
    notes: str = Field(default="")


# ============================================================================
# Relationships (graph view)
# ============================================================================


class DtRelationship(SQLModel, table=True):
    __tablename__ = "dt_relationships"

    id: Optional[int] = Field(default=None, primary_key=True)
    project_id: int = Field(foreign_key="dt_projects.id", index=True)
    source_type: str
    source_id: int
    target_type: str
    target_id: int
    relationship_type: AecoRelationshipType
    label: str = Field(default="")


# ============================================================================
# Pydantic Output Models
# ============================================================================


class DtProjectOut(BaseModel):
    id: int
    code: str
    name: str
    description: str
    client_name: str
    city: str
    country: str
    phase: AecoProjectPhase
    status: AecoProjectStatus
    progress_pct: float
    budget_eur: float
    actual_cost_eur: float
    start_date: Optional[date] = None
    target_completion_date: Optional[date] = None
    actual_completion_date: Optional[date] = None
    created_at: datetime


class DtBuildingOut(BaseModel):
    id: int
    project_id: int
    name: str
    building_type: AecoBuildingType
    floor_count: int
    gross_floor_area_sqm: float
    year_built: Optional[int] = None
    address: str


class DtFloorOut(BaseModel):
    id: int
    building_id: int
    name: str
    level: int
    area_sqm: float


class DtSpaceOut(BaseModel):
    id: int
    floor_id: int
    name: str
    space_type: AecoSpaceType
    area_sqm: float
    capacity: int
    room_number: str


class DtProjectMemberOut(BaseModel):
    id: int
    project_id: int
    name: str
    organization: str
    role: AecoMemberRole
    email: Optional[str] = None
    phone: Optional[str] = None


class DtProjectKpiOut(BaseModel):
    """Aggregated KPIs for the project overview page."""

    project_id: int
    building_count: int
    floor_count: int
    space_count: int
    member_count: int
    open_issues: int
    documents_count: int
    progress_pct: float
    budget_eur: float
    actual_cost_eur: float
    cost_variance_pct: float


class DtPortfolioStatsOut(BaseModel):
    """Top-level numbers for the portfolio home page."""

    total_projects: int
    active_projects: int
    operating_projects: int
    constructing_projects: int
    design_projects: int
    total_budget_eur: float
    total_actual_cost_eur: float
    total_buildings: int


# -- Issues -----------------------------------------------------------


class DtIssueOut(BaseModel):
    id: int
    project_id: int
    title: str
    description: str
    category: AecoIssueCategory
    severity: AecoIssueSeverity
    status: AecoIssueStatus
    raised_by: str
    assigned_to: Optional[str] = None
    space_id: Optional[int] = None
    created_at: datetime
    resolved_at: Optional[datetime] = None


class DtIssueStatsOut(BaseModel):
    project_id: int
    total: int
    open: int
    in_progress: int
    resolved: int
    critical: int
    by_category: dict[str, int]


# -- Documents --------------------------------------------------------


class DtDocumentOut(BaseModel):
    id: int
    project_id: int
    title: str
    document_type: AecoDocumentType
    phase: AecoProjectPhase
    file_url: str
    author: str
    version: str
    created_at: datetime


# -- Design phase -----------------------------------------------------


class DtBimModelOut(BaseModel):
    id: int
    project_id: int
    building_id: Optional[int] = None
    name: str
    discipline: AecoBimDiscipline
    lod: AecoBimLod
    version: str
    file_url: str
    file_size_mb: float
    element_count: int
    uploaded_by: str
    uploaded_at: datetime


class DtClashReportOut(BaseModel):
    id: int
    project_id: int
    bim_model_id: Optional[int] = None
    title: str
    discipline_a: AecoBimDiscipline
    discipline_b: AecoBimDiscipline
    severity: AecoIssueSeverity
    status: AecoIssueStatus
    clash_count: int
    detected_at: datetime


class DtRoomRequirementOut(BaseModel):
    id: int
    space_id: int
    requirement_type: str
    description: str
    spec_value: str
    spec_unit: str
    is_met: bool


# -- Build phase ------------------------------------------------------


class DtCostItemOut(BaseModel):
    id: int
    project_id: int
    code: str
    description: str
    category: str
    quantity: float
    unit: str
    unit_price_eur: float
    estimated_eur: float
    actual_eur: float
    status: AecoCostStatus
    created_at: datetime


class DtCostSummaryOut(BaseModel):
    project_id: int
    total_estimated_eur: float
    total_actual_eur: float
    variance_eur: float
    variance_pct: float
    item_count: int
    by_category: dict[str, float]


class DtScheduleActivityOut(BaseModel):
    id: int
    project_id: int
    name: str
    parent_activity_id: Optional[int] = None
    start_date: date
    end_date: date
    progress_pct: float
    status: AecoScheduleStatus
    responsible_party: str


class DtScheduleSummaryOut(BaseModel):
    project_id: int
    total: int
    not_started: int
    in_progress: int
    completed: int
    delayed: int
    avg_progress_pct: float


class DtSiteReportOut(BaseModel):
    id: int
    project_id: int
    report_type: AecoSiteReportType
    report_date: date
    author: str
    weather: str
    workforce_count: int
    summary: str
    issues_count: int
    created_at: datetime


class DtChangeOrderOut(BaseModel):
    id: int
    project_id: int
    title: str
    description: str
    status: AecoChangeOrderStatus
    cost_impact_eur: float
    schedule_impact_days: int
    requested_by: str
    requested_at: datetime
    decided_at: Optional[datetime] = None


# -- Operate phase ----------------------------------------------------


class DtSensorDeviceOut(BaseModel):
    id: int
    space_id: Optional[int] = None
    building_id: int
    sensor_code: str
    sensor_type: AecoSensorType
    manufacturer: str
    model: str
    install_date: Optional[date] = None
    last_seen_at: Optional[datetime] = None


class DtMaintenanceOrderOut(BaseModel):
    id: int
    asset_id: Optional[int] = None
    space_id: Optional[int] = None
    building_id: int
    title: str
    description: str
    priority: AecoMaintenancePriority
    status: AecoMaintenanceStatus
    assigned_technician: str
    due_date: Optional[date] = None
    completed_at: Optional[datetime] = None
    created_at: datetime


class DtEnergyConsumptionOut(BaseModel):
    id: int
    building_id: int
    meter_code: str
    period_start: datetime
    period_end: datetime
    kwh: float
    cost_eur: float


class DtEnergyDailyPointOut(BaseModel):
    """Single point on a daily energy trend chart (date as ISO string + kwh)."""

    period_start: datetime
    kwh: float
    cost_eur: float


class DtSpaceUtilizationOut(BaseModel):
    id: int
    space_id: int
    period_start: datetime
    period_end: datetime
    occupancy_pct: float
    peak_count: int


class DtLeaseContractOut(BaseModel):
    id: int
    space_id: int
    tenant_name: str
    start_date: date
    end_date: date
    monthly_rent_eur: float
    status: AecoLeaseStatus


class DtMaintenanceStatsOut(BaseModel):
    project_id: int
    total: int
    open: int
    in_progress: int
    completed: int
    overdue: int
    avg_days_to_complete: float


# -- Twin (spatial hierarchy) -----------------------------------------


class DtTwinSpaceOut(BaseModel):
    id: int
    name: str
    space_type: AecoSpaceType
    area_sqm: float
    capacity: int
    room_number: str


class DtTwinFloorOut(BaseModel):
    id: int
    name: str
    level: int
    area_sqm: float
    spaces: list[DtTwinSpaceOut]


class DtTwinBuildingOut(BaseModel):
    id: int
    name: str
    building_type: AecoBuildingType
    floor_count: int
    gross_floor_area_sqm: float
    floors: list[DtTwinFloorOut]


class DtTwinOut(BaseModel):
    project_id: int
    project_name: str
    project_phase: AecoProjectPhase
    buildings: list[DtTwinBuildingOut]


# ============================================================================
# Pydantic Input Models
# ============================================================================


class DtProjectCreate(BaseModel):
    code: str
    name: str
    description: str = ""
    client_name: str = ""
    city: str = ""
    country: str = ""
    phase: AecoProjectPhase = AecoProjectPhase.design
    status: AecoProjectStatus = AecoProjectStatus.active
    budget_eur: float = 0.0
    start_date: Optional[date] = None
    target_completion_date: Optional[date] = None


class DtBuildingCreate(BaseModel):
    project_id: int
    name: str
    building_type: AecoBuildingType
    floor_count: int = 1
    gross_floor_area_sqm: float = 0.0
    year_built: Optional[int] = None
    address: str = ""
