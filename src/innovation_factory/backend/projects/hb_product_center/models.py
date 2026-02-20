"""Data models for the Hugo Boss Intelligent Product Center.

Covers: products, visual recognition, quality control, authenticity verification,
supply chain intelligence, sustainability metrics, and AI chat.
"""

from datetime import date, datetime, timezone
from enum import Enum
from typing import Optional

from pydantic import BaseModel
from sqlmodel import Column, Field, JSON, SQLModel, Text


# ============================================================================
# Enums
# ============================================================================


class ProductCategory(str, Enum):
    suits = "suits"
    shirts = "shirts"
    knitwear = "knitwear"
    outerwear = "outerwear"
    trousers = "trousers"
    shoes = "shoes"
    accessories = "accessories"
    fragrances = "fragrances"
    sportswear = "sportswear"
    denim = "denim"


class ProductCollection(str, Enum):
    boss = "BOSS"
    hugo = "HUGO"
    boss_orange = "BOSS Orange"
    boss_green = "BOSS Green"


class ProductSeason(str, Enum):
    ss25 = "SS25"
    fw25 = "FW25"
    ss26 = "SS26"
    fw26 = "FW26"


class ProductStatus(str, Enum):
    active = "active"
    discontinued = "discontinued"
    sample = "sample"
    pre_production = "pre_production"


class ImageType(str, Enum):
    master = "master"
    sample = "sample"
    inspection = "inspection"
    customer = "customer"
    lifestyle = "lifestyle"


class RecognitionJobType(str, Enum):
    single = "single"
    batch = "batch"


class RecognitionJobStatus(str, Enum):
    pending = "pending"
    processing = "processing"
    completed = "completed"
    failed = "failed"


class UserRole(str, Enum):
    store_associate = "store_associate"
    warehouse_staff = "warehouse_staff"
    buyer = "buyer"
    merchandiser = "merchandiser"
    brand_protection = "brand_protection"
    sustainability = "sustainability"
    quality_inspector = "quality_inspector"


class InspectionStatus(str, Enum):
    pending = "pending"
    in_review = "in_review"
    approved = "approved"
    rejected = "rejected"


class DefectType(str, Enum):
    stitching = "stitching"
    fabric_flaw = "fabric_flaw"
    color_variation = "color_variation"
    misalignment = "misalignment"
    stain = "stain"
    missing_component = "missing_component"
    zipper_defect = "zipper_defect"
    button_issue = "button_issue"
    print_error = "print_error"
    sizing_error = "sizing_error"


class DefectSeverity(str, Enum):
    minor = "minor"
    moderate = "moderate"
    major = "major"
    critical = "critical"


class RequesterType(str, Enum):
    customer = "customer"
    partner = "partner"
    internal = "internal"
    retailer = "retailer"


class VerificationStatus(str, Enum):
    pending = "pending"
    verified = "verified"
    suspicious = "suspicious"
    counterfeit = "counterfeit"


class VerificationMethod(str, Enum):
    image_analysis = "image_analysis"
    nfc_tag = "nfc_tag"
    qr_code = "qr_code"
    label_check = "label_check"
    material_analysis = "material_analysis"


class AlertSeverity(str, Enum):
    low = "low"
    medium = "medium"
    high = "high"
    critical = "critical"


class AlertResolution(str, Enum):
    open = "open"
    investigating = "investigating"
    confirmed_counterfeit = "confirmed_counterfeit"
    false_positive = "false_positive"
    resolved = "resolved"


class SupplyChainEventType(str, Enum):
    manufactured = "manufactured"
    quality_checked = "quality_checked"
    shipped = "shipped"
    received_warehouse = "received_warehouse"
    inspected = "inspected"
    distributed = "distributed"
    received_store = "received_store"
    sold = "sold"
    returned = "returned"


class ComplianceStatus(str, Enum):
    compliant = "compliant"
    non_compliant = "non_compliant"
    pending_review = "pending_review"
    exempted = "exempted"


class ChatContext(str, Enum):
    recognition = "recognition"
    quality = "quality"
    authenticity = "authenticity"
    supply_chain = "supply_chain"
    general = "general"
    quality_asst = "quality_asst"


# ============================================================================
# Core Product Domain
# ============================================================================


class HbProduct(SQLModel, table=True):
    __tablename__ = "hb_products"

    id: Optional[int] = Field(default=None, primary_key=True)
    sku: str = Field(unique=True, index=True)
    style_name: str
    color: str
    color_code: str
    size: str
    category: ProductCategory
    collection: ProductCollection
    season: ProductSeason
    material: str
    price: float
    status: ProductStatus = Field(default=ProductStatus.active)
    country_of_origin: str = Field(default="")
    supplier_name: str = Field(default="")
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))


class HbProductImage(SQLModel, table=True):
    __tablename__ = "hb_product_images"

    id: Optional[int] = Field(default=None, primary_key=True)
    product_id: int = Field(foreign_key="hb_products.id", index=True)
    image_url: str
    image_type: ImageType
    uploaded_by: Optional[str] = None
    metadata_json: Optional[dict] = Field(default=None, sa_column=Column(JSON))
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))


# ============================================================================
# Visual Recognition Hub
# ============================================================================


class HbRecognitionJob(SQLModel, table=True):
    __tablename__ = "hb_recognition_jobs"

    id: Optional[int] = Field(default=None, primary_key=True)
    job_type: RecognitionJobType
    status: RecognitionJobStatus = Field(default=RecognitionJobStatus.pending)
    user_role: Optional[UserRole] = None
    submitted_by: Optional[str] = None
    image_count: int = Field(default=1)
    completed_count: int = Field(default=0)
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    completed_at: Optional[datetime] = None


class HbRecognitionResult(SQLModel, table=True):
    __tablename__ = "hb_recognition_results"

    id: Optional[int] = Field(default=None, primary_key=True)
    job_id: int = Field(foreign_key="hb_recognition_jobs.id", index=True)
    product_id: Optional[int] = Field(default=None, foreign_key="hb_products.id", index=True)
    image_url: str = Field(default="")
    confidence_score: float = Field(default=0.0)
    detected_sku: Optional[str] = None
    detected_color: Optional[str] = None
    detected_size: Optional[str] = None
    detected_category: Optional[str] = None
    processing_time_ms: int = Field(default=0)
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))


# ============================================================================
# Quality Control Studio
# ============================================================================


class HbQualityInspection(SQLModel, table=True):
    __tablename__ = "hb_quality_inspections"

    id: Optional[int] = Field(default=None, primary_key=True)
    product_id: int = Field(foreign_key="hb_products.id", index=True)
    batch_number: str = Field(default="")
    inspector: str = Field(default="")
    manufacturing_partner: str = Field(default="")
    overall_score: float = Field(default=0.0)
    status: InspectionStatus = Field(default=InspectionStatus.pending)
    notes: Optional[str] = Field(default=None, sa_column=Column(Text))
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    completed_at: Optional[datetime] = None


class HbQualityDefect(SQLModel, table=True):
    __tablename__ = "hb_quality_defects"

    id: Optional[int] = Field(default=None, primary_key=True)
    inspection_id: int = Field(foreign_key="hb_quality_inspections.id", index=True)
    defect_type: DefectType
    severity: DefectSeverity
    location_description: str = Field(default="")
    confidence_score: float = Field(default=0.0)
    image_url: Optional[str] = None
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))


# ============================================================================
# Authenticity Verification
# ============================================================================


class HbAuthVerification(SQLModel, table=True):
    __tablename__ = "hb_auth_verifications"

    id: Optional[int] = Field(default=None, primary_key=True)
    product_id: Optional[int] = Field(default=None, foreign_key="hb_products.id", index=True)
    requester_type: RequesterType
    requester_name: str = Field(default="")
    requester_email: Optional[str] = None
    status: VerificationStatus = Field(default=VerificationStatus.pending)
    confidence_score: Optional[float] = None
    verification_method: VerificationMethod = Field(default=VerificationMethod.image_analysis)
    image_url: Optional[str] = None
    region: str = Field(default="")
    notes: Optional[str] = Field(default=None, sa_column=Column(Text))
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    completed_at: Optional[datetime] = None


class HbAuthAlert(SQLModel, table=True):
    __tablename__ = "hb_auth_alerts"

    id: Optional[int] = Field(default=None, primary_key=True)
    verification_id: int = Field(foreign_key="hb_auth_verifications.id", index=True)
    alert_type: str = Field(default="")
    severity: AlertSeverity
    region: str = Field(default="")
    description: str = Field(default="", sa_column=Column(Text))
    investigated_by: Optional[str] = None
    resolution: AlertResolution = Field(default=AlertResolution.open)
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    resolved_at: Optional[datetime] = None


# ============================================================================
# Supply Chain Intelligence
# ============================================================================


class HbSupplyChainEvent(SQLModel, table=True):
    __tablename__ = "hb_supply_chain_events"

    id: Optional[int] = Field(default=None, primary_key=True)
    product_id: int = Field(foreign_key="hb_products.id", index=True)
    event_type: SupplyChainEventType
    location: str = Field(default="")
    partner_name: str = Field(default="")
    country: str = Field(default="")
    details: Optional[str] = Field(default=None, sa_column=Column(Text))
    event_date: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))


class HbSustainabilityMetric(SQLModel, table=True):
    __tablename__ = "hb_sustainability_metrics"

    id: Optional[int] = Field(default=None, primary_key=True)
    product_id: int = Field(foreign_key="hb_products.id", index=True)
    carbon_footprint_kg: float = Field(default=0.0)
    water_usage_liters: float = Field(default=0.0)
    recycled_content_pct: float = Field(default=0.0)
    organic_material_pct: float = Field(default=0.0)
    certifications: Optional[dict] = Field(default=None, sa_column=Column(JSON))
    compliance_status: ComplianceStatus = Field(default=ComplianceStatus.pending_review)
    last_audit_date: Optional[date] = None
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))


# ============================================================================
# Chat / AI Assistant
# ============================================================================


class HbChatSession(SQLModel, table=True):
    __tablename__ = "hb_chat_sessions"

    id: Optional[int] = Field(default=None, primary_key=True)
    user_role: Optional[UserRole] = None
    context: ChatContext = Field(default=ChatContext.general)
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))


class HbChatMessage(SQLModel, table=True):
    __tablename__ = "hb_chat_messages"

    id: Optional[int] = Field(default=None, primary_key=True)
    session_id: int = Field(foreign_key="hb_chat_sessions.id", index=True)
    role: str
    content: str = Field(sa_column=Column(Text))
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))


# ============================================================================
# Pydantic Output Models
# ============================================================================


class HbProductOut(BaseModel):
    id: int
    sku: str
    style_name: str
    color: str
    color_code: str
    size: str
    category: ProductCategory
    collection: ProductCollection
    season: ProductSeason
    material: str
    price: float
    status: ProductStatus
    country_of_origin: str
    supplier_name: str
    created_at: datetime


class HbProductImageOut(BaseModel):
    id: int
    product_id: int
    image_url: str
    image_type: ImageType
    uploaded_by: Optional[str] = None
    created_at: datetime


class HbRecognitionJobOut(BaseModel):
    id: int
    job_type: RecognitionJobType
    status: RecognitionJobStatus
    user_role: Optional[UserRole] = None
    submitted_by: Optional[str] = None
    image_count: int
    completed_count: int
    created_at: datetime
    completed_at: Optional[datetime] = None


class HbRecognitionResultOut(BaseModel):
    id: int
    job_id: int
    product_id: Optional[int] = None
    image_url: str
    confidence_score: float
    detected_sku: Optional[str] = None
    detected_color: Optional[str] = None
    detected_size: Optional[str] = None
    detected_category: Optional[str] = None
    processing_time_ms: int
    created_at: datetime


class HbRecognitionJobDetailOut(BaseModel):
    id: int
    job_type: RecognitionJobType
    status: RecognitionJobStatus
    user_role: Optional[UserRole] = None
    submitted_by: Optional[str] = None
    image_count: int
    completed_count: int
    created_at: datetime
    completed_at: Optional[datetime] = None
    results: list[HbRecognitionResultOut] = []


class HbQualityInspectionOut(BaseModel):
    id: int
    product_id: int
    batch_number: str
    inspector: str
    manufacturing_partner: str
    overall_score: float
    status: InspectionStatus
    notes: Optional[str] = None
    created_at: datetime
    completed_at: Optional[datetime] = None


class HbQualityDefectOut(BaseModel):
    id: int
    inspection_id: int
    defect_type: DefectType
    severity: DefectSeverity
    location_description: str
    confidence_score: float
    image_url: Optional[str] = None
    created_at: datetime


class HbInspectionDetailOut(BaseModel):
    id: int
    product_id: int
    batch_number: str
    inspector: str
    manufacturing_partner: str
    overall_score: float
    status: InspectionStatus
    notes: Optional[str] = None
    created_at: datetime
    completed_at: Optional[datetime] = None
    defects: list[HbQualityDefectOut] = []
    product: Optional[HbProductOut] = None


class HbAuthVerificationOut(BaseModel):
    id: int
    product_id: Optional[int] = None
    requester_type: RequesterType
    requester_name: str
    requester_email: Optional[str] = None
    status: VerificationStatus
    confidence_score: Optional[float] = None
    verification_method: VerificationMethod
    image_url: Optional[str] = None
    region: str
    notes: Optional[str] = None
    created_at: datetime
    completed_at: Optional[datetime] = None


class HbAuthAlertOut(BaseModel):
    id: int
    verification_id: int
    alert_type: str
    severity: AlertSeverity
    region: str
    description: str
    investigated_by: Optional[str] = None
    resolution: AlertResolution
    created_at: datetime
    resolved_at: Optional[datetime] = None


class HbSupplyChainEventOut(BaseModel):
    id: int
    product_id: int
    event_type: SupplyChainEventType
    location: str
    partner_name: str
    country: str
    details: Optional[str] = None
    event_date: datetime
    created_at: datetime


class HbSustainabilityMetricOut(BaseModel):
    id: int
    product_id: int
    carbon_footprint_kg: float
    water_usage_liters: float
    recycled_content_pct: float
    organic_material_pct: float
    certifications: Optional[dict] = None
    compliance_status: ComplianceStatus
    last_audit_date: Optional[date] = None
    created_at: datetime


class HbChatSessionOut(BaseModel):
    id: int
    user_role: Optional[UserRole] = None
    context: ChatContext
    created_at: datetime


class HbChatMessageOut(BaseModel):
    id: int
    session_id: int
    role: str
    content: str
    created_at: datetime


# ============================================================================
# Pydantic Input Models
# ============================================================================


class HbProductCreate(BaseModel):
    sku: str
    style_name: str
    color: str
    color_code: str
    size: str
    category: str
    collection: str
    season: str
    material: str
    price: float
    country_of_origin: str = ""
    supplier_name: str = ""


class HbRecognitionJobCreate(BaseModel):
    job_type: str = "single"
    user_role: Optional[str] = None
    submitted_by: Optional[str] = None
    image_count: int = 1


class HbQualityInspectionCreate(BaseModel):
    product_id: int
    batch_number: str = ""
    inspector: str = ""
    manufacturing_partner: str = ""


class HbQualityInspectionUpdate(BaseModel):
    status: Optional[str] = None
    overall_score: Optional[float] = None
    notes: Optional[str] = None


class HbAuthVerificationCreate(BaseModel):
    product_id: Optional[int] = None
    requester_type: str
    requester_name: str = ""
    requester_email: Optional[str] = None
    verification_method: str = "image_analysis"
    region: str = ""


class HbAuthAlertUpdate(BaseModel):
    resolution: Optional[str] = None
    investigated_by: Optional[str] = None


class HbChatSessionCreate(BaseModel):
    user_role: Optional[str] = None
    context: str = "general"


class HbChatMessageIn(BaseModel):
    content: str
    session_id: Optional[int] = None


# ============================================================================
# Dashboard / Aggregation Models
# ============================================================================


class HbDashboardSummary(BaseModel):
    total_products: int
    active_products: int
    recognition_jobs_today: int
    recognition_jobs_total: int
    avg_quality_score: float
    inspections_pending: int
    auth_success_rate: float
    auth_alerts_open: int
    supply_chain_events_total: int
    avg_sustainability_score: float


class HbQualityStats(BaseModel):
    total_inspections: int
    approved: int
    rejected: int
    pending: int
    in_review: int
    avg_score: float
    defect_counts: dict[str, int]
    severity_counts: dict[str, int]


class HbTrendPoint(BaseModel):
    date: str
    value: float
    label: Optional[str] = None


class HbProductJourney(BaseModel):
    product: HbProductOut
    events: list[HbSupplyChainEventOut]
    sustainability: Optional[HbSustainabilityMetricOut] = None
