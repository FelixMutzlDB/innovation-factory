import { useQuery, useSuspenseQuery, useMutation } from "@tanstack/react-query";
import type { UseQueryOptions, UseSuspenseQueryOptions, UseMutationOptions } from "@tanstack/react-query";

export const AlertResolution = {
  open: "open",
  investigating: "investigating",
  confirmed_counterfeit: "confirmed_counterfeit",
  false_positive: "false_positive",
  resolved: "resolved",
} as const;

export type AlertResolution = (typeof AlertResolution)[keyof typeof AlertResolution];

export const AlertSeverity = {
  low: "low",
  medium: "medium",
  high: "high",
  critical: "critical",
} as const;

export type AlertSeverity = (typeof AlertSeverity)[keyof typeof AlertSeverity];

export const AnomalySeverity = {
  low: "low",
  medium: "medium",
  high: "high",
  critical: "critical",
} as const;

export type AnomalySeverity = (typeof AnomalySeverity)[keyof typeof AnomalySeverity];

export const AnomalyStatus = {
  new: "new",
  acknowledged: "acknowledged",
  investigating: "investigating",
  resolved: "resolved",
  dismissed: "dismissed",
} as const;

export type AnomalyStatus = (typeof AnomalyStatus)[keyof typeof AnomalyStatus];

export const AnomalyType = {
  performance_drop: "performance_drop",
  budget_overrun: "budget_overrun",
  ctr_anomaly: "ctr_anomaly",
  impression_spike: "impression_spike",
  viewability_drop: "viewability_drop",
  conversion_decline: "conversion_decline",
  inventory_underutilization: "inventory_underutilization",
} as const;

export type AnomalyType = (typeof AnomalyType)[keyof typeof AnomalyType];

export interface AtAdInventoryOut {
  city?: string | null;
  cpm_rate: number;
  created_at: string;
  daily_impressions_est: number;
  format_spec?: Record<string, unknown> | null;
  id: number;
  inventory_type: InventoryType;
  latitude?: number | null;
  location_type: LocationType;
  longitude?: number | null;
  media_owner?: string | null;
  name: string;
  region?: string | null;
  status: InventoryStatus;
}

export interface AtAdvertiserOut {
  budget_tier: string;
  contact_email: string;
  contact_name: string;
  created_at: string;
  id: number;
  industry: string;
  name: string;
  phone?: string | null;
  updated_at: string;
  website?: string | null;
}

export interface AtAnomalyOut {
  actual_value: number;
  anomaly_type: AnomalyType;
  campaign_id?: number | null;
  description: string;
  detected_at: string;
  deviation_pct: number;
  expected_value: number;
  id: number;
  metric_name: string;
  placement_id?: number | null;
  resolved_at?: string | null;
  resolved_by?: string | null;
  rule_id?: number | null;
  severity: AnomalySeverity;
  status: AnomalyStatus;
  suggested_actions?: unknown[] | null;
  title: string;
}

export interface AtAnomalyRuleOut {
  condition_type: RuleConditionType;
  created_at: string;
  description?: string | null;
  enabled: boolean;
  id: number;
  lookback_days: number;
  metric_name: string;
  name: string;
  threshold_value: number;
}

export interface AtAnomalyUpdate {
  resolved_by?: string | null;
  status?: AnomalyStatus | null;
}

export interface AtCampaignOut {
  advertiser?: AtAdvertiserOut | null;
  advertiser_id: number;
  budget: number;
  campaign_type: CampaignType;
  created_at: string;
  description?: string | null;
  end_date: string;
  id: number;
  kpi_targets?: Record<string, unknown> | null;
  name: string;
  spent: number;
  start_date: string;
  status: CampaignStatus;
  target_audience?: string | null;
  target_regions?: unknown[] | null;
  updated_at: string;
}

export interface AtCampaignUpdate {
  budget?: number | null;
  kpi_targets?: Record<string, unknown> | null;
  spent?: number | null;
  status?: CampaignStatus | null;
  target_audience?: string | null;
  target_regions?: unknown[] | null;
}

export interface AtChatHistoryOut {
  ended_at?: string | null;
  messages: AtChatMessageOut[];
  session_id: number;
  session_type: string;
  started_at: string;
}

export interface AtChatMessageIn {
  message: string;
  session_id?: number | null;
}

export interface AtChatMessageOut {
  content: string;
  created_at: string;
  id: number;
  role: AtChatRole;
  session_id: number;
  sources?: Record<string, unknown>[] | null;
  tokens_used?: number | null;
}

export const AtChatRole = {
  user: "user",
  assistant: "assistant",
  system: "system",
} as const;

export type AtChatRole = (typeof AtChatRole)[keyof typeof AtChatRole];

export interface AtCustomerContractOut {
  account_manager?: string | null;
  advertiser_id: number;
  contract_number: string;
  contract_type: string;
  created_at: string;
  end_date: string;
  id: number;
  start_date: string;
  status: ContractStatus;
  terms_summary?: string | null;
  total_value: number;
}

export interface AtDashboardSummaryOut {
  active_anomalies: number;
  active_campaigns: number;
  available_inventory: number;
  avg_ctr: number;
  critical_anomalies: number;
  total_campaigns: number;
  total_impressions: number;
  total_inventory: number;
  total_spend: number;
}

export interface AtIssueOut {
  advertiser_id?: number | null;
  assigned_to?: string | null;
  campaign_id?: number | null;
  category: IssueCategory;
  created_at: string;
  description: string;
  id: number;
  priority: IssuePriority;
  resolution?: string | null;
  resolved_at?: string | null;
  status: IssueStatus;
  title: string;
  updated_at: string;
}

export interface AtIssueUpdate {
  assigned_to?: string | null;
  priority?: IssuePriority | null;
  resolution?: string | null;
  status?: IssueStatus | null;
}

export interface AtPlacementOut {
  campaign_id: number;
  created_at: string;
  daily_budget: number;
  end_date: string;
  id: number;
  inventory?: AtAdInventoryOut | null;
  inventory_id: number;
  start_date: string;
  status: PlacementStatus;
}

export interface Body_bsh_uploadTicketMedia {
  file: string;
  media_type: string;
}

export interface Body_vh_upload_ticket_media {
  file: string;
}

export interface BshChatHistoryOut {
  ended_at?: string | null;
  messages: BshChatMessageOut[];
  session_id: number;
  session_type: string;
  started_at: string;
  ticket_id: number;
}

export interface BshChatMessageIn {
  message: string;
  session_type?: string;
}

export interface BshChatMessageOut {
  content: string;
  created_at: string;
  id: number;
  role: BshChatRole;
  session_id: number;
  sources?: Record<string, unknown>[] | null;
  tokens_used?: number | null;
}

export const BshChatRole = {
  user: "user",
  assistant: "assistant",
  system: "system",
} as const;

export type BshChatRole = (typeof BshChatRole)[keyof typeof BshChatRole];

export interface BshCustomerDeviceIn {
  batch_number?: string | null;
  device_id: number;
  purchase_date?: string | null;
  serial_number: string;
  warranty_expiry_date?: string | null;
}

export interface BshCustomerDeviceOut {
  batch_number?: string | null;
  customer_id: number;
  device?: BshDeviceOut | null;
  device_id: number;
  id: number;
  purchase_date?: string | null;
  registered_at: string;
  serial_number: string;
  warranty_expiry_date?: string | null;
}

export interface BshCustomerIn {
  address?: string | null;
  city?: string | null;
  country?: string | null;
  first_name: string;
  last_name: string;
  phone?: string | null;
  postal_code?: string | null;
}

export interface BshCustomerOut {
  address?: string | null;
  city?: string | null;
  country?: string | null;
  created_at: string;
  databricks_user_id: string;
  email: string;
  first_name: string;
  id: number;
  last_name: string;
  phone?: string | null;
  postal_code?: string | null;
  updated_at: string;
}

export interface BshDeviceOut {
  brand: string;
  category: DeviceCategory;
  created_at: string;
  description?: string | null;
  id: number;
  image_url?: string | null;
  model_number: string;
  name: string;
  specifications?: Record<string, unknown> | null;
}

export interface BshDocumentOut {
  content?: string | null;
  created_at: string;
  device_id: number;
  document_type: string;
  file_url?: string | null;
  id: number;
  language: string;
  title: string;
  updated_at: string;
  version?: string | null;
}

export interface BshKnowledgeArticleOut {
  category: DeviceCategory;
  content: string;
  created_at: string;
  device_id?: number | null;
  helpful_count: number;
  id: number;
  issue_type?: string | null;
  tags?: string[] | null;
  title: string;
  updated_at: string;
  view_count: number;
}

export interface BshTechnicianOut {
  certification_level?: string | null;
  created_at: string;
  databricks_user_id: string;
  email: string;
  first_name: string;
  id: number;
  last_name: string;
  phone?: string | null;
  specialization?: string | null;
  updated_at: string;
}

export interface BshTicketIn {
  customer_device_id: number;
  description: string;
  priority?: number;
  title: string;
}

export interface BshTicketNoteIn {
  content: string;
  is_internal?: boolean;
}

export interface BshTicketNoteOut {
  author_id?: number | null;
  author_role: innovation_factory__backend__projects__bsh_home_connect__models__UserRole;
  content: string;
  created_at: string;
  id: number;
  is_internal: boolean;
  ticket_id: number;
}

export interface BshTicketOut {
  assigned_at?: string | null;
  completed_at?: string | null;
  created_at: string;
  customer_device?: BshCustomerDeviceOut | null;
  customer_device_id: number;
  customer_id: number;
  description: string;
  id: number;
  issue_summary?: string | null;
  notes?: BshTicketNoteOut[] | null;
  priority: number;
  shipping_label_url?: string | null;
  status: BshTicketStatus;
  technician_id?: number | null;
  title: string;
  tracking_number?: string | null;
  troubleshooting_attempted?: string | null;
  updated_at: string;
}

export const BshTicketStatus = {
  open: "open",
  in_progress: "in_progress",
  awaiting_parts: "awaiting_parts",
  awaiting_customer: "awaiting_customer",
  shipped_for_repair: "shipped_for_repair",
  in_repair: "in_repair",
  resolved: "resolved",
  closed: "closed",
} as const;

export type BshTicketStatus = (typeof BshTicketStatus)[keyof typeof BshTicketStatus];

export interface BshTicketUpdate {
  issue_summary?: string | null;
  priority?: number | null;
  status?: BshTicketStatus | null;
  technician_id?: number | null;
  tracking_number?: string | null;
  troubleshooting_attempted?: string | null;
}

export const CampaignStatus = {
  draft: "draft",
  active: "active",
  paused: "paused",
  completed: "completed",
  cancelled: "cancelled",
} as const;

export type CampaignStatus = (typeof CampaignStatus)[keyof typeof CampaignStatus];

export const CampaignType = {
  online: "online",
  outdoor: "outdoor",
  crossmedia: "crossmedia",
} as const;

export type CampaignType = (typeof CampaignType)[keyof typeof CampaignType];

export const ChatContext = {
  recognition: "recognition",
  quality: "quality",
  authenticity: "authenticity",
  supply_chain: "supply_chain",
  general: "general",
  quality_asst: "quality_asst",
} as const;

export type ChatContext = (typeof ChatContext)[keyof typeof ChatContext];

export const ComplianceStatus = {
  compliant: "compliant",
  non_compliant: "non_compliant",
  pending_review: "pending_review",
  exempted: "exempted",
} as const;

export type ComplianceStatus = (typeof ComplianceStatus)[keyof typeof ComplianceStatus];

export const ConsumptionCategory = {
  household_appliances: "household_appliances",
  climate_control: "climate_control",
  ev_charging: "ev_charging",
  garden: "garden",
  other: "other",
} as const;

export type ConsumptionCategory = (typeof ConsumptionCategory)[keyof typeof ConsumptionCategory];

export const ContractStatus = {
  active: "active",
  expired: "expired",
  pending: "pending",
  terminated: "terminated",
} as const;

export type ContractStatus = (typeof ContractStatus)[keyof typeof ContractStatus];

export interface DashboardEmbedOut {
  configured?: boolean;
  dashboard_id?: string | null;
  embed_url?: string | null;
}

export interface DatabricksResourcesOut {
  dashboard_embed_url: string;
  dashboard_id: string;
  genie_space_id: string;
  mas_endpoint_name: string;
  mas_tile_id: string;
  warehouse_id: string;
  workspace_url: string;
}

export const DefectSeverity = {
  minor: "minor",
  moderate: "moderate",
  major: "major",
  critical: "critical",
} as const;

export type DefectSeverity = (typeof DefectSeverity)[keyof typeof DefectSeverity];

export const DefectType = {
  stitching: "stitching",
  fabric_flaw: "fabric_flaw",
  color_variation: "color_variation",
  misalignment: "misalignment",
  stain: "stain",
  missing_component: "missing_component",
  zipper_defect: "zipper_defect",
  button_issue: "button_issue",
  print_error: "print_error",
  sizing_error: "sizing_error",
} as const;

export type DefectType = (typeof DefectType)[keyof typeof DefectType];

export const DeviceCategory = {
  washing_machine: "washing_machine",
  dryer: "dryer",
  dishwasher: "dishwasher",
  refrigerator: "refrigerator",
  oven: "oven",
  cooktop: "cooktop",
  microwave: "microwave",
  coffee_machine: "coffee_machine",
  vacuum_cleaner: "vacuum_cleaner",
  other: "other",
} as const;

export type DeviceCategory = (typeof DeviceCategory)[keyof typeof DeviceCategory];

export const DeviceType = {
  heat_pump: "heat_pump",
  pv_system: "pv_system",
  battery: "battery",
  ev: "ev",
  grid_meter: "grid_meter",
} as const;

export type DeviceType = (typeof DeviceType)[keyof typeof DeviceType];

export interface DocContentOut {
  content: string;
  slug: string;
  title: string;
}

export interface DocListOut {
  slugs: string[];
}

export const FuelType = {
  diesel: "diesel",
  premium_diesel: "premium_diesel",
  regular_95: "regular_95",
  premium_98: "premium_98",
  lpg: "lpg",
} as const;

export type FuelType = (typeof FuelType)[keyof typeof FuelType];

export interface HTTPValidationError {
  detail?: ValidationError[];
}

export interface HbAuthAlertOut {
  alert_type: string;
  created_at: string;
  description: string;
  id: number;
  investigated_by?: string | null;
  region: string;
  resolution: AlertResolution;
  resolved_at?: string | null;
  severity: AlertSeverity;
  verification_id: number;
}

export interface HbAuthAlertUpdate {
  investigated_by?: string | null;
  resolution?: string | null;
}

export interface HbAuthVerificationCreate {
  product_id?: number | null;
  region?: string;
  requester_email?: string | null;
  requester_name?: string;
  requester_type: string;
  verification_method?: string;
}

export interface HbAuthVerificationOut {
  completed_at?: string | null;
  confidence_score?: number | null;
  created_at: string;
  id: number;
  image_url?: string | null;
  notes?: string | null;
  product_id?: number | null;
  region: string;
  requester_email?: string | null;
  requester_name: string;
  requester_type: RequesterType;
  status: VerificationStatus;
  verification_method: VerificationMethod;
}

export interface HbChatMessageIn {
  content: string;
  session_id?: number | null;
}

export interface HbChatMessageOut {
  content: string;
  created_at: string;
  id: number;
  role: string;
  session_id: number;
}

export interface HbChatSessionCreate {
  context?: string;
  user_role?: string | null;
}

export interface HbChatSessionOut {
  context: ChatContext;
  created_at: string;
  id: number;
  user_role?: innovation_factory__backend__projects__hb_product_center__models__UserRole | null;
}

export interface HbDashboardSummary {
  active_products: number;
  auth_alerts_open: number;
  auth_success_rate: number;
  avg_quality_score: number;
  avg_sustainability_score: number;
  inspections_pending: number;
  recognition_jobs_today: number;
  recognition_jobs_total: number;
  supply_chain_events_total: number;
  total_products: number;
}

export interface HbDatabricksResourcesOut {
  aq_dashboard_embed_url: string;
  aq_dashboard_id: string;
  aq_genie_space_id: string;
  sc_dashboard_embed_url: string;
  sc_dashboard_id: string;
  sc_genie_space_id: string;
  workspace_url: string;
}

export interface HbInspectionDetailOut {
  batch_number: string;
  completed_at?: string | null;
  created_at: string;
  defects?: HbQualityDefectOut[];
  id: number;
  inspector: string;
  manufacturing_partner: string;
  notes?: string | null;
  overall_score: number;
  product?: HbProductOut | null;
  product_id: number;
  status: InspectionStatus;
}

export interface HbProductImageOut {
  created_at: string;
  id: number;
  image_type: ImageType;
  image_url: string;
  product_id: number;
  uploaded_by?: string | null;
}

export interface HbProductJourney {
  events: HbSupplyChainEventOut[];
  product: HbProductOut;
  sustainability?: HbSustainabilityMetricOut | null;
}

export interface HbProductOut {
  category: innovation_factory__backend__projects__hb_product_center__models__ProductCategory;
  collection: ProductCollection;
  color: string;
  color_code: string;
  country_of_origin: string;
  created_at: string;
  id: number;
  material: string;
  price: number;
  season: ProductSeason;
  size: string;
  sku: string;
  status: ProductStatus;
  style_name: string;
  supplier_name: string;
}

export interface HbQualityDefectOut {
  confidence_score: number;
  created_at: string;
  defect_type: DefectType;
  id: number;
  image_url?: string | null;
  inspection_id: number;
  location_description: string;
  severity: DefectSeverity;
}

export interface HbQualityInspectionCreate {
  batch_number?: string;
  inspector?: string;
  manufacturing_partner?: string;
  product_id: number;
}

export interface HbQualityInspectionOut {
  batch_number: string;
  completed_at?: string | null;
  created_at: string;
  id: number;
  inspector: string;
  manufacturing_partner: string;
  notes?: string | null;
  overall_score: number;
  product_id: number;
  status: InspectionStatus;
}

export interface HbQualityInspectionUpdate {
  notes?: string | null;
  overall_score?: number | null;
  status?: string | null;
}

export interface HbQualityStats {
  approved: number;
  avg_score: number;
  defect_counts: Record<string, number>;
  in_review: number;
  pending: number;
  rejected: number;
  severity_counts: Record<string, number>;
  total_inspections: number;
}

export interface HbRecognitionJobCreate {
  image_count?: number;
  job_type?: string;
  submitted_by?: string | null;
  user_role?: string | null;
}

export interface HbRecognitionJobDetailOut {
  completed_at?: string | null;
  completed_count: number;
  created_at: string;
  id: number;
  image_count: number;
  job_type: RecognitionJobType;
  results?: HbRecognitionResultOut[];
  status: RecognitionJobStatus;
  submitted_by?: string | null;
  user_role?: innovation_factory__backend__projects__hb_product_center__models__UserRole | null;
}

export interface HbRecognitionJobOut {
  completed_at?: string | null;
  completed_count: number;
  created_at: string;
  id: number;
  image_count: number;
  job_type: RecognitionJobType;
  status: RecognitionJobStatus;
  submitted_by?: string | null;
  user_role?: innovation_factory__backend__projects__hb_product_center__models__UserRole | null;
}

export interface HbRecognitionResultOut {
  confidence_score: number;
  created_at: string;
  detected_category?: string | null;
  detected_color?: string | null;
  detected_size?: string | null;
  detected_sku?: string | null;
  id: number;
  image_url: string;
  job_id: number;
  processing_time_ms: number;
  product_id?: number | null;
}

export interface HbSupplyChainEventOut {
  country: string;
  created_at: string;
  details?: string | null;
  event_date: string;
  event_type: SupplyChainEventType;
  id: number;
  location: string;
  partner_name: string;
  product_id: number;
}

export interface HbSustainabilityMetricOut {
  carbon_footprint_kg: number;
  certifications?: Record<string, unknown> | null;
  compliance_status: ComplianceStatus;
  created_at: string;
  id: number;
  last_audit_date?: string | null;
  organic_material_pct: number;
  product_id: number;
  recycled_content_pct: number;
  water_usage_liters: number;
}

export interface HbTrendPoint {
  date: string;
  label?: string | null;
  value: number;
}

export interface IdeaMessageIn {
  content: string;
}

export interface IdeaMessageOut {
  content: string;
  created_at: string;
  id: number;
  role: string;
  session_id: number;
}

export interface IdeaSessionOut {
  company_name?: string | null;
  created_at: string;
  description?: string | null;
  generated_prompt?: string | null;
  id: number;
  status: IdeaSessionStatus;
}

export const IdeaSessionStatus = {
  collecting_name: "collecting_name",
  collecting_description: "collecting_description",
  generating: "generating",
  completed: "completed",
} as const;

export type IdeaSessionStatus = (typeof IdeaSessionStatus)[keyof typeof IdeaSessionStatus];

export const ImageType = {
  master: "master",
  sample: "sample",
  inspection: "inspection",
  customer: "customer",
  lifestyle: "lifestyle",
} as const;

export type ImageType = (typeof ImageType)[keyof typeof ImageType];

export const InspectionStatus = {
  pending: "pending",
  in_review: "in_review",
  approved: "approved",
  rejected: "rejected",
} as const;

export type InspectionStatus = (typeof InspectionStatus)[keyof typeof InspectionStatus];

export const InventoryStatus = {
  available: "available",
  booked: "booked",
  maintenance: "maintenance",
  inactive: "inactive",
} as const;

export type InventoryStatus = (typeof InventoryStatus)[keyof typeof InventoryStatus];

export const InventoryType = {
  display_banner: "display_banner",
  video: "video",
  native: "native",
  high_impact: "high_impact",
  dooh_screen: "dooh_screen",
  billboard: "billboard",
  transit_poster: "transit_poster",
  city_light: "city_light",
  mega_poster: "mega_poster",
} as const;

export type InventoryType = (typeof InventoryType)[keyof typeof InventoryType];

export const IssueCategory = {
  delivery: "delivery",
  targeting: "targeting",
  creative: "creative",
  billing: "billing",
  technical: "technical",
  reporting: "reporting",
  inventory: "inventory",
} as const;

export type IssueCategory = (typeof IssueCategory)[keyof typeof IssueCategory];

export const IssuePriority = {
  low: "low",
  medium: "medium",
  high: "high",
  urgent: "urgent",
} as const;

export type IssuePriority = (typeof IssuePriority)[keyof typeof IssuePriority];

export const IssueStatus = {
  open: "open",
  in_progress: "in_progress",
  waiting_on_customer: "waiting_on_customer",
  resolved: "resolved",
  closed: "closed",
} as const;

export type IssueStatus = (typeof IssueStatus)[keyof typeof IssueStatus];

export const LocationType = {
  online: "online",
  train_station: "train_station",
  mall: "mall",
  pedestrian_zone: "pedestrian_zone",
  highway: "highway",
  bus_stop: "bus_stop",
  airport: "airport",
  subway: "subway",
} as const;

export type LocationType = (typeof LocationType)[keyof typeof LocationType];

export const LoyaltyTier = {
  bronze: "bronze",
  silver: "silver",
  gold: "gold",
  platinum: "platinum",
} as const;

export type LoyaltyTier = (typeof LoyaltyTier)[keyof typeof LoyaltyTier];

export const MacAlertSeverity = {
  low: "low",
  medium: "medium",
  high: "high",
  critical: "critical",
} as const;

export type MacAlertSeverity = (typeof MacAlertSeverity)[keyof typeof MacAlertSeverity];

export const MacAlertStatus = {
  active: "active",
  acknowledged: "acknowledged",
  resolved: "resolved",
  dismissed: "dismissed",
} as const;

export type MacAlertStatus = (typeof MacAlertStatus)[keyof typeof MacAlertStatus];

export interface MacAnomalyAlertOut {
  description: string;
  detected_at: string;
  id: number;
  metric_type: string;
  resolved_at?: string | null;
  severity: MacAlertSeverity;
  station_id: number;
  status: MacAlertStatus;
  suggested_action: string;
  title: string;
}

export interface MacAnomalyAlertUpdate {
  resolved_at?: string | null;
  status?: MacAlertStatus | null;
}

export interface MacChatHistoryOut {
  ended_at?: string | null;
  messages: MacChatMessageOut[];
  session_id: number;
  session_type: string;
  started_at: string;
}

export interface MacChatMessageIn {
  message: string;
  session_type?: string;
}

export interface MacChatMessageOut {
  content: string;
  created_at: string;
  id: number;
  role: MacChatRole;
  session_id: number;
  sources?: Record<string, unknown>[] | null;
}

export const MacChatRole = {
  user: "user",
  assistant: "assistant",
  system: "system",
} as const;

export type MacChatRole = (typeof MacChatRole)[keyof typeof MacChatRole];

export interface MacCompetitorPriceOut {
  competitor_name: string;
  fuel_type: FuelType;
  id: number;
  price_date: string;
  price_per_liter: number;
  station_id: number;
}

export interface MacCustomerContractOut {
  contract_type: string;
  customer_id: number;
  discount_pct: number;
  end_date?: string | null;
  id: number;
  monthly_volume_commitment: number;
  notes?: string | null;
  start_date: string;
}

export interface MacCustomerProfileOut {
  company_name: string;
  contact_email: string;
  contact_name: string;
  contract_type?: string | null;
  fleet_size: number;
  id: number;
  loyalty_tier: LoyaltyTier;
  phone?: string | null;
}

export interface MacFuelSaleOut {
  fuel_type: FuelType;
  id: number;
  margin: number;
  revenue: number;
  sale_date: string;
  station_id: number;
  unit_price: number;
  volume_liters: number;
}

export interface MacInventoryOut {
  delivery_scheduled: boolean;
  id: number;
  product_category: innovation_factory__backend__projects__mol_asm_cockpit__models__ProductCategory;
  record_date: string;
  reorder_point: number;
  spoilage_count: number;
  station_id: number;
  stock_level: number;
  stock_out_events: number;
}

export const MacIssueCategory = {
  equipment: "equipment",
  supply_chain: "supply_chain",
  quality: "quality",
  customer_complaint: "customer_complaint",
  staffing: "staffing",
  safety: "safety",
  it_system: "it_system",
} as const;

export type MacIssueCategory = (typeof MacIssueCategory)[keyof typeof MacIssueCategory];

export interface MacIssueOut {
  category: MacIssueCategory;
  created_at: string;
  description: string;
  id: number;
  priority: number;
  resolution?: string | null;
  resolved_at?: string | null;
  station_id: number;
  status: MacIssueStatus;
  title: string;
}

export const MacIssueStatus = {
  open: "open",
  in_progress: "in_progress",
  resolved: "resolved",
  closed: "closed",
} as const;

export type MacIssueStatus = (typeof MacIssueStatus)[keyof typeof MacIssueStatus];

export interface MacLoyaltyMetricOut {
  active_members: number;
  id: number;
  loyalty_revenue_share: number;
  month: string;
  new_signups: number;
  points_redeemed: number;
  station_id: number;
}

export interface MacNonfuelSaleOut {
  category: NonfuelCategory;
  id: number;
  margin: number;
  quantity: number;
  revenue: number;
  sale_date: string;
  station_id: number;
}

export interface MacPriceHistoryOut {
  cost_per_liter: number;
  fuel_type: FuelType;
  id: number;
  price_date: string;
  price_per_liter: number;
  station_id: number;
}

export interface MacRegionOut {
  country: string;
  id: number;
  name: string;
}

export interface MacStationKPI {
  active_alerts: number;
  city: string;
  region_name: string;
  station_code: string;
  station_id: number;
  station_name: string;
  total_fuel_margin: number;
  total_fuel_revenue: number;
  total_fuel_volume: number;
  total_nonfuel_margin: number;
  total_nonfuel_revenue: number;
}

export interface MacStationOut {
  city: string;
  has_ev_charging: boolean;
  has_fresh_corner: boolean;
  id: number;
  latitude: number;
  longitude: number;
  name: string;
  num_pumps: number;
  opened_date?: string | null;
  region_id: number;
  shop_area_sqm: number;
  station_code: string;
  station_type: StationType;
}

export interface MacWorkforceShiftOut {
  actual_headcount: number;
  id: number;
  overtime_hours: number;
  planned_headcount: number;
  shift_date: string;
  shift_type: ShiftType;
  station_id: number;
}

export const NonfuelCategory = {
  coffee: "coffee",
  hot_food: "hot_food",
  cold_food: "cold_food",
  bakery: "bakery",
  beverages: "beverages",
  tobacco: "tobacco",
  car_care: "car_care",
  convenience: "convenience",
} as const;

export type NonfuelCategory = (typeof NonfuelCategory)[keyof typeof NonfuelCategory];

export const OptimizationMode = {
  energy_saver: "energy_saver",
  cost_saver: "cost_saver",
} as const;

export type OptimizationMode = (typeof OptimizationMode)[keyof typeof OptimizationMode];

export const PlacementStatus = {
  scheduled: "scheduled",
  active: "active",
  paused: "paused",
  completed: "completed",
  cancelled: "cancelled",
} as const;

export type PlacementStatus = (typeof PlacementStatus)[keyof typeof PlacementStatus];

export const ProductCollection = {
  BOSS: "BOSS",
  HUGO: "HUGO",
  "BOSS Orange": "BOSS Orange",
  "BOSS Green": "BOSS Green",
} as const;

export type ProductCollection = (typeof ProductCollection)[keyof typeof ProductCollection];

export interface ProductIdentifyRequest {
  description: string;
}

export interface ProductIdentifyResponse {
  ai_analysis: string;
  matches: ProductMatch[];
}

export interface ProductMatch {
  category: string;
  collection?: string | null;
  color?: string | null;
  confidence: string;
  material?: string | null;
  price?: number | null;
  product_id: number;
  sku: string;
  style_name: string;
}

export const ProductSeason = {
  SS25: "SS25",
  FW25: "FW25",
  SS26: "SS26",
  FW26: "FW26",
} as const;

export type ProductSeason = (typeof ProductSeason)[keyof typeof ProductSeason];

export const ProductStatus = {
  active: "active",
  discontinued: "discontinued",
  sample: "sample",
  pre_production: "pre_production",
} as const;

export type ProductStatus = (typeof ProductStatus)[keyof typeof ProductStatus];

export interface ProjectOut {
  color?: string | null;
  company: string;
  description: string;
  icon?: string | null;
  id: number;
  name: string;
  slug: string;
}

export const RecognitionJobStatus = {
  pending: "pending",
  processing: "processing",
  completed: "completed",
  failed: "failed",
} as const;

export type RecognitionJobStatus = (typeof RecognitionJobStatus)[keyof typeof RecognitionJobStatus];

export const RecognitionJobType = {
  single: "single",
  batch: "batch",
} as const;

export type RecognitionJobType = (typeof RecognitionJobType)[keyof typeof RecognitionJobType];

export const RequesterType = {
  customer: "customer",
  partner: "partner",
  internal: "internal",
  retailer: "retailer",
} as const;

export type RequesterType = (typeof RequesterType)[keyof typeof RequesterType];

export const RuleConditionType = {
  threshold: "threshold",
  trend: "trend",
  deviation: "deviation",
} as const;

export type RuleConditionType = (typeof RuleConditionType)[keyof typeof RuleConditionType];

export const ShiftType = {
  morning: "morning",
  afternoon: "afternoon",
  night: "night",
} as const;

export type ShiftType = (typeof ShiftType)[keyof typeof ShiftType];

export const StationType = {
  highway: "highway",
  urban: "urban",
  suburban: "suburban",
} as const;

export type StationType = (typeof StationType)[keyof typeof StationType];

export const SupplyChainEventType = {
  manufactured: "manufactured",
  quality_checked: "quality_checked",
  shipped: "shipped",
  received_warehouse: "received_warehouse",
  inspected: "inspected",
  distributed: "distributed",
  received_store: "received_store",
  sold: "sold",
  returned: "returned",
} as const;

export type SupplyChainEventType = (typeof SupplyChainEventType)[keyof typeof SupplyChainEventType];

export interface ValidationError {
  ctx?: Record<string, unknown>;
  input?: unknown;
  loc: (string | number)[];
  msg: string;
  type: string;
}

export const VerificationMethod = {
  image_analysis: "image_analysis",
  nfc_tag: "nfc_tag",
  qr_code: "qr_code",
  label_check: "label_check",
  material_analysis: "material_analysis",
} as const;

export type VerificationMethod = (typeof VerificationMethod)[keyof typeof VerificationMethod];

export const VerificationStatus = {
  pending: "pending",
  verified: "verified",
  suspicious: "suspicious",
  counterfeit: "counterfeit",
} as const;

export type VerificationStatus = (typeof VerificationStatus)[keyof typeof VerificationStatus];

export interface VersionOut {
  version: string;
}

export interface VhAlternativeProviderOut {
  estimated_monthly_cost_eur: number;
  potential_savings_eur: number;
  potential_savings_percent: number;
  provider: VhEnergyProviderOut;
}

export interface VhChatHistoryOut {
  messages: VhChatMessageOut[];
  session_id: number;
}

export interface VhChatMessageIn {
  content: string;
}

export interface VhChatMessageOut {
  content: string;
  created_at: string;
  id: number;
  role: VhChatRole;
  sources?: string | null;
}

export const VhChatRole = {
  user: "user",
  assistant: "assistant",
  system: "system",
} as const;

export type VhChatRole = (typeof VhChatRole)[keyof typeof VhChatRole];

export interface VhConsumptionBreakdownOut {
  category: ConsumptionCategory;
  percentage: number;
  value_kwh: number;
}

export interface VhEnergyDeviceOut {
  brand: string;
  capacity_kw?: number | null;
  device_type: DeviceType;
  household_id: number;
  id: number;
  installation_date: string;
  last_maintenance_date?: string | null;
  model: string;
  next_maintenance_date?: string | null;
  serial_number?: string | null;
  specifications?: string | null;
}

export interface VhEnergyProviderOut {
  base_rate_eur: number;
  feed_in_rate_eur: number;
  id: number;
  kwh_rate_eur: number;
  name: string;
  night_rate_eur?: number | null;
}

export interface VhEnergyReadingOut {
  battery_charge_kwh: number;
  battery_discharge_kwh: number;
  battery_level_kwh: number;
  ev_consumption_kwh: number;
  grid_export_kwh: number;
  grid_import_kwh: number;
  heat_pump_consumption_kwh: number;
  household_consumption_kwh: number;
  household_id: number;
  id: number;
  pv_generation_kwh: number;
  timestamp: string;
  total_consumption_kwh: number;
}

export interface VhEnergySourcesOut {
  battery_discharge_kw: number;
  grid_import_kw: number;
  pv_generation_kw: number;
  total_available_kw: number;
}

export interface VhHouseholdCockpitOut {
  consumption_breakdown: VhConsumptionBreakdownOut[];
  cost_this_month_eur: number;
  cost_today_eur: number;
  current_consumption_kw: number;
  devices: VhEnergyDeviceOut[];
  energy_sources: VhEnergySourcesOut;
  household: VhHouseholdOut;
  recent_readings: VhEnergyReadingOut[];
}

export interface VhHouseholdOut {
  address: string;
  created_at: string;
  has_battery: boolean;
  has_ev: boolean;
  has_heat_pump: boolean;
  has_pv: boolean;
  id: number;
  neighborhood_id: number;
  optimization_mode: OptimizationMode;
  owner_name: string;
  updated_at: string;
}

export interface VhHouseholdSummaryOut {
  address: string;
  battery_level_percent: number;
  current_consumption_kw: number;
  current_generation_kw: number;
  id: number;
  optimization_mode: OptimizationMode;
  owner_name: string;
}

export interface VhMaintenanceAlertAcknowledge {
  is_acknowledged: boolean;
}

export interface VhMaintenanceAlertOut {
  alert_type: string;
  created_at: string;
  device_id: number;
  device_model: string;
  device_type: DeviceType;
  id: number;
  is_acknowledged: boolean;
  message: string;
  predicted_date?: string | null;
  severity: AlertSeverity;
}

export interface VhNeighborhoodOut {
  created_at: string;
  id: number;
  location: string;
  name: string;
  total_households: number;
}

export interface VhNeighborhoodSummaryOut {
  households: VhHouseholdSummaryOut[];
  id: number;
  location: string;
  name: string;
  total_consumption_kwh: number;
  total_generation_kwh: number;
  total_households: number;
  total_storage_capacity_kwh: number;
}

export interface VhOptimizationModeUpdate {
  optimization_mode: OptimizationMode;
}

export interface VhOptimizationSuggestionOut {
  category: string;
  description: string;
  id: string;
  potential_savings_eur?: number | null;
  potential_savings_kwh?: number | null;
  title: string;
}

export interface VhProviderComparisonOut {
  alternative_providers: VhAlternativeProviderOut[];
  current_monthly_cost_eur: number;
  current_provider: VhEnergyProviderOut;
}

export interface VhTicketIn {
  description: string;
  device_id?: number | null;
  priority?: string | null;
  title: string;
}

export interface VhTicketOut {
  created_at: string;
  description: string;
  device_id?: number | null;
  household_id: number;
  id: number;
  issue_summary?: string | null;
  priority?: string | null;
  resolution_notes?: string | null;
  resolved_at?: string | null;
  status: VhTicketStatus;
  title: string;
  updated_at: string;
}

export const VhTicketStatus = {
  new: "new",
  in_progress: "in_progress",
  resolved: "resolved",
  escalated: "escalated",
} as const;

export type VhTicketStatus = (typeof VhTicketStatus)[keyof typeof VhTicketStatus];

export interface VhTicketUpdate {
  resolution_notes?: string | null;
  status?: VhTicketStatus | null;
}

export const innovation_factory__backend__projects__bsh_home_connect__models__UserRole = {
  customer: "customer",
  technician: "technician",
  system: "system",
} as const;

export type innovation_factory__backend__projects__bsh_home_connect__models__UserRole = (typeof innovation_factory__backend__projects__bsh_home_connect__models__UserRole)[keyof typeof innovation_factory__backend__projects__bsh_home_connect__models__UserRole];

export const innovation_factory__backend__projects__hb_product_center__models__ProductCategory = {
  suits: "suits",
  shirts: "shirts",
  knitwear: "knitwear",
  outerwear: "outerwear",
  trousers: "trousers",
  shoes: "shoes",
  accessories: "accessories",
  fragrances: "fragrances",
  sportswear: "sportswear",
  denim: "denim",
} as const;

export type innovation_factory__backend__projects__hb_product_center__models__ProductCategory = (typeof innovation_factory__backend__projects__hb_product_center__models__ProductCategory)[keyof typeof innovation_factory__backend__projects__hb_product_center__models__ProductCategory];

export const innovation_factory__backend__projects__hb_product_center__models__UserRole = {
  store_associate: "store_associate",
  warehouse_staff: "warehouse_staff",
  buyer: "buyer",
  merchandiser: "merchandiser",
  brand_protection: "brand_protection",
  sustainability: "sustainability",
  quality_inspector: "quality_inspector",
} as const;

export type innovation_factory__backend__projects__hb_product_center__models__UserRole = (typeof innovation_factory__backend__projects__hb_product_center__models__UserRole)[keyof typeof innovation_factory__backend__projects__hb_product_center__models__UserRole];

export const innovation_factory__backend__projects__mol_asm_cockpit__models__ProductCategory = {
  fuel: "fuel",
  coffee: "coffee",
  hot_food: "hot_food",
  cold_food: "cold_food",
  bakery: "bakery",
  beverages: "beverages",
  tobacco: "tobacco",
  car_care: "car_care",
  convenience: "convenience",
} as const;

export type innovation_factory__backend__projects__mol_asm_cockpit__models__ProductCategory = (typeof innovation_factory__backend__projects__mol_asm_cockpit__models__ProductCategory)[keyof typeof innovation_factory__backend__projects__mol_asm_cockpit__models__ProductCategory];

export interface CurrentUserParams {
  "X-Forwarded-Access-Token"?: string | null;
}

export interface GetProjectDocParams {
  slug: string;
}

export interface GetIdeaSessionParams {
  session_id: number;
}

export interface SendIdeaMessageParams {
  session_id: number;
}

export interface GetIdeaMessagesParams {
  session_id: number;
}

export interface At_listAnomaliesParams {
  status?: AnomalyStatus | null;
  severity?: AnomalySeverity | null;
  anomaly_type?: AnomalyType | null;
  campaign_id?: number | null;
  limit?: number;
  offset?: number;
}

export interface At_getAnomalyParams {
  anomaly_id: number;
}

export interface At_updateAnomalyParams {
  anomaly_id: number;
}

export interface At_listCampaignsParams {
  status?: CampaignStatus | null;
  campaign_type?: CampaignType | null;
  advertiser_id?: number | null;
  limit?: number;
  offset?: number;
}

export interface At_getCampaignParams {
  campaign_id: number;
}

export interface At_updateCampaignParams {
  campaign_id: number;
}

export interface At_listPlacementsParams {
  campaign_id: number;
}

export interface At_getChatSessionParams {
  session_id: number;
}

export interface At_listContractsParams {
  advertiser_id?: number | null;
}

export interface At_listInventoryParams {
  inventory_type?: InventoryType | null;
  location_type?: LocationType | null;
  status?: InventoryStatus | null;
  city?: string | null;
  limit?: number;
  offset?: number;
}

export interface At_getInventoryItemParams {
  inventory_id: number;
}

export interface At_listIssuesParams {
  status?: IssueStatus | null;
  priority?: IssuePriority | null;
  category?: IssueCategory | null;
  campaign_id?: number | null;
  limit?: number;
  offset?: number;
}

export interface At_getIssueParams {
  issue_id: number;
}

export interface At_updateIssueParams {
  issue_id: number;
}

export interface At_getPlacementParams {
  placement_id: number;
}

export interface Bsh_getCurrentCustomerParams {
  "X-Forwarded-Access-Token"?: string | null;
}

export interface Bsh_updateCurrentCustomerParams {
  "X-Forwarded-Access-Token"?: string | null;
}

export interface Bsh_listMyDevicesParams {
  "X-Forwarded-Access-Token"?: string | null;
}

export interface Bsh_registerDeviceParams {
  "X-Forwarded-Access-Token"?: string | null;
}

export interface Bsh_getMyDeviceParams {
  device_id: number;
  "X-Forwarded-Access-Token"?: string | null;
}

export interface Bsh_listDevicesParams {
  category?: string | null;
}

export interface Bsh_getDeviceDocumentsParams {
  device_id: number;
}

export interface Bsh_getDeviceKnowledgeParams {
  device_id: number;
}

export interface Bsh_searchKnowledgeParams {
  query: string;
  category?: DeviceCategory | null;
  limit?: number;
}

export interface Bsh_getCurrentTechnicianParams {
  "X-Forwarded-Access-Token"?: string | null;
}

export interface Bsh_getTechnicianParams {
  technician_id: number;
}

export interface Bsh_listTicketsParams {
  status?: BshTicketStatus | null;
  role?: string | null;
  "X-Forwarded-Access-Token"?: string | null;
}

export interface Bsh_createTicketParams {
  "X-Forwarded-Access-Token"?: string | null;
}

export interface Bsh_getTicketParams {
  ticket_id: number;
  "X-Forwarded-Access-Token"?: string | null;
}

export interface Bsh_updateTicketParams {
  ticket_id: number;
  "X-Forwarded-Access-Token"?: string | null;
}

export interface Bsh_sendChatMessageParams {
  ticket_id: number;
  "X-Forwarded-Access-Token"?: string | null;
}

export interface Bsh_getChatHistoryParams {
  ticket_id: number;
  session_type?: string;
  "X-Forwarded-Access-Token"?: string | null;
}

export interface Bsh_uploadTicketMediaParams {
  ticket_id: number;
  "X-Forwarded-Access-Token"?: string | null;
}

export interface Bsh_listTicketNotesParams {
  ticket_id: number;
  "X-Forwarded-Access-Token"?: string | null;
}

export interface Bsh_addTicketNoteParams {
  ticket_id: number;
  "X-Forwarded-Access-Token"?: string | null;
}

export interface Bsh_generateShippingLabelParams {
  ticket_id: number;
  "X-Forwarded-Access-Token"?: string | null;
}

export interface Hb_listAlertsParams {
  resolution?: string | null;
  limit?: number;
  offset?: number;
}

export interface Hb_updateAlertParams {
  alert_id: number;
}

export interface Hb_listVerificationsParams {
  status?: string | null;
  requester_type?: string | null;
  limit?: number;
  offset?: number;
}

export interface Hb_getVerificationParams {
  verification_id: number;
}

export interface Hb_getChatMessagesParams {
  session_id: number;
}

export interface Hb_sendChatMessageParams {
  session_id: number;
}

export interface Hb_listProductsParams {
  category?: string | null;
  collection?: string | null;
  season?: string | null;
  search?: string | null;
  limit?: number;
  offset?: number;
}

export interface Hb_getProductParams {
  product_id: number;
}

export interface Hb_getProductImagesParams {
  product_id: number;
}

export interface Hb_listInspectionsParams {
  status?: string | null;
  product_id?: number | null;
  limit?: number;
  offset?: number;
}

export interface Hb_getInspectionParams {
  inspection_id: number;
}

export interface Hb_updateInspectionParams {
  inspection_id: number;
}

export interface Hb_listRecognitionJobsParams {
  status?: string | null;
  limit?: number;
  offset?: number;
}

export interface Hb_getRecognitionJobParams {
  job_id: number;
}

export interface Hb_listSupplyChainEventsParams {
  product_id?: number | null;
  event_type?: string | null;
  country?: string | null;
  limit?: number;
  offset?: number;
}

export interface Hb_getProductJourneyParams {
  product_id: number;
}

export interface Hb_listSustainabilityMetricsParams {
  limit?: number;
  offset?: number;
}

export interface Hb_getProductSustainabilityParams {
  product_id: number;
}

export interface Mac_listAnomalyAlertsParams {
  station_id?: number | null;
  status?: string | null;
  severity?: string | null;
  limit?: number;
}

export interface Mac_getAnomalyAlertParams {
  alert_id: number;
}

export interface Mac_updateAnomalyAlertParams {
  alert_id: number;
}

export interface Mac_getChatHistoryParams {
  session_id: number;
}

export interface Mac_sendChatMessageParams {
  session_id?: number | null;
}

export interface Mac_listInventoryParams {
  station_id?: number | null;
  product_category?: string | null;
  days?: number;
  limit?: number;
}

export interface Mac_listCompetitorPricesParams {
  station_id?: number | null;
  days?: number;
  limit?: number;
}

export interface Mac_listPriceHistoryParams {
  station_id?: number | null;
  fuel_type?: string | null;
  days?: number;
  limit?: number;
}

export interface Mac_listFuelSalesParams {
  station_id?: number | null;
  fuel_type?: string | null;
  days?: number;
  limit?: number;
}

export interface Mac_listLoyaltyMetricsParams {
  station_id?: number | null;
  limit?: number;
}

export interface Mac_listNonfuelSalesParams {
  station_id?: number | null;
  category?: string | null;
  days?: number;
  limit?: number;
}

export interface Mac_listStationsParams {
  region_id?: number | null;
  station_type?: string | null;
}

export interface Mac_stationKPIsParams {
  days?: number;
}

export interface Mac_getStationParams {
  station_id: number;
}

export interface Mac_listCustomerContractsParams {
  customer_id: number;
}

export interface Mac_listIssuesParams {
  station_id?: number | null;
  status?: string | null;
  category?: string | null;
  limit?: number;
}

export interface Mac_listWorkforceShiftsParams {
  station_id?: number | null;
  days?: number;
  limit?: number;
}

export interface Vh_send_chat_messageParams {
  ticket_id: number;
}

export interface Vh_get_chat_historyParams {
  ticket_id: number;
}

export interface Vh_get_current_readingParams {
  household_id: number;
}

export interface Vh_get_energy_readingsParams {
  household_id: number;
  hours?: number;
}

export interface Vh_get_householdParams {
  household_id: number;
}

export interface Vh_get_household_cockpitParams {
  household_id: number;
}

export interface Vh_update_optimization_modeParams {
  household_id: number;
}

export interface Vh_acknowledge_alertParams {
  alert_id: number;
}

export interface Vh_list_maintenance_alertsParams {
  household_id: number;
  include_acknowledged?: boolean;
}

export interface Vh_get_neighborhood_summaryParams {
  neighborhood_id: number;
}

export interface Vh_get_optimization_suggestionsParams {
  household_id: number;
}

export interface Vh_compare_providersParams {
  household_id: number;
  current_provider_id?: number;
}

export interface Vh_list_ticketsParams {
  household_id?: number | null;
  status?: VhTicketStatus | null;
}

export interface Vh_create_ticketParams {
  household_id: number;
}

export interface Vh_get_ticketParams {
  ticket_id: number;
}

export interface Vh_update_ticketParams {
  ticket_id: number;
}

export interface Vh_upload_ticket_mediaParams {
  ticket_id: number;
}

export interface GetProjectParams {
  slug: string;
}

export class ApiError extends Error {
  status: number;
  statusText: string;
  body: unknown;

  constructor(status: number, statusText: string, body: unknown) {
    super(`HTTP ${status}: ${statusText}`);
    this.name = "ApiError";
    this.status = status;
    this.statusText = statusText;
    this.body = body;
  }
}

export const currentUser = async (params?: CurrentUserParams, options?: RequestInit): Promise<{ data: unknown }> => {
  const res = await fetch("/api/current-user", { ...options, method: "GET", headers: { ...(params?.["X-Forwarded-Access-Token"] != null && { "X-Forwarded-Access-Token": params["X-Forwarded-Access-Token"] }), ...options?.headers } });
  if (!res.ok) {
    const body = await res.text();
    let parsed: unknown;
    try { parsed = JSON.parse(body); } catch { parsed = body; }
    throw new ApiError(res.status, res.statusText, parsed);
  }
  return { data: await res.json() };
};

export const currentUserKey = (params?: CurrentUserParams) => {
  return ["/api/current-user", params] as const;
};

export function useCurrentUser<TData = { data: unknown }>(options?: { params?: CurrentUserParams; query?: Omit<UseQueryOptions<{ data: unknown }, ApiError, TData>, "queryKey" | "queryFn"> }) {
  return useQuery({ queryKey: currentUserKey(options?.params), queryFn: () => currentUser(options?.params), ...options?.query });
}

export function useCurrentUserSuspense<TData = { data: unknown }>(options?: { params?: CurrentUserParams; query?: Omit<UseSuspenseQueryOptions<{ data: unknown }, ApiError, TData>, "queryKey" | "queryFn"> }) {
  return useSuspenseQuery({ queryKey: currentUserKey(options?.params), queryFn: () => currentUser(options?.params), ...options?.query });
}

export const listProjectDocs = async (options?: RequestInit): Promise<{ data: DocListOut }> => {
  const res = await fetch("/api/docs/projects", { ...options, method: "GET" });
  if (!res.ok) {
    const body = await res.text();
    let parsed: unknown;
    try { parsed = JSON.parse(body); } catch { parsed = body; }
    throw new ApiError(res.status, res.statusText, parsed);
  }
  return { data: await res.json() };
};

export const listProjectDocsKey = () => {
  return ["/api/docs/projects"] as const;
};

export function useListProjectDocs<TData = { data: DocListOut }>(options?: { query?: Omit<UseQueryOptions<{ data: DocListOut }, ApiError, TData>, "queryKey" | "queryFn"> }) {
  return useQuery({ queryKey: listProjectDocsKey(), queryFn: () => listProjectDocs(), ...options?.query });
}

export function useListProjectDocsSuspense<TData = { data: DocListOut }>(options?: { query?: Omit<UseSuspenseQueryOptions<{ data: DocListOut }, ApiError, TData>, "queryKey" | "queryFn"> }) {
  return useSuspenseQuery({ queryKey: listProjectDocsKey(), queryFn: () => listProjectDocs(), ...options?.query });
}

export const getProjectDoc = async (params: GetProjectDocParams, options?: RequestInit): Promise<{ data: DocContentOut }> => {
  const res = await fetch(`/api/docs/projects/${params.slug}`, { ...options, method: "GET" });
  if (!res.ok) {
    const body = await res.text();
    let parsed: unknown;
    try { parsed = JSON.parse(body); } catch { parsed = body; }
    throw new ApiError(res.status, res.statusText, parsed);
  }
  return { data: await res.json() };
};

export const getProjectDocKey = (params?: GetProjectDocParams) => {
  return ["/api/docs/projects/{slug}", params] as const;
};

export function useGetProjectDoc<TData = { data: DocContentOut }>(options: { params: GetProjectDocParams; query?: Omit<UseQueryOptions<{ data: DocContentOut }, ApiError, TData>, "queryKey" | "queryFn"> }) {
  return useQuery({ queryKey: getProjectDocKey(options.params), queryFn: () => getProjectDoc(options.params), ...options?.query });
}

export function useGetProjectDocSuspense<TData = { data: DocContentOut }>(options: { params: GetProjectDocParams; query?: Omit<UseSuspenseQueryOptions<{ data: DocContentOut }, ApiError, TData>, "queryKey" | "queryFn"> }) {
  return useSuspenseQuery({ queryKey: getProjectDocKey(options.params), queryFn: () => getProjectDoc(options.params), ...options?.query });
}

export const createIdeaSession = async (options?: RequestInit): Promise<{ data: IdeaSessionOut }> => {
  const res = await fetch("/api/ideas/sessions", { ...options, method: "POST" });
  if (!res.ok) {
    const body = await res.text();
    let parsed: unknown;
    try { parsed = JSON.parse(body); } catch { parsed = body; }
    throw new ApiError(res.status, res.statusText, parsed);
  }
  return { data: await res.json() };
};

export function useCreateIdeaSession(options?: { mutation?: UseMutationOptions<{ data: IdeaSessionOut }, ApiError, void> }) {
  return useMutation({ mutationFn: () => createIdeaSession(), ...options?.mutation });
}

export const getIdeaSession = async (params: GetIdeaSessionParams, options?: RequestInit): Promise<{ data: IdeaSessionOut }> => {
  const res = await fetch(`/api/ideas/sessions/${params.session_id}`, { ...options, method: "GET" });
  if (!res.ok) {
    const body = await res.text();
    let parsed: unknown;
    try { parsed = JSON.parse(body); } catch { parsed = body; }
    throw new ApiError(res.status, res.statusText, parsed);
  }
  return { data: await res.json() };
};

export const getIdeaSessionKey = (params?: GetIdeaSessionParams) => {
  return ["/api/ideas/sessions/{session_id}", params] as const;
};

export function useGetIdeaSession<TData = { data: IdeaSessionOut }>(options: { params: GetIdeaSessionParams; query?: Omit<UseQueryOptions<{ data: IdeaSessionOut }, ApiError, TData>, "queryKey" | "queryFn"> }) {
  return useQuery({ queryKey: getIdeaSessionKey(options.params), queryFn: () => getIdeaSession(options.params), ...options?.query });
}

export function useGetIdeaSessionSuspense<TData = { data: IdeaSessionOut }>(options: { params: GetIdeaSessionParams; query?: Omit<UseSuspenseQueryOptions<{ data: IdeaSessionOut }, ApiError, TData>, "queryKey" | "queryFn"> }) {
  return useSuspenseQuery({ queryKey: getIdeaSessionKey(options.params), queryFn: () => getIdeaSession(options.params), ...options?.query });
}

export const sendIdeaMessage = async (params: SendIdeaMessageParams, data: IdeaMessageIn, options?: RequestInit): Promise<{ data: unknown }> => {
  const res = await fetch(`/api/ideas/sessions/${params.session_id}/chat`, { ...options, method: "POST", headers: { "Content-Type": "application/json", ...options?.headers }, body: JSON.stringify(data) });
  if (!res.ok) {
    const body = await res.text();
    let parsed: unknown;
    try { parsed = JSON.parse(body); } catch { parsed = body; }
    throw new ApiError(res.status, res.statusText, parsed);
  }
  return { data: await res.json() };
};

export function useSendIdeaMessage(options?: { mutation?: UseMutationOptions<{ data: unknown }, ApiError, { params: SendIdeaMessageParams; data: IdeaMessageIn }> }) {
  return useMutation({ mutationFn: (vars) => sendIdeaMessage(vars.params, vars.data), ...options?.mutation });
}

export const getIdeaMessages = async (params: GetIdeaMessagesParams, options?: RequestInit): Promise<{ data: IdeaMessageOut[] }> => {
  const res = await fetch(`/api/ideas/sessions/${params.session_id}/messages`, { ...options, method: "GET" });
  if (!res.ok) {
    const body = await res.text();
    let parsed: unknown;
    try { parsed = JSON.parse(body); } catch { parsed = body; }
    throw new ApiError(res.status, res.statusText, parsed);
  }
  return { data: await res.json() };
};

export const getIdeaMessagesKey = (params?: GetIdeaMessagesParams) => {
  return ["/api/ideas/sessions/{session_id}/messages", params] as const;
};

export function useGetIdeaMessages<TData = { data: IdeaMessageOut[] }>(options: { params: GetIdeaMessagesParams; query?: Omit<UseQueryOptions<{ data: IdeaMessageOut[] }, ApiError, TData>, "queryKey" | "queryFn"> }) {
  return useQuery({ queryKey: getIdeaMessagesKey(options.params), queryFn: () => getIdeaMessages(options.params), ...options?.query });
}

export function useGetIdeaMessagesSuspense<TData = { data: IdeaMessageOut[] }>(options: { params: GetIdeaMessagesParams; query?: Omit<UseSuspenseQueryOptions<{ data: IdeaMessageOut[] }, ApiError, TData>, "queryKey" | "queryFn"> }) {
  return useSuspenseQuery({ queryKey: getIdeaMessagesKey(options.params), queryFn: () => getIdeaMessages(options.params), ...options?.query });
}

export const listProjects = async (options?: RequestInit): Promise<{ data: ProjectOut[] }> => {
  const res = await fetch("/api/projects", { ...options, method: "GET" });
  if (!res.ok) {
    const body = await res.text();
    let parsed: unknown;
    try { parsed = JSON.parse(body); } catch { parsed = body; }
    throw new ApiError(res.status, res.statusText, parsed);
  }
  return { data: await res.json() };
};

export const listProjectsKey = () => {
  return ["/api/projects"] as const;
};

export function useListProjects<TData = { data: ProjectOut[] }>(options?: { query?: Omit<UseQueryOptions<{ data: ProjectOut[] }, ApiError, TData>, "queryKey" | "queryFn"> }) {
  return useQuery({ queryKey: listProjectsKey(), queryFn: () => listProjects(), ...options?.query });
}

export function useListProjectsSuspense<TData = { data: ProjectOut[] }>(options?: { query?: Omit<UseSuspenseQueryOptions<{ data: ProjectOut[] }, ApiError, TData>, "queryKey" | "queryFn"> }) {
  return useSuspenseQuery({ queryKey: listProjectsKey(), queryFn: () => listProjects(), ...options?.query });
}

export const at_listAdvertisers = async (options?: RequestInit): Promise<{ data: AtAdvertiserOut[] }> => {
  const res = await fetch("/api/projects/adtech-intelligence/advertisers", { ...options, method: "GET" });
  if (!res.ok) {
    const body = await res.text();
    let parsed: unknown;
    try { parsed = JSON.parse(body); } catch { parsed = body; }
    throw new ApiError(res.status, res.statusText, parsed);
  }
  return { data: await res.json() };
};

export const at_listAdvertisersKey = () => {
  return ["/api/projects/adtech-intelligence/advertisers"] as const;
};

export function useAt_listAdvertisers<TData = { data: AtAdvertiserOut[] }>(options?: { query?: Omit<UseQueryOptions<{ data: AtAdvertiserOut[] }, ApiError, TData>, "queryKey" | "queryFn"> }) {
  return useQuery({ queryKey: at_listAdvertisersKey(), queryFn: () => at_listAdvertisers(), ...options?.query });
}

export function useAt_listAdvertisersSuspense<TData = { data: AtAdvertiserOut[] }>(options?: { query?: Omit<UseSuspenseQueryOptions<{ data: AtAdvertiserOut[] }, ApiError, TData>, "queryKey" | "queryFn"> }) {
  return useSuspenseQuery({ queryKey: at_listAdvertisersKey(), queryFn: () => at_listAdvertisers(), ...options?.query });
}

export const at_listAnomalies = async (params?: At_listAnomaliesParams, options?: RequestInit): Promise<{ data: AtAnomalyOut[] }> => {
  const searchParams = new URLSearchParams();
  if (params?.status != null) searchParams.set("status", String(params?.status));
  if (params?.severity != null) searchParams.set("severity", String(params?.severity));
  if (params?.anomaly_type != null) searchParams.set("anomaly_type", String(params?.anomaly_type));
  if (params?.campaign_id != null) searchParams.set("campaign_id", String(params?.campaign_id));
  if (params?.limit != null) searchParams.set("limit", String(params?.limit));
  if (params?.offset != null) searchParams.set("offset", String(params?.offset));
  const queryString = searchParams.toString();
  const url = queryString ? `/api/projects/adtech-intelligence/anomalies?${queryString}` : `/api/projects/adtech-intelligence/anomalies`;
  const res = await fetch(url, { ...options, method: "GET" });
  if (!res.ok) {
    const body = await res.text();
    let parsed: unknown;
    try { parsed = JSON.parse(body); } catch { parsed = body; }
    throw new ApiError(res.status, res.statusText, parsed);
  }
  return { data: await res.json() };
};

export const at_listAnomaliesKey = (params?: At_listAnomaliesParams) => {
  return ["/api/projects/adtech-intelligence/anomalies", params] as const;
};

export function useAt_listAnomalies<TData = { data: AtAnomalyOut[] }>(options?: { params?: At_listAnomaliesParams; query?: Omit<UseQueryOptions<{ data: AtAnomalyOut[] }, ApiError, TData>, "queryKey" | "queryFn"> }) {
  return useQuery({ queryKey: at_listAnomaliesKey(options?.params), queryFn: () => at_listAnomalies(options?.params), ...options?.query });
}

export function useAt_listAnomaliesSuspense<TData = { data: AtAnomalyOut[] }>(options?: { params?: At_listAnomaliesParams; query?: Omit<UseSuspenseQueryOptions<{ data: AtAnomalyOut[] }, ApiError, TData>, "queryKey" | "queryFn"> }) {
  return useSuspenseQuery({ queryKey: at_listAnomaliesKey(options?.params), queryFn: () => at_listAnomalies(options?.params), ...options?.query });
}

export const at_getAnomalyCounts = async (options?: RequestInit): Promise<{ data: unknown }> => {
  const res = await fetch("/api/projects/adtech-intelligence/anomalies/counts", { ...options, method: "GET" });
  if (!res.ok) {
    const body = await res.text();
    let parsed: unknown;
    try { parsed = JSON.parse(body); } catch { parsed = body; }
    throw new ApiError(res.status, res.statusText, parsed);
  }
  return { data: await res.json() };
};

export const at_getAnomalyCountsKey = () => {
  return ["/api/projects/adtech-intelligence/anomalies/counts"] as const;
};

export function useAt_getAnomalyCounts<TData = { data: unknown }>(options?: { query?: Omit<UseQueryOptions<{ data: unknown }, ApiError, TData>, "queryKey" | "queryFn"> }) {
  return useQuery({ queryKey: at_getAnomalyCountsKey(), queryFn: () => at_getAnomalyCounts(), ...options?.query });
}

export function useAt_getAnomalyCountsSuspense<TData = { data: unknown }>(options?: { query?: Omit<UseSuspenseQueryOptions<{ data: unknown }, ApiError, TData>, "queryKey" | "queryFn"> }) {
  return useSuspenseQuery({ queryKey: at_getAnomalyCountsKey(), queryFn: () => at_getAnomalyCounts(), ...options?.query });
}

export const at_getAnomaly = async (params: At_getAnomalyParams, options?: RequestInit): Promise<{ data: AtAnomalyOut }> => {
  const res = await fetch(`/api/projects/adtech-intelligence/anomalies/${params.anomaly_id}`, { ...options, method: "GET" });
  if (!res.ok) {
    const body = await res.text();
    let parsed: unknown;
    try { parsed = JSON.parse(body); } catch { parsed = body; }
    throw new ApiError(res.status, res.statusText, parsed);
  }
  return { data: await res.json() };
};

export const at_getAnomalyKey = (params?: At_getAnomalyParams) => {
  return ["/api/projects/adtech-intelligence/anomalies/{anomaly_id}", params] as const;
};

export function useAt_getAnomaly<TData = { data: AtAnomalyOut }>(options: { params: At_getAnomalyParams; query?: Omit<UseQueryOptions<{ data: AtAnomalyOut }, ApiError, TData>, "queryKey" | "queryFn"> }) {
  return useQuery({ queryKey: at_getAnomalyKey(options.params), queryFn: () => at_getAnomaly(options.params), ...options?.query });
}

export function useAt_getAnomalySuspense<TData = { data: AtAnomalyOut }>(options: { params: At_getAnomalyParams; query?: Omit<UseSuspenseQueryOptions<{ data: AtAnomalyOut }, ApiError, TData>, "queryKey" | "queryFn"> }) {
  return useSuspenseQuery({ queryKey: at_getAnomalyKey(options.params), queryFn: () => at_getAnomaly(options.params), ...options?.query });
}

export const at_updateAnomaly = async (params: At_updateAnomalyParams, data: AtAnomalyUpdate, options?: RequestInit): Promise<{ data: AtAnomalyOut }> => {
  const res = await fetch(`/api/projects/adtech-intelligence/anomalies/${params.anomaly_id}`, { ...options, method: "PATCH", headers: { "Content-Type": "application/json", ...options?.headers }, body: JSON.stringify(data) });
  if (!res.ok) {
    const body = await res.text();
    let parsed: unknown;
    try { parsed = JSON.parse(body); } catch { parsed = body; }
    throw new ApiError(res.status, res.statusText, parsed);
  }
  return { data: await res.json() };
};

export function useAt_updateAnomaly(options?: { mutation?: UseMutationOptions<{ data: AtAnomalyOut }, ApiError, { params: At_updateAnomalyParams; data: AtAnomalyUpdate }> }) {
  return useMutation({ mutationFn: (vars) => at_updateAnomaly(vars.params, vars.data), ...options?.mutation });
}

export const at_listAnomalyRules = async (options?: RequestInit): Promise<{ data: AtAnomalyRuleOut[] }> => {
  const res = await fetch("/api/projects/adtech-intelligence/anomaly-rules", { ...options, method: "GET" });
  if (!res.ok) {
    const body = await res.text();
    let parsed: unknown;
    try { parsed = JSON.parse(body); } catch { parsed = body; }
    throw new ApiError(res.status, res.statusText, parsed);
  }
  return { data: await res.json() };
};

export const at_listAnomalyRulesKey = () => {
  return ["/api/projects/adtech-intelligence/anomaly-rules"] as const;
};

export function useAt_listAnomalyRules<TData = { data: AtAnomalyRuleOut[] }>(options?: { query?: Omit<UseQueryOptions<{ data: AtAnomalyRuleOut[] }, ApiError, TData>, "queryKey" | "queryFn"> }) {
  return useQuery({ queryKey: at_listAnomalyRulesKey(), queryFn: () => at_listAnomalyRules(), ...options?.query });
}

export function useAt_listAnomalyRulesSuspense<TData = { data: AtAnomalyRuleOut[] }>(options?: { query?: Omit<UseSuspenseQueryOptions<{ data: AtAnomalyRuleOut[] }, ApiError, TData>, "queryKey" | "queryFn"> }) {
  return useSuspenseQuery({ queryKey: at_listAnomalyRulesKey(), queryFn: () => at_listAnomalyRules(), ...options?.query });
}

export const at_listCampaigns = async (params?: At_listCampaignsParams, options?: RequestInit): Promise<{ data: AtCampaignOut[] }> => {
  const searchParams = new URLSearchParams();
  if (params?.status != null) searchParams.set("status", String(params?.status));
  if (params?.campaign_type != null) searchParams.set("campaign_type", String(params?.campaign_type));
  if (params?.advertiser_id != null) searchParams.set("advertiser_id", String(params?.advertiser_id));
  if (params?.limit != null) searchParams.set("limit", String(params?.limit));
  if (params?.offset != null) searchParams.set("offset", String(params?.offset));
  const queryString = searchParams.toString();
  const url = queryString ? `/api/projects/adtech-intelligence/campaigns?${queryString}` : `/api/projects/adtech-intelligence/campaigns`;
  const res = await fetch(url, { ...options, method: "GET" });
  if (!res.ok) {
    const body = await res.text();
    let parsed: unknown;
    try { parsed = JSON.parse(body); } catch { parsed = body; }
    throw new ApiError(res.status, res.statusText, parsed);
  }
  return { data: await res.json() };
};

export const at_listCampaignsKey = (params?: At_listCampaignsParams) => {
  return ["/api/projects/adtech-intelligence/campaigns", params] as const;
};

export function useAt_listCampaigns<TData = { data: AtCampaignOut[] }>(options?: { params?: At_listCampaignsParams; query?: Omit<UseQueryOptions<{ data: AtCampaignOut[] }, ApiError, TData>, "queryKey" | "queryFn"> }) {
  return useQuery({ queryKey: at_listCampaignsKey(options?.params), queryFn: () => at_listCampaigns(options?.params), ...options?.query });
}

export function useAt_listCampaignsSuspense<TData = { data: AtCampaignOut[] }>(options?: { params?: At_listCampaignsParams; query?: Omit<UseSuspenseQueryOptions<{ data: AtCampaignOut[] }, ApiError, TData>, "queryKey" | "queryFn"> }) {
  return useSuspenseQuery({ queryKey: at_listCampaignsKey(options?.params), queryFn: () => at_listCampaigns(options?.params), ...options?.query });
}

export const at_getCampaign = async (params: At_getCampaignParams, options?: RequestInit): Promise<{ data: AtCampaignOut }> => {
  const res = await fetch(`/api/projects/adtech-intelligence/campaigns/${params.campaign_id}`, { ...options, method: "GET" });
  if (!res.ok) {
    const body = await res.text();
    let parsed: unknown;
    try { parsed = JSON.parse(body); } catch { parsed = body; }
    throw new ApiError(res.status, res.statusText, parsed);
  }
  return { data: await res.json() };
};

export const at_getCampaignKey = (params?: At_getCampaignParams) => {
  return ["/api/projects/adtech-intelligence/campaigns/{campaign_id}", params] as const;
};

export function useAt_getCampaign<TData = { data: AtCampaignOut }>(options: { params: At_getCampaignParams; query?: Omit<UseQueryOptions<{ data: AtCampaignOut }, ApiError, TData>, "queryKey" | "queryFn"> }) {
  return useQuery({ queryKey: at_getCampaignKey(options.params), queryFn: () => at_getCampaign(options.params), ...options?.query });
}

export function useAt_getCampaignSuspense<TData = { data: AtCampaignOut }>(options: { params: At_getCampaignParams; query?: Omit<UseSuspenseQueryOptions<{ data: AtCampaignOut }, ApiError, TData>, "queryKey" | "queryFn"> }) {
  return useSuspenseQuery({ queryKey: at_getCampaignKey(options.params), queryFn: () => at_getCampaign(options.params), ...options?.query });
}

export const at_updateCampaign = async (params: At_updateCampaignParams, data: AtCampaignUpdate, options?: RequestInit): Promise<{ data: AtCampaignOut }> => {
  const res = await fetch(`/api/projects/adtech-intelligence/campaigns/${params.campaign_id}`, { ...options, method: "PATCH", headers: { "Content-Type": "application/json", ...options?.headers }, body: JSON.stringify(data) });
  if (!res.ok) {
    const body = await res.text();
    let parsed: unknown;
    try { parsed = JSON.parse(body); } catch { parsed = body; }
    throw new ApiError(res.status, res.statusText, parsed);
  }
  return { data: await res.json() };
};

export function useAt_updateCampaign(options?: { mutation?: UseMutationOptions<{ data: AtCampaignOut }, ApiError, { params: At_updateCampaignParams; data: AtCampaignUpdate }> }) {
  return useMutation({ mutationFn: (vars) => at_updateCampaign(vars.params, vars.data), ...options?.mutation });
}

export const at_listPlacements = async (params: At_listPlacementsParams, options?: RequestInit): Promise<{ data: AtPlacementOut[] }> => {
  const res = await fetch(`/api/projects/adtech-intelligence/campaigns/${params.campaign_id}/placements`, { ...options, method: "GET" });
  if (!res.ok) {
    const body = await res.text();
    let parsed: unknown;
    try { parsed = JSON.parse(body); } catch { parsed = body; }
    throw new ApiError(res.status, res.statusText, parsed);
  }
  return { data: await res.json() };
};

export const at_listPlacementsKey = (params?: At_listPlacementsParams) => {
  return ["/api/projects/adtech-intelligence/campaigns/{campaign_id}/placements", params] as const;
};

export function useAt_listPlacements<TData = { data: AtPlacementOut[] }>(options: { params: At_listPlacementsParams; query?: Omit<UseQueryOptions<{ data: AtPlacementOut[] }, ApiError, TData>, "queryKey" | "queryFn"> }) {
  return useQuery({ queryKey: at_listPlacementsKey(options.params), queryFn: () => at_listPlacements(options.params), ...options?.query });
}

export function useAt_listPlacementsSuspense<TData = { data: AtPlacementOut[] }>(options: { params: At_listPlacementsParams; query?: Omit<UseSuspenseQueryOptions<{ data: AtPlacementOut[] }, ApiError, TData>, "queryKey" | "queryFn"> }) {
  return useSuspenseQuery({ queryKey: at_listPlacementsKey(options.params), queryFn: () => at_listPlacements(options.params), ...options?.query });
}

export const at_sendChatMessage = async (data: AtChatMessageIn, options?: RequestInit): Promise<{ data: unknown }> => {
  const res = await fetch("/api/projects/adtech-intelligence/chat", { ...options, method: "POST", headers: { "Content-Type": "application/json", ...options?.headers }, body: JSON.stringify(data) });
  if (!res.ok) {
    const body = await res.text();
    let parsed: unknown;
    try { parsed = JSON.parse(body); } catch { parsed = body; }
    throw new ApiError(res.status, res.statusText, parsed);
  }
  return { data: await res.json() };
};

export function useAt_sendChatMessage(options?: { mutation?: UseMutationOptions<{ data: unknown }, ApiError, AtChatMessageIn> }) {
  return useMutation({ mutationFn: (data) => at_sendChatMessage(data), ...options?.mutation });
}

export const at_listChatSessions = async (options?: RequestInit): Promise<{ data: AtChatHistoryOut[] }> => {
  const res = await fetch("/api/projects/adtech-intelligence/chat/sessions", { ...options, method: "GET" });
  if (!res.ok) {
    const body = await res.text();
    let parsed: unknown;
    try { parsed = JSON.parse(body); } catch { parsed = body; }
    throw new ApiError(res.status, res.statusText, parsed);
  }
  return { data: await res.json() };
};

export const at_listChatSessionsKey = () => {
  return ["/api/projects/adtech-intelligence/chat/sessions"] as const;
};

export function useAt_listChatSessions<TData = { data: AtChatHistoryOut[] }>(options?: { query?: Omit<UseQueryOptions<{ data: AtChatHistoryOut[] }, ApiError, TData>, "queryKey" | "queryFn"> }) {
  return useQuery({ queryKey: at_listChatSessionsKey(), queryFn: () => at_listChatSessions(), ...options?.query });
}

export function useAt_listChatSessionsSuspense<TData = { data: AtChatHistoryOut[] }>(options?: { query?: Omit<UseSuspenseQueryOptions<{ data: AtChatHistoryOut[] }, ApiError, TData>, "queryKey" | "queryFn"> }) {
  return useSuspenseQuery({ queryKey: at_listChatSessionsKey(), queryFn: () => at_listChatSessions(), ...options?.query });
}

export const at_getChatSession = async (params: At_getChatSessionParams, options?: RequestInit): Promise<{ data: AtChatHistoryOut }> => {
  const res = await fetch(`/api/projects/adtech-intelligence/chat/sessions/${params.session_id}`, { ...options, method: "GET" });
  if (!res.ok) {
    const body = await res.text();
    let parsed: unknown;
    try { parsed = JSON.parse(body); } catch { parsed = body; }
    throw new ApiError(res.status, res.statusText, parsed);
  }
  return { data: await res.json() };
};

export const at_getChatSessionKey = (params?: At_getChatSessionParams) => {
  return ["/api/projects/adtech-intelligence/chat/sessions/{session_id}", params] as const;
};

export function useAt_getChatSession<TData = { data: AtChatHistoryOut }>(options: { params: At_getChatSessionParams; query?: Omit<UseQueryOptions<{ data: AtChatHistoryOut }, ApiError, TData>, "queryKey" | "queryFn"> }) {
  return useQuery({ queryKey: at_getChatSessionKey(options.params), queryFn: () => at_getChatSession(options.params), ...options?.query });
}

export function useAt_getChatSessionSuspense<TData = { data: AtChatHistoryOut }>(options: { params: At_getChatSessionParams; query?: Omit<UseSuspenseQueryOptions<{ data: AtChatHistoryOut }, ApiError, TData>, "queryKey" | "queryFn"> }) {
  return useSuspenseQuery({ queryKey: at_getChatSessionKey(options.params), queryFn: () => at_getChatSession(options.params), ...options?.query });
}

export const at_listContracts = async (params?: At_listContractsParams, options?: RequestInit): Promise<{ data: AtCustomerContractOut[] }> => {
  const searchParams = new URLSearchParams();
  if (params?.advertiser_id != null) searchParams.set("advertiser_id", String(params?.advertiser_id));
  const queryString = searchParams.toString();
  const url = queryString ? `/api/projects/adtech-intelligence/contracts?${queryString}` : `/api/projects/adtech-intelligence/contracts`;
  const res = await fetch(url, { ...options, method: "GET" });
  if (!res.ok) {
    const body = await res.text();
    let parsed: unknown;
    try { parsed = JSON.parse(body); } catch { parsed = body; }
    throw new ApiError(res.status, res.statusText, parsed);
  }
  return { data: await res.json() };
};

export const at_listContractsKey = (params?: At_listContractsParams) => {
  return ["/api/projects/adtech-intelligence/contracts", params] as const;
};

export function useAt_listContracts<TData = { data: AtCustomerContractOut[] }>(options?: { params?: At_listContractsParams; query?: Omit<UseQueryOptions<{ data: AtCustomerContractOut[] }, ApiError, TData>, "queryKey" | "queryFn"> }) {
  return useQuery({ queryKey: at_listContractsKey(options?.params), queryFn: () => at_listContracts(options?.params), ...options?.query });
}

export function useAt_listContractsSuspense<TData = { data: AtCustomerContractOut[] }>(options?: { params?: At_listContractsParams; query?: Omit<UseSuspenseQueryOptions<{ data: AtCustomerContractOut[] }, ApiError, TData>, "queryKey" | "queryFn"> }) {
  return useSuspenseQuery({ queryKey: at_listContractsKey(options?.params), queryFn: () => at_listContracts(options?.params), ...options?.query });
}

export const at_getDashboardSummary = async (options?: RequestInit): Promise<{ data: AtDashboardSummaryOut }> => {
  const res = await fetch("/api/projects/adtech-intelligence/dashboard/summary", { ...options, method: "GET" });
  if (!res.ok) {
    const body = await res.text();
    let parsed: unknown;
    try { parsed = JSON.parse(body); } catch { parsed = body; }
    throw new ApiError(res.status, res.statusText, parsed);
  }
  return { data: await res.json() };
};

export const at_getDashboardSummaryKey = () => {
  return ["/api/projects/adtech-intelligence/dashboard/summary"] as const;
};

export function useAt_getDashboardSummary<TData = { data: AtDashboardSummaryOut }>(options?: { query?: Omit<UseQueryOptions<{ data: AtDashboardSummaryOut }, ApiError, TData>, "queryKey" | "queryFn"> }) {
  return useQuery({ queryKey: at_getDashboardSummaryKey(), queryFn: () => at_getDashboardSummary(), ...options?.query });
}

export function useAt_getDashboardSummarySuspense<TData = { data: AtDashboardSummaryOut }>(options?: { query?: Omit<UseSuspenseQueryOptions<{ data: AtDashboardSummaryOut }, ApiError, TData>, "queryKey" | "queryFn"> }) {
  return useSuspenseQuery({ queryKey: at_getDashboardSummaryKey(), queryFn: () => at_getDashboardSummary(), ...options?.query });
}

export const at_getDatabricksResources = async (options?: RequestInit): Promise<{ data: DatabricksResourcesOut }> => {
  const res = await fetch("/api/projects/adtech-intelligence/databricks-resources", { ...options, method: "GET" });
  if (!res.ok) {
    const body = await res.text();
    let parsed: unknown;
    try { parsed = JSON.parse(body); } catch { parsed = body; }
    throw new ApiError(res.status, res.statusText, parsed);
  }
  return { data: await res.json() };
};

export const at_getDatabricksResourcesKey = () => {
  return ["/api/projects/adtech-intelligence/databricks-resources"] as const;
};

export function useAt_getDatabricksResources<TData = { data: DatabricksResourcesOut }>(options?: { query?: Omit<UseQueryOptions<{ data: DatabricksResourcesOut }, ApiError, TData>, "queryKey" | "queryFn"> }) {
  return useQuery({ queryKey: at_getDatabricksResourcesKey(), queryFn: () => at_getDatabricksResources(), ...options?.query });
}

export function useAt_getDatabricksResourcesSuspense<TData = { data: DatabricksResourcesOut }>(options?: { query?: Omit<UseSuspenseQueryOptions<{ data: DatabricksResourcesOut }, ApiError, TData>, "queryKey" | "queryFn"> }) {
  return useSuspenseQuery({ queryKey: at_getDatabricksResourcesKey(), queryFn: () => at_getDatabricksResources(), ...options?.query });
}

export const at_listInventory = async (params?: At_listInventoryParams, options?: RequestInit): Promise<{ data: AtAdInventoryOut[] }> => {
  const searchParams = new URLSearchParams();
  if (params?.inventory_type != null) searchParams.set("inventory_type", String(params?.inventory_type));
  if (params?.location_type != null) searchParams.set("location_type", String(params?.location_type));
  if (params?.status != null) searchParams.set("status", String(params?.status));
  if (params?.city != null) searchParams.set("city", String(params?.city));
  if (params?.limit != null) searchParams.set("limit", String(params?.limit));
  if (params?.offset != null) searchParams.set("offset", String(params?.offset));
  const queryString = searchParams.toString();
  const url = queryString ? `/api/projects/adtech-intelligence/inventory?${queryString}` : `/api/projects/adtech-intelligence/inventory`;
  const res = await fetch(url, { ...options, method: "GET" });
  if (!res.ok) {
    const body = await res.text();
    let parsed: unknown;
    try { parsed = JSON.parse(body); } catch { parsed = body; }
    throw new ApiError(res.status, res.statusText, parsed);
  }
  return { data: await res.json() };
};

export const at_listInventoryKey = (params?: At_listInventoryParams) => {
  return ["/api/projects/adtech-intelligence/inventory", params] as const;
};

export function useAt_listInventory<TData = { data: AtAdInventoryOut[] }>(options?: { params?: At_listInventoryParams; query?: Omit<UseQueryOptions<{ data: AtAdInventoryOut[] }, ApiError, TData>, "queryKey" | "queryFn"> }) {
  return useQuery({ queryKey: at_listInventoryKey(options?.params), queryFn: () => at_listInventory(options?.params), ...options?.query });
}

export function useAt_listInventorySuspense<TData = { data: AtAdInventoryOut[] }>(options?: { params?: At_listInventoryParams; query?: Omit<UseSuspenseQueryOptions<{ data: AtAdInventoryOut[] }, ApiError, TData>, "queryKey" | "queryFn"> }) {
  return useSuspenseQuery({ queryKey: at_listInventoryKey(options?.params), queryFn: () => at_listInventory(options?.params), ...options?.query });
}

export const at_getInventoryItem = async (params: At_getInventoryItemParams, options?: RequestInit): Promise<{ data: AtAdInventoryOut }> => {
  const res = await fetch(`/api/projects/adtech-intelligence/inventory/${params.inventory_id}`, { ...options, method: "GET" });
  if (!res.ok) {
    const body = await res.text();
    let parsed: unknown;
    try { parsed = JSON.parse(body); } catch { parsed = body; }
    throw new ApiError(res.status, res.statusText, parsed);
  }
  return { data: await res.json() };
};

export const at_getInventoryItemKey = (params?: At_getInventoryItemParams) => {
  return ["/api/projects/adtech-intelligence/inventory/{inventory_id}", params] as const;
};

export function useAt_getInventoryItem<TData = { data: AtAdInventoryOut }>(options: { params: At_getInventoryItemParams; query?: Omit<UseQueryOptions<{ data: AtAdInventoryOut }, ApiError, TData>, "queryKey" | "queryFn"> }) {
  return useQuery({ queryKey: at_getInventoryItemKey(options.params), queryFn: () => at_getInventoryItem(options.params), ...options?.query });
}

export function useAt_getInventoryItemSuspense<TData = { data: AtAdInventoryOut }>(options: { params: At_getInventoryItemParams; query?: Omit<UseSuspenseQueryOptions<{ data: AtAdInventoryOut }, ApiError, TData>, "queryKey" | "queryFn"> }) {
  return useSuspenseQuery({ queryKey: at_getInventoryItemKey(options.params), queryFn: () => at_getInventoryItem(options.params), ...options?.query });
}

export const at_listIssues = async (params?: At_listIssuesParams, options?: RequestInit): Promise<{ data: AtIssueOut[] }> => {
  const searchParams = new URLSearchParams();
  if (params?.status != null) searchParams.set("status", String(params?.status));
  if (params?.priority != null) searchParams.set("priority", String(params?.priority));
  if (params?.category != null) searchParams.set("category", String(params?.category));
  if (params?.campaign_id != null) searchParams.set("campaign_id", String(params?.campaign_id));
  if (params?.limit != null) searchParams.set("limit", String(params?.limit));
  if (params?.offset != null) searchParams.set("offset", String(params?.offset));
  const queryString = searchParams.toString();
  const url = queryString ? `/api/projects/adtech-intelligence/issues?${queryString}` : `/api/projects/adtech-intelligence/issues`;
  const res = await fetch(url, { ...options, method: "GET" });
  if (!res.ok) {
    const body = await res.text();
    let parsed: unknown;
    try { parsed = JSON.parse(body); } catch { parsed = body; }
    throw new ApiError(res.status, res.statusText, parsed);
  }
  return { data: await res.json() };
};

export const at_listIssuesKey = (params?: At_listIssuesParams) => {
  return ["/api/projects/adtech-intelligence/issues", params] as const;
};

export function useAt_listIssues<TData = { data: AtIssueOut[] }>(options?: { params?: At_listIssuesParams; query?: Omit<UseQueryOptions<{ data: AtIssueOut[] }, ApiError, TData>, "queryKey" | "queryFn"> }) {
  return useQuery({ queryKey: at_listIssuesKey(options?.params), queryFn: () => at_listIssues(options?.params), ...options?.query });
}

export function useAt_listIssuesSuspense<TData = { data: AtIssueOut[] }>(options?: { params?: At_listIssuesParams; query?: Omit<UseSuspenseQueryOptions<{ data: AtIssueOut[] }, ApiError, TData>, "queryKey" | "queryFn"> }) {
  return useSuspenseQuery({ queryKey: at_listIssuesKey(options?.params), queryFn: () => at_listIssues(options?.params), ...options?.query });
}

export const at_getIssue = async (params: At_getIssueParams, options?: RequestInit): Promise<{ data: AtIssueOut }> => {
  const res = await fetch(`/api/projects/adtech-intelligence/issues/${params.issue_id}`, { ...options, method: "GET" });
  if (!res.ok) {
    const body = await res.text();
    let parsed: unknown;
    try { parsed = JSON.parse(body); } catch { parsed = body; }
    throw new ApiError(res.status, res.statusText, parsed);
  }
  return { data: await res.json() };
};

export const at_getIssueKey = (params?: At_getIssueParams) => {
  return ["/api/projects/adtech-intelligence/issues/{issue_id}", params] as const;
};

export function useAt_getIssue<TData = { data: AtIssueOut }>(options: { params: At_getIssueParams; query?: Omit<UseQueryOptions<{ data: AtIssueOut }, ApiError, TData>, "queryKey" | "queryFn"> }) {
  return useQuery({ queryKey: at_getIssueKey(options.params), queryFn: () => at_getIssue(options.params), ...options?.query });
}

export function useAt_getIssueSuspense<TData = { data: AtIssueOut }>(options: { params: At_getIssueParams; query?: Omit<UseSuspenseQueryOptions<{ data: AtIssueOut }, ApiError, TData>, "queryKey" | "queryFn"> }) {
  return useSuspenseQuery({ queryKey: at_getIssueKey(options.params), queryFn: () => at_getIssue(options.params), ...options?.query });
}

export const at_updateIssue = async (params: At_updateIssueParams, data: AtIssueUpdate, options?: RequestInit): Promise<{ data: AtIssueOut }> => {
  const res = await fetch(`/api/projects/adtech-intelligence/issues/${params.issue_id}`, { ...options, method: "PATCH", headers: { "Content-Type": "application/json", ...options?.headers }, body: JSON.stringify(data) });
  if (!res.ok) {
    const body = await res.text();
    let parsed: unknown;
    try { parsed = JSON.parse(body); } catch { parsed = body; }
    throw new ApiError(res.status, res.statusText, parsed);
  }
  return { data: await res.json() };
};

export function useAt_updateIssue(options?: { mutation?: UseMutationOptions<{ data: AtIssueOut }, ApiError, { params: At_updateIssueParams; data: AtIssueUpdate }> }) {
  return useMutation({ mutationFn: (vars) => at_updateIssue(vars.params, vars.data), ...options?.mutation });
}

export const at_sendMasChatMessage = async (data: AtChatMessageIn, options?: RequestInit): Promise<{ data: unknown }> => {
  const res = await fetch("/api/projects/adtech-intelligence/mas-chat", { ...options, method: "POST", headers: { "Content-Type": "application/json", ...options?.headers }, body: JSON.stringify(data) });
  if (!res.ok) {
    const body = await res.text();
    let parsed: unknown;
    try { parsed = JSON.parse(body); } catch { parsed = body; }
    throw new ApiError(res.status, res.statusText, parsed);
  }
  return { data: await res.json() };
};

export function useAt_sendMasChatMessage(options?: { mutation?: UseMutationOptions<{ data: unknown }, ApiError, AtChatMessageIn> }) {
  return useMutation({ mutationFn: (data) => at_sendMasChatMessage(data), ...options?.mutation });
}

export const at_getPlacement = async (params: At_getPlacementParams, options?: RequestInit): Promise<{ data: AtPlacementOut }> => {
  const res = await fetch(`/api/projects/adtech-intelligence/placements/${params.placement_id}`, { ...options, method: "GET" });
  if (!res.ok) {
    const body = await res.text();
    let parsed: unknown;
    try { parsed = JSON.parse(body); } catch { parsed = body; }
    throw new ApiError(res.status, res.statusText, parsed);
  }
  return { data: await res.json() };
};

export const at_getPlacementKey = (params?: At_getPlacementParams) => {
  return ["/api/projects/adtech-intelligence/placements/{placement_id}", params] as const;
};

export function useAt_getPlacement<TData = { data: AtPlacementOut }>(options: { params: At_getPlacementParams; query?: Omit<UseQueryOptions<{ data: AtPlacementOut }, ApiError, TData>, "queryKey" | "queryFn"> }) {
  return useQuery({ queryKey: at_getPlacementKey(options.params), queryFn: () => at_getPlacement(options.params), ...options?.query });
}

export function useAt_getPlacementSuspense<TData = { data: AtPlacementOut }>(options: { params: At_getPlacementParams; query?: Omit<UseSuspenseQueryOptions<{ data: AtPlacementOut }, ApiError, TData>, "queryKey" | "queryFn"> }) {
  return useSuspenseQuery({ queryKey: at_getPlacementKey(options.params), queryFn: () => at_getPlacement(options.params), ...options?.query });
}

export const bsh_getCurrentCustomer = async (params?: Bsh_getCurrentCustomerParams, options?: RequestInit): Promise<{ data: BshCustomerOut }> => {
  const res = await fetch("/api/projects/bsh-home-connect/customers/me", { ...options, method: "GET", headers: { ...(params?.["X-Forwarded-Access-Token"] != null && { "X-Forwarded-Access-Token": params["X-Forwarded-Access-Token"] }), ...options?.headers } });
  if (!res.ok) {
    const body = await res.text();
    let parsed: unknown;
    try { parsed = JSON.parse(body); } catch { parsed = body; }
    throw new ApiError(res.status, res.statusText, parsed);
  }
  return { data: await res.json() };
};

export const bsh_getCurrentCustomerKey = (params?: Bsh_getCurrentCustomerParams) => {
  return ["/api/projects/bsh-home-connect/customers/me", params] as const;
};

export function useBsh_getCurrentCustomer<TData = { data: BshCustomerOut }>(options?: { params?: Bsh_getCurrentCustomerParams; query?: Omit<UseQueryOptions<{ data: BshCustomerOut }, ApiError, TData>, "queryKey" | "queryFn"> }) {
  return useQuery({ queryKey: bsh_getCurrentCustomerKey(options?.params), queryFn: () => bsh_getCurrentCustomer(options?.params), ...options?.query });
}

export function useBsh_getCurrentCustomerSuspense<TData = { data: BshCustomerOut }>(options?: { params?: Bsh_getCurrentCustomerParams; query?: Omit<UseSuspenseQueryOptions<{ data: BshCustomerOut }, ApiError, TData>, "queryKey" | "queryFn"> }) {
  return useSuspenseQuery({ queryKey: bsh_getCurrentCustomerKey(options?.params), queryFn: () => bsh_getCurrentCustomer(options?.params), ...options?.query });
}

export const bsh_updateCurrentCustomer = async (data: BshCustomerIn, params?: Bsh_updateCurrentCustomerParams, options?: RequestInit): Promise<{ data: BshCustomerOut }> => {
  const res = await fetch("/api/projects/bsh-home-connect/customers/me", { ...options, method: "PUT", headers: { "Content-Type": "application/json", ...(params?.["X-Forwarded-Access-Token"] != null && { "X-Forwarded-Access-Token": params["X-Forwarded-Access-Token"] }), ...options?.headers }, body: JSON.stringify(data) });
  if (!res.ok) {
    const body = await res.text();
    let parsed: unknown;
    try { parsed = JSON.parse(body); } catch { parsed = body; }
    throw new ApiError(res.status, res.statusText, parsed);
  }
  return { data: await res.json() };
};

export function useBsh_updateCurrentCustomer(options?: { mutation?: UseMutationOptions<{ data: BshCustomerOut }, ApiError, { params: Bsh_updateCurrentCustomerParams; data: BshCustomerIn }> }) {
  return useMutation({ mutationFn: (vars) => bsh_updateCurrentCustomer(vars.data, vars.params), ...options?.mutation });
}

export const bsh_listMyDevices = async (params?: Bsh_listMyDevicesParams, options?: RequestInit): Promise<{ data: BshCustomerDeviceOut[] }> => {
  const res = await fetch("/api/projects/bsh-home-connect/customers/me/devices", { ...options, method: "GET", headers: { ...(params?.["X-Forwarded-Access-Token"] != null && { "X-Forwarded-Access-Token": params["X-Forwarded-Access-Token"] }), ...options?.headers } });
  if (!res.ok) {
    const body = await res.text();
    let parsed: unknown;
    try { parsed = JSON.parse(body); } catch { parsed = body; }
    throw new ApiError(res.status, res.statusText, parsed);
  }
  return { data: await res.json() };
};

export const bsh_listMyDevicesKey = (params?: Bsh_listMyDevicesParams) => {
  return ["/api/projects/bsh-home-connect/customers/me/devices", params] as const;
};

export function useBsh_listMyDevices<TData = { data: BshCustomerDeviceOut[] }>(options?: { params?: Bsh_listMyDevicesParams; query?: Omit<UseQueryOptions<{ data: BshCustomerDeviceOut[] }, ApiError, TData>, "queryKey" | "queryFn"> }) {
  return useQuery({ queryKey: bsh_listMyDevicesKey(options?.params), queryFn: () => bsh_listMyDevices(options?.params), ...options?.query });
}

export function useBsh_listMyDevicesSuspense<TData = { data: BshCustomerDeviceOut[] }>(options?: { params?: Bsh_listMyDevicesParams; query?: Omit<UseSuspenseQueryOptions<{ data: BshCustomerDeviceOut[] }, ApiError, TData>, "queryKey" | "queryFn"> }) {
  return useSuspenseQuery({ queryKey: bsh_listMyDevicesKey(options?.params), queryFn: () => bsh_listMyDevices(options?.params), ...options?.query });
}

export const bsh_registerDevice = async (data: BshCustomerDeviceIn, params?: Bsh_registerDeviceParams, options?: RequestInit): Promise<{ data: BshCustomerDeviceOut }> => {
  const res = await fetch("/api/projects/bsh-home-connect/customers/me/devices", { ...options, method: "POST", headers: { "Content-Type": "application/json", ...(params?.["X-Forwarded-Access-Token"] != null && { "X-Forwarded-Access-Token": params["X-Forwarded-Access-Token"] }), ...options?.headers }, body: JSON.stringify(data) });
  if (!res.ok) {
    const body = await res.text();
    let parsed: unknown;
    try { parsed = JSON.parse(body); } catch { parsed = body; }
    throw new ApiError(res.status, res.statusText, parsed);
  }
  return { data: await res.json() };
};

export function useBsh_registerDevice(options?: { mutation?: UseMutationOptions<{ data: BshCustomerDeviceOut }, ApiError, { params: Bsh_registerDeviceParams; data: BshCustomerDeviceIn }> }) {
  return useMutation({ mutationFn: (vars) => bsh_registerDevice(vars.data, vars.params), ...options?.mutation });
}

export const bsh_getMyDevice = async (params: Bsh_getMyDeviceParams, options?: RequestInit): Promise<{ data: BshCustomerDeviceOut }> => {
  const res = await fetch(`/api/projects/bsh-home-connect/customers/me/devices/${params.device_id}`, { ...options, method: "GET", headers: { ...(params?.["X-Forwarded-Access-Token"] != null && { "X-Forwarded-Access-Token": params["X-Forwarded-Access-Token"] }), ...options?.headers } });
  if (!res.ok) {
    const body = await res.text();
    let parsed: unknown;
    try { parsed = JSON.parse(body); } catch { parsed = body; }
    throw new ApiError(res.status, res.statusText, parsed);
  }
  return { data: await res.json() };
};

export const bsh_getMyDeviceKey = (params?: Bsh_getMyDeviceParams) => {
  return ["/api/projects/bsh-home-connect/customers/me/devices/{device_id}", params] as const;
};

export function useBsh_getMyDevice<TData = { data: BshCustomerDeviceOut }>(options: { params: Bsh_getMyDeviceParams; query?: Omit<UseQueryOptions<{ data: BshCustomerDeviceOut }, ApiError, TData>, "queryKey" | "queryFn"> }) {
  return useQuery({ queryKey: bsh_getMyDeviceKey(options.params), queryFn: () => bsh_getMyDevice(options.params), ...options?.query });
}

export function useBsh_getMyDeviceSuspense<TData = { data: BshCustomerDeviceOut }>(options: { params: Bsh_getMyDeviceParams; query?: Omit<UseSuspenseQueryOptions<{ data: BshCustomerDeviceOut }, ApiError, TData>, "queryKey" | "queryFn"> }) {
  return useSuspenseQuery({ queryKey: bsh_getMyDeviceKey(options.params), queryFn: () => bsh_getMyDevice(options.params), ...options?.query });
}

export const bsh_listDevices = async (params?: Bsh_listDevicesParams, options?: RequestInit): Promise<{ data: BshDeviceOut[] }> => {
  const searchParams = new URLSearchParams();
  if (params?.category != null) searchParams.set("category", String(params?.category));
  const queryString = searchParams.toString();
  const url = queryString ? `/api/projects/bsh-home-connect/devices?${queryString}` : `/api/projects/bsh-home-connect/devices`;
  const res = await fetch(url, { ...options, method: "GET" });
  if (!res.ok) {
    const body = await res.text();
    let parsed: unknown;
    try { parsed = JSON.parse(body); } catch { parsed = body; }
    throw new ApiError(res.status, res.statusText, parsed);
  }
  return { data: await res.json() };
};

export const bsh_listDevicesKey = (params?: Bsh_listDevicesParams) => {
  return ["/api/projects/bsh-home-connect/devices", params] as const;
};

export function useBsh_listDevices<TData = { data: BshDeviceOut[] }>(options?: { params?: Bsh_listDevicesParams; query?: Omit<UseQueryOptions<{ data: BshDeviceOut[] }, ApiError, TData>, "queryKey" | "queryFn"> }) {
  return useQuery({ queryKey: bsh_listDevicesKey(options?.params), queryFn: () => bsh_listDevices(options?.params), ...options?.query });
}

export function useBsh_listDevicesSuspense<TData = { data: BshDeviceOut[] }>(options?: { params?: Bsh_listDevicesParams; query?: Omit<UseSuspenseQueryOptions<{ data: BshDeviceOut[] }, ApiError, TData>, "queryKey" | "queryFn"> }) {
  return useSuspenseQuery({ queryKey: bsh_listDevicesKey(options?.params), queryFn: () => bsh_listDevices(options?.params), ...options?.query });
}

export const bsh_getDeviceDocuments = async (params: Bsh_getDeviceDocumentsParams, options?: RequestInit): Promise<{ data: BshDocumentOut[] }> => {
  const res = await fetch(`/api/projects/bsh-home-connect/documents/${params.device_id}`, { ...options, method: "GET" });
  if (!res.ok) {
    const body = await res.text();
    let parsed: unknown;
    try { parsed = JSON.parse(body); } catch { parsed = body; }
    throw new ApiError(res.status, res.statusText, parsed);
  }
  return { data: await res.json() };
};

export const bsh_getDeviceDocumentsKey = (params?: Bsh_getDeviceDocumentsParams) => {
  return ["/api/projects/bsh-home-connect/documents/{device_id}", params] as const;
};

export function useBsh_getDeviceDocuments<TData = { data: BshDocumentOut[] }>(options: { params: Bsh_getDeviceDocumentsParams; query?: Omit<UseQueryOptions<{ data: BshDocumentOut[] }, ApiError, TData>, "queryKey" | "queryFn"> }) {
  return useQuery({ queryKey: bsh_getDeviceDocumentsKey(options.params), queryFn: () => bsh_getDeviceDocuments(options.params), ...options?.query });
}

export function useBsh_getDeviceDocumentsSuspense<TData = { data: BshDocumentOut[] }>(options: { params: Bsh_getDeviceDocumentsParams; query?: Omit<UseSuspenseQueryOptions<{ data: BshDocumentOut[] }, ApiError, TData>, "queryKey" | "queryFn"> }) {
  return useSuspenseQuery({ queryKey: bsh_getDeviceDocumentsKey(options.params), queryFn: () => bsh_getDeviceDocuments(options.params), ...options?.query });
}

export const bsh_getDeviceKnowledge = async (params: Bsh_getDeviceKnowledgeParams, options?: RequestInit): Promise<{ data: BshKnowledgeArticleOut[] }> => {
  const res = await fetch(`/api/projects/bsh-home-connect/knowledge/device/${params.device_id}`, { ...options, method: "GET" });
  if (!res.ok) {
    const body = await res.text();
    let parsed: unknown;
    try { parsed = JSON.parse(body); } catch { parsed = body; }
    throw new ApiError(res.status, res.statusText, parsed);
  }
  return { data: await res.json() };
};

export const bsh_getDeviceKnowledgeKey = (params?: Bsh_getDeviceKnowledgeParams) => {
  return ["/api/projects/bsh-home-connect/knowledge/device/{device_id}", params] as const;
};

export function useBsh_getDeviceKnowledge<TData = { data: BshKnowledgeArticleOut[] }>(options: { params: Bsh_getDeviceKnowledgeParams; query?: Omit<UseQueryOptions<{ data: BshKnowledgeArticleOut[] }, ApiError, TData>, "queryKey" | "queryFn"> }) {
  return useQuery({ queryKey: bsh_getDeviceKnowledgeKey(options.params), queryFn: () => bsh_getDeviceKnowledge(options.params), ...options?.query });
}

export function useBsh_getDeviceKnowledgeSuspense<TData = { data: BshKnowledgeArticleOut[] }>(options: { params: Bsh_getDeviceKnowledgeParams; query?: Omit<UseSuspenseQueryOptions<{ data: BshKnowledgeArticleOut[] }, ApiError, TData>, "queryKey" | "queryFn"> }) {
  return useSuspenseQuery({ queryKey: bsh_getDeviceKnowledgeKey(options.params), queryFn: () => bsh_getDeviceKnowledge(options.params), ...options?.query });
}

export const bsh_searchKnowledge = async (params: Bsh_searchKnowledgeParams, options?: RequestInit): Promise<{ data: BshKnowledgeArticleOut[] }> => {
  const searchParams = new URLSearchParams();
  if (params.query != null) searchParams.set("query", String(params.query));
  if (params?.category != null) searchParams.set("category", String(params?.category));
  if (params?.limit != null) searchParams.set("limit", String(params?.limit));
  const queryString = searchParams.toString();
  const url = queryString ? `/api/projects/bsh-home-connect/knowledge/search?${queryString}` : `/api/projects/bsh-home-connect/knowledge/search`;
  const res = await fetch(url, { ...options, method: "GET" });
  if (!res.ok) {
    const body = await res.text();
    let parsed: unknown;
    try { parsed = JSON.parse(body); } catch { parsed = body; }
    throw new ApiError(res.status, res.statusText, parsed);
  }
  return { data: await res.json() };
};

export const bsh_searchKnowledgeKey = (params?: Bsh_searchKnowledgeParams) => {
  return ["/api/projects/bsh-home-connect/knowledge/search", params] as const;
};

export function useBsh_searchKnowledge<TData = { data: BshKnowledgeArticleOut[] }>(options: { params: Bsh_searchKnowledgeParams; query?: Omit<UseQueryOptions<{ data: BshKnowledgeArticleOut[] }, ApiError, TData>, "queryKey" | "queryFn"> }) {
  return useQuery({ queryKey: bsh_searchKnowledgeKey(options.params), queryFn: () => bsh_searchKnowledge(options.params), ...options?.query });
}

export function useBsh_searchKnowledgeSuspense<TData = { data: BshKnowledgeArticleOut[] }>(options: { params: Bsh_searchKnowledgeParams; query?: Omit<UseSuspenseQueryOptions<{ data: BshKnowledgeArticleOut[] }, ApiError, TData>, "queryKey" | "queryFn"> }) {
  return useSuspenseQuery({ queryKey: bsh_searchKnowledgeKey(options.params), queryFn: () => bsh_searchKnowledge(options.params), ...options?.query });
}

export const bsh_getCurrentTechnician = async (params?: Bsh_getCurrentTechnicianParams, options?: RequestInit): Promise<{ data: BshTechnicianOut }> => {
  const res = await fetch("/api/projects/bsh-home-connect/technicians/me", { ...options, method: "GET", headers: { ...(params?.["X-Forwarded-Access-Token"] != null && { "X-Forwarded-Access-Token": params["X-Forwarded-Access-Token"] }), ...options?.headers } });
  if (!res.ok) {
    const body = await res.text();
    let parsed: unknown;
    try { parsed = JSON.parse(body); } catch { parsed = body; }
    throw new ApiError(res.status, res.statusText, parsed);
  }
  return { data: await res.json() };
};

export const bsh_getCurrentTechnicianKey = (params?: Bsh_getCurrentTechnicianParams) => {
  return ["/api/projects/bsh-home-connect/technicians/me", params] as const;
};

export function useBsh_getCurrentTechnician<TData = { data: BshTechnicianOut }>(options?: { params?: Bsh_getCurrentTechnicianParams; query?: Omit<UseQueryOptions<{ data: BshTechnicianOut }, ApiError, TData>, "queryKey" | "queryFn"> }) {
  return useQuery({ queryKey: bsh_getCurrentTechnicianKey(options?.params), queryFn: () => bsh_getCurrentTechnician(options?.params), ...options?.query });
}

export function useBsh_getCurrentTechnicianSuspense<TData = { data: BshTechnicianOut }>(options?: { params?: Bsh_getCurrentTechnicianParams; query?: Omit<UseSuspenseQueryOptions<{ data: BshTechnicianOut }, ApiError, TData>, "queryKey" | "queryFn"> }) {
  return useSuspenseQuery({ queryKey: bsh_getCurrentTechnicianKey(options?.params), queryFn: () => bsh_getCurrentTechnician(options?.params), ...options?.query });
}

export const bsh_getTechnician = async (params: Bsh_getTechnicianParams, options?: RequestInit): Promise<{ data: BshTechnicianOut }> => {
  const res = await fetch(`/api/projects/bsh-home-connect/technicians/${params.technician_id}`, { ...options, method: "GET" });
  if (!res.ok) {
    const body = await res.text();
    let parsed: unknown;
    try { parsed = JSON.parse(body); } catch { parsed = body; }
    throw new ApiError(res.status, res.statusText, parsed);
  }
  return { data: await res.json() };
};

export const bsh_getTechnicianKey = (params?: Bsh_getTechnicianParams) => {
  return ["/api/projects/bsh-home-connect/technicians/{technician_id}", params] as const;
};

export function useBsh_getTechnician<TData = { data: BshTechnicianOut }>(options: { params: Bsh_getTechnicianParams; query?: Omit<UseQueryOptions<{ data: BshTechnicianOut }, ApiError, TData>, "queryKey" | "queryFn"> }) {
  return useQuery({ queryKey: bsh_getTechnicianKey(options.params), queryFn: () => bsh_getTechnician(options.params), ...options?.query });
}

export function useBsh_getTechnicianSuspense<TData = { data: BshTechnicianOut }>(options: { params: Bsh_getTechnicianParams; query?: Omit<UseSuspenseQueryOptions<{ data: BshTechnicianOut }, ApiError, TData>, "queryKey" | "queryFn"> }) {
  return useSuspenseQuery({ queryKey: bsh_getTechnicianKey(options.params), queryFn: () => bsh_getTechnician(options.params), ...options?.query });
}

export const bsh_listTickets = async (params?: Bsh_listTicketsParams, options?: RequestInit): Promise<{ data: BshTicketOut[] }> => {
  const searchParams = new URLSearchParams();
  if (params?.status != null) searchParams.set("status", String(params?.status));
  if (params?.role != null) searchParams.set("role", String(params?.role));
  const queryString = searchParams.toString();
  const url = queryString ? `/api/projects/bsh-home-connect/tickets?${queryString}` : `/api/projects/bsh-home-connect/tickets`;
  const res = await fetch(url, { ...options, method: "GET", headers: { ...(params?.["X-Forwarded-Access-Token"] != null && { "X-Forwarded-Access-Token": params["X-Forwarded-Access-Token"] }), ...options?.headers } });
  if (!res.ok) {
    const body = await res.text();
    let parsed: unknown;
    try { parsed = JSON.parse(body); } catch { parsed = body; }
    throw new ApiError(res.status, res.statusText, parsed);
  }
  return { data: await res.json() };
};

export const bsh_listTicketsKey = (params?: Bsh_listTicketsParams) => {
  return ["/api/projects/bsh-home-connect/tickets", params] as const;
};

export function useBsh_listTickets<TData = { data: BshTicketOut[] }>(options?: { params?: Bsh_listTicketsParams; query?: Omit<UseQueryOptions<{ data: BshTicketOut[] }, ApiError, TData>, "queryKey" | "queryFn"> }) {
  return useQuery({ queryKey: bsh_listTicketsKey(options?.params), queryFn: () => bsh_listTickets(options?.params), ...options?.query });
}

export function useBsh_listTicketsSuspense<TData = { data: BshTicketOut[] }>(options?: { params?: Bsh_listTicketsParams; query?: Omit<UseSuspenseQueryOptions<{ data: BshTicketOut[] }, ApiError, TData>, "queryKey" | "queryFn"> }) {
  return useSuspenseQuery({ queryKey: bsh_listTicketsKey(options?.params), queryFn: () => bsh_listTickets(options?.params), ...options?.query });
}

export const bsh_createTicket = async (data: BshTicketIn, params?: Bsh_createTicketParams, options?: RequestInit): Promise<{ data: BshTicketOut }> => {
  const res = await fetch("/api/projects/bsh-home-connect/tickets", { ...options, method: "POST", headers: { "Content-Type": "application/json", ...(params?.["X-Forwarded-Access-Token"] != null && { "X-Forwarded-Access-Token": params["X-Forwarded-Access-Token"] }), ...options?.headers }, body: JSON.stringify(data) });
  if (!res.ok) {
    const body = await res.text();
    let parsed: unknown;
    try { parsed = JSON.parse(body); } catch { parsed = body; }
    throw new ApiError(res.status, res.statusText, parsed);
  }
  return { data: await res.json() };
};

export function useBsh_createTicket(options?: { mutation?: UseMutationOptions<{ data: BshTicketOut }, ApiError, { params: Bsh_createTicketParams; data: BshTicketIn }> }) {
  return useMutation({ mutationFn: (vars) => bsh_createTicket(vars.data, vars.params), ...options?.mutation });
}

export const bsh_getTicket = async (params: Bsh_getTicketParams, options?: RequestInit): Promise<{ data: BshTicketOut }> => {
  const res = await fetch(`/api/projects/bsh-home-connect/tickets/${params.ticket_id}`, { ...options, method: "GET", headers: { ...(params?.["X-Forwarded-Access-Token"] != null && { "X-Forwarded-Access-Token": params["X-Forwarded-Access-Token"] }), ...options?.headers } });
  if (!res.ok) {
    const body = await res.text();
    let parsed: unknown;
    try { parsed = JSON.parse(body); } catch { parsed = body; }
    throw new ApiError(res.status, res.statusText, parsed);
  }
  return { data: await res.json() };
};

export const bsh_getTicketKey = (params?: Bsh_getTicketParams) => {
  return ["/api/projects/bsh-home-connect/tickets/{ticket_id}", params] as const;
};

export function useBsh_getTicket<TData = { data: BshTicketOut }>(options: { params: Bsh_getTicketParams; query?: Omit<UseQueryOptions<{ data: BshTicketOut }, ApiError, TData>, "queryKey" | "queryFn"> }) {
  return useQuery({ queryKey: bsh_getTicketKey(options.params), queryFn: () => bsh_getTicket(options.params), ...options?.query });
}

export function useBsh_getTicketSuspense<TData = { data: BshTicketOut }>(options: { params: Bsh_getTicketParams; query?: Omit<UseSuspenseQueryOptions<{ data: BshTicketOut }, ApiError, TData>, "queryKey" | "queryFn"> }) {
  return useSuspenseQuery({ queryKey: bsh_getTicketKey(options.params), queryFn: () => bsh_getTicket(options.params), ...options?.query });
}

export const bsh_updateTicket = async (params: Bsh_updateTicketParams, data: BshTicketUpdate, options?: RequestInit): Promise<{ data: BshTicketOut }> => {
  const res = await fetch(`/api/projects/bsh-home-connect/tickets/${params.ticket_id}`, { ...options, method: "PATCH", headers: { "Content-Type": "application/json", ...(params?.["X-Forwarded-Access-Token"] != null && { "X-Forwarded-Access-Token": params["X-Forwarded-Access-Token"] }), ...options?.headers }, body: JSON.stringify(data) });
  if (!res.ok) {
    const body = await res.text();
    let parsed: unknown;
    try { parsed = JSON.parse(body); } catch { parsed = body; }
    throw new ApiError(res.status, res.statusText, parsed);
  }
  return { data: await res.json() };
};

export function useBsh_updateTicket(options?: { mutation?: UseMutationOptions<{ data: BshTicketOut }, ApiError, { params: Bsh_updateTicketParams; data: BshTicketUpdate }> }) {
  return useMutation({ mutationFn: (vars) => bsh_updateTicket(vars.params, vars.data), ...options?.mutation });
}

export const bsh_sendChatMessage = async (params: Bsh_sendChatMessageParams, data: BshChatMessageIn, options?: RequestInit): Promise<{ data: unknown }> => {
  const res = await fetch(`/api/projects/bsh-home-connect/tickets/${params.ticket_id}/chat`, { ...options, method: "POST", headers: { "Content-Type": "application/json", ...(params?.["X-Forwarded-Access-Token"] != null && { "X-Forwarded-Access-Token": params["X-Forwarded-Access-Token"] }), ...options?.headers }, body: JSON.stringify(data) });
  if (!res.ok) {
    const body = await res.text();
    let parsed: unknown;
    try { parsed = JSON.parse(body); } catch { parsed = body; }
    throw new ApiError(res.status, res.statusText, parsed);
  }
  return { data: await res.json() };
};

export function useBsh_sendChatMessage(options?: { mutation?: UseMutationOptions<{ data: unknown }, ApiError, { params: Bsh_sendChatMessageParams; data: BshChatMessageIn }> }) {
  return useMutation({ mutationFn: (vars) => bsh_sendChatMessage(vars.params, vars.data), ...options?.mutation });
}

export const bsh_getChatHistory = async (params: Bsh_getChatHistoryParams, options?: RequestInit): Promise<{ data: BshChatHistoryOut }> => {
  const searchParams = new URLSearchParams();
  if (params?.session_type != null) searchParams.set("session_type", String(params?.session_type));
  const queryString = searchParams.toString();
  const url = queryString ? `/api/projects/bsh-home-connect/tickets/${params.ticket_id}/chat/history?${queryString}` : `/api/projects/bsh-home-connect/tickets/${params.ticket_id}/chat/history`;
  const res = await fetch(url, { ...options, method: "GET", headers: { ...(params?.["X-Forwarded-Access-Token"] != null && { "X-Forwarded-Access-Token": params["X-Forwarded-Access-Token"] }), ...options?.headers } });
  if (!res.ok) {
    const body = await res.text();
    let parsed: unknown;
    try { parsed = JSON.parse(body); } catch { parsed = body; }
    throw new ApiError(res.status, res.statusText, parsed);
  }
  return { data: await res.json() };
};

export const bsh_getChatHistoryKey = (params?: Bsh_getChatHistoryParams) => {
  return ["/api/projects/bsh-home-connect/tickets/{ticket_id}/chat/history", params] as const;
};

export function useBsh_getChatHistory<TData = { data: BshChatHistoryOut }>(options: { params: Bsh_getChatHistoryParams; query?: Omit<UseQueryOptions<{ data: BshChatHistoryOut }, ApiError, TData>, "queryKey" | "queryFn"> }) {
  return useQuery({ queryKey: bsh_getChatHistoryKey(options.params), queryFn: () => bsh_getChatHistory(options.params), ...options?.query });
}

export function useBsh_getChatHistorySuspense<TData = { data: BshChatHistoryOut }>(options: { params: Bsh_getChatHistoryParams; query?: Omit<UseSuspenseQueryOptions<{ data: BshChatHistoryOut }, ApiError, TData>, "queryKey" | "queryFn"> }) {
  return useSuspenseQuery({ queryKey: bsh_getChatHistoryKey(options.params), queryFn: () => bsh_getChatHistory(options.params), ...options?.query });
}

export const bsh_uploadTicketMedia = async (params: Bsh_uploadTicketMediaParams, data: FormData, options?: RequestInit): Promise<{ data: unknown }> => {
  const res = await fetch(`/api/projects/bsh-home-connect/tickets/${params.ticket_id}/media`, { ...options, method: "POST", headers: { ...(params?.["X-Forwarded-Access-Token"] != null && { "X-Forwarded-Access-Token": params["X-Forwarded-Access-Token"] }), ...options?.headers }, body: data });
  if (!res.ok) {
    const body = await res.text();
    let parsed: unknown;
    try { parsed = JSON.parse(body); } catch { parsed = body; }
    throw new ApiError(res.status, res.statusText, parsed);
  }
  return { data: await res.json() };
};

export function useBsh_uploadTicketMedia(options?: { mutation?: UseMutationOptions<{ data: unknown }, ApiError, { params: Bsh_uploadTicketMediaParams; data: FormData }> }) {
  return useMutation({ mutationFn: (vars) => bsh_uploadTicketMedia(vars.params, vars.data), ...options?.mutation });
}

export const bsh_listTicketNotes = async (params: Bsh_listTicketNotesParams, options?: RequestInit): Promise<{ data: BshTicketNoteOut[] }> => {
  const res = await fetch(`/api/projects/bsh-home-connect/tickets/${params.ticket_id}/notes`, { ...options, method: "GET", headers: { ...(params?.["X-Forwarded-Access-Token"] != null && { "X-Forwarded-Access-Token": params["X-Forwarded-Access-Token"] }), ...options?.headers } });
  if (!res.ok) {
    const body = await res.text();
    let parsed: unknown;
    try { parsed = JSON.parse(body); } catch { parsed = body; }
    throw new ApiError(res.status, res.statusText, parsed);
  }
  return { data: await res.json() };
};

export const bsh_listTicketNotesKey = (params?: Bsh_listTicketNotesParams) => {
  return ["/api/projects/bsh-home-connect/tickets/{ticket_id}/notes", params] as const;
};

export function useBsh_listTicketNotes<TData = { data: BshTicketNoteOut[] }>(options: { params: Bsh_listTicketNotesParams; query?: Omit<UseQueryOptions<{ data: BshTicketNoteOut[] }, ApiError, TData>, "queryKey" | "queryFn"> }) {
  return useQuery({ queryKey: bsh_listTicketNotesKey(options.params), queryFn: () => bsh_listTicketNotes(options.params), ...options?.query });
}

export function useBsh_listTicketNotesSuspense<TData = { data: BshTicketNoteOut[] }>(options: { params: Bsh_listTicketNotesParams; query?: Omit<UseSuspenseQueryOptions<{ data: BshTicketNoteOut[] }, ApiError, TData>, "queryKey" | "queryFn"> }) {
  return useSuspenseQuery({ queryKey: bsh_listTicketNotesKey(options.params), queryFn: () => bsh_listTicketNotes(options.params), ...options?.query });
}

export const bsh_addTicketNote = async (params: Bsh_addTicketNoteParams, data: BshTicketNoteIn, options?: RequestInit): Promise<{ data: BshTicketNoteOut }> => {
  const res = await fetch(`/api/projects/bsh-home-connect/tickets/${params.ticket_id}/notes`, { ...options, method: "POST", headers: { "Content-Type": "application/json", ...(params?.["X-Forwarded-Access-Token"] != null && { "X-Forwarded-Access-Token": params["X-Forwarded-Access-Token"] }), ...options?.headers }, body: JSON.stringify(data) });
  if (!res.ok) {
    const body = await res.text();
    let parsed: unknown;
    try { parsed = JSON.parse(body); } catch { parsed = body; }
    throw new ApiError(res.status, res.statusText, parsed);
  }
  return { data: await res.json() };
};

export function useBsh_addTicketNote(options?: { mutation?: UseMutationOptions<{ data: BshTicketNoteOut }, ApiError, { params: Bsh_addTicketNoteParams; data: BshTicketNoteIn }> }) {
  return useMutation({ mutationFn: (vars) => bsh_addTicketNote(vars.params, vars.data), ...options?.mutation });
}

export const bsh_generateShippingLabel = async (params: Bsh_generateShippingLabelParams, options?: RequestInit): Promise<{ data: unknown }> => {
  const res = await fetch(`/api/projects/bsh-home-connect/tickets/${params.ticket_id}/shipping-label`, { ...options, method: "POST", headers: { ...(params?.["X-Forwarded-Access-Token"] != null && { "X-Forwarded-Access-Token": params["X-Forwarded-Access-Token"] }), ...options?.headers } });
  if (!res.ok) {
    const body = await res.text();
    let parsed: unknown;
    try { parsed = JSON.parse(body); } catch { parsed = body; }
    throw new ApiError(res.status, res.statusText, parsed);
  }
  return { data: await res.json() };
};

export function useBsh_generateShippingLabel(options?: { mutation?: UseMutationOptions<{ data: unknown }, ApiError, { params: Bsh_generateShippingLabelParams }> }) {
  return useMutation({ mutationFn: (vars) => bsh_generateShippingLabel(vars.params), ...options?.mutation });
}

export const hb_listAlerts = async (params?: Hb_listAlertsParams, options?: RequestInit): Promise<{ data: HbAuthAlertOut[] }> => {
  const searchParams = new URLSearchParams();
  if (params?.resolution != null) searchParams.set("resolution", String(params?.resolution));
  if (params?.limit != null) searchParams.set("limit", String(params?.limit));
  if (params?.offset != null) searchParams.set("offset", String(params?.offset));
  const queryString = searchParams.toString();
  const url = queryString ? `/api/projects/hb-product-center/authenticity/alerts?${queryString}` : `/api/projects/hb-product-center/authenticity/alerts`;
  const res = await fetch(url, { ...options, method: "GET" });
  if (!res.ok) {
    const body = await res.text();
    let parsed: unknown;
    try { parsed = JSON.parse(body); } catch { parsed = body; }
    throw new ApiError(res.status, res.statusText, parsed);
  }
  return { data: await res.json() };
};

export const hb_listAlertsKey = (params?: Hb_listAlertsParams) => {
  return ["/api/projects/hb-product-center/authenticity/alerts", params] as const;
};

export function useHb_listAlerts<TData = { data: HbAuthAlertOut[] }>(options?: { params?: Hb_listAlertsParams; query?: Omit<UseQueryOptions<{ data: HbAuthAlertOut[] }, ApiError, TData>, "queryKey" | "queryFn"> }) {
  return useQuery({ queryKey: hb_listAlertsKey(options?.params), queryFn: () => hb_listAlerts(options?.params), ...options?.query });
}

export function useHb_listAlertsSuspense<TData = { data: HbAuthAlertOut[] }>(options?: { params?: Hb_listAlertsParams; query?: Omit<UseSuspenseQueryOptions<{ data: HbAuthAlertOut[] }, ApiError, TData>, "queryKey" | "queryFn"> }) {
  return useSuspenseQuery({ queryKey: hb_listAlertsKey(options?.params), queryFn: () => hb_listAlerts(options?.params), ...options?.query });
}

export const hb_updateAlert = async (params: Hb_updateAlertParams, data: HbAuthAlertUpdate, options?: RequestInit): Promise<{ data: HbAuthAlertOut }> => {
  const res = await fetch(`/api/projects/hb-product-center/authenticity/alerts/${params.alert_id}`, { ...options, method: "PATCH", headers: { "Content-Type": "application/json", ...options?.headers }, body: JSON.stringify(data) });
  if (!res.ok) {
    const body = await res.text();
    let parsed: unknown;
    try { parsed = JSON.parse(body); } catch { parsed = body; }
    throw new ApiError(res.status, res.statusText, parsed);
  }
  return { data: await res.json() };
};

export function useHb_updateAlert(options?: { mutation?: UseMutationOptions<{ data: HbAuthAlertOut }, ApiError, { params: Hb_updateAlertParams; data: HbAuthAlertUpdate }> }) {
  return useMutation({ mutationFn: (vars) => hb_updateAlert(vars.params, vars.data), ...options?.mutation });
}

export const hb_listVerifications = async (params?: Hb_listVerificationsParams, options?: RequestInit): Promise<{ data: HbAuthVerificationOut[] }> => {
  const searchParams = new URLSearchParams();
  if (params?.status != null) searchParams.set("status", String(params?.status));
  if (params?.requester_type != null) searchParams.set("requester_type", String(params?.requester_type));
  if (params?.limit != null) searchParams.set("limit", String(params?.limit));
  if (params?.offset != null) searchParams.set("offset", String(params?.offset));
  const queryString = searchParams.toString();
  const url = queryString ? `/api/projects/hb-product-center/authenticity/verifications?${queryString}` : `/api/projects/hb-product-center/authenticity/verifications`;
  const res = await fetch(url, { ...options, method: "GET" });
  if (!res.ok) {
    const body = await res.text();
    let parsed: unknown;
    try { parsed = JSON.parse(body); } catch { parsed = body; }
    throw new ApiError(res.status, res.statusText, parsed);
  }
  return { data: await res.json() };
};

export const hb_listVerificationsKey = (params?: Hb_listVerificationsParams) => {
  return ["/api/projects/hb-product-center/authenticity/verifications", params] as const;
};

export function useHb_listVerifications<TData = { data: HbAuthVerificationOut[] }>(options?: { params?: Hb_listVerificationsParams; query?: Omit<UseQueryOptions<{ data: HbAuthVerificationOut[] }, ApiError, TData>, "queryKey" | "queryFn"> }) {
  return useQuery({ queryKey: hb_listVerificationsKey(options?.params), queryFn: () => hb_listVerifications(options?.params), ...options?.query });
}

export function useHb_listVerificationsSuspense<TData = { data: HbAuthVerificationOut[] }>(options?: { params?: Hb_listVerificationsParams; query?: Omit<UseSuspenseQueryOptions<{ data: HbAuthVerificationOut[] }, ApiError, TData>, "queryKey" | "queryFn"> }) {
  return useSuspenseQuery({ queryKey: hb_listVerificationsKey(options?.params), queryFn: () => hb_listVerifications(options?.params), ...options?.query });
}

export const hb_getVerification = async (params: Hb_getVerificationParams, options?: RequestInit): Promise<{ data: HbAuthVerificationOut }> => {
  const res = await fetch(`/api/projects/hb-product-center/authenticity/verifications/${params.verification_id}`, { ...options, method: "GET" });
  if (!res.ok) {
    const body = await res.text();
    let parsed: unknown;
    try { parsed = JSON.parse(body); } catch { parsed = body; }
    throw new ApiError(res.status, res.statusText, parsed);
  }
  return { data: await res.json() };
};

export const hb_getVerificationKey = (params?: Hb_getVerificationParams) => {
  return ["/api/projects/hb-product-center/authenticity/verifications/{verification_id}", params] as const;
};

export function useHb_getVerification<TData = { data: HbAuthVerificationOut }>(options: { params: Hb_getVerificationParams; query?: Omit<UseQueryOptions<{ data: HbAuthVerificationOut }, ApiError, TData>, "queryKey" | "queryFn"> }) {
  return useQuery({ queryKey: hb_getVerificationKey(options.params), queryFn: () => hb_getVerification(options.params), ...options?.query });
}

export function useHb_getVerificationSuspense<TData = { data: HbAuthVerificationOut }>(options: { params: Hb_getVerificationParams; query?: Omit<UseSuspenseQueryOptions<{ data: HbAuthVerificationOut }, ApiError, TData>, "queryKey" | "queryFn"> }) {
  return useSuspenseQuery({ queryKey: hb_getVerificationKey(options.params), queryFn: () => hb_getVerification(options.params), ...options?.query });
}

export const hb_createVerification = async (data: HbAuthVerificationCreate, options?: RequestInit): Promise<{ data: HbAuthVerificationOut }> => {
  const res = await fetch("/api/projects/hb-product-center/authenticity/verify", { ...options, method: "POST", headers: { "Content-Type": "application/json", ...options?.headers }, body: JSON.stringify(data) });
  if (!res.ok) {
    const body = await res.text();
    let parsed: unknown;
    try { parsed = JSON.parse(body); } catch { parsed = body; }
    throw new ApiError(res.status, res.statusText, parsed);
  }
  return { data: await res.json() };
};

export function useHb_createVerification(options?: { mutation?: UseMutationOptions<{ data: HbAuthVerificationOut }, ApiError, HbAuthVerificationCreate> }) {
  return useMutation({ mutationFn: (data) => hb_createVerification(data), ...options?.mutation });
}

export const hb_sendMasChatMessage = async (data: HbChatMessageIn, options?: RequestInit): Promise<{ data: unknown }> => {
  const res = await fetch("/api/projects/hb-product-center/chat/mas-chat", { ...options, method: "POST", headers: { "Content-Type": "application/json", ...options?.headers }, body: JSON.stringify(data) });
  if (!res.ok) {
    const body = await res.text();
    let parsed: unknown;
    try { parsed = JSON.parse(body); } catch { parsed = body; }
    throw new ApiError(res.status, res.statusText, parsed);
  }
  return { data: await res.json() };
};

export function useHb_sendMasChatMessage(options?: { mutation?: UseMutationOptions<{ data: unknown }, ApiError, HbChatMessageIn> }) {
  return useMutation({ mutationFn: (data) => hb_sendMasChatMessage(data), ...options?.mutation });
}

export const hb_createChatSession = async (data: HbChatSessionCreate, options?: RequestInit): Promise<{ data: HbChatSessionOut }> => {
  const res = await fetch("/api/projects/hb-product-center/chat/sessions", { ...options, method: "POST", headers: { "Content-Type": "application/json", ...options?.headers }, body: JSON.stringify(data) });
  if (!res.ok) {
    const body = await res.text();
    let parsed: unknown;
    try { parsed = JSON.parse(body); } catch { parsed = body; }
    throw new ApiError(res.status, res.statusText, parsed);
  }
  return { data: await res.json() };
};

export function useHb_createChatSession(options?: { mutation?: UseMutationOptions<{ data: HbChatSessionOut }, ApiError, HbChatSessionCreate> }) {
  return useMutation({ mutationFn: (data) => hb_createChatSession(data), ...options?.mutation });
}

export const hb_getChatMessages = async (params: Hb_getChatMessagesParams, options?: RequestInit): Promise<{ data: HbChatMessageOut[] }> => {
  const res = await fetch(`/api/projects/hb-product-center/chat/sessions/${params.session_id}/messages`, { ...options, method: "GET" });
  if (!res.ok) {
    const body = await res.text();
    let parsed: unknown;
    try { parsed = JSON.parse(body); } catch { parsed = body; }
    throw new ApiError(res.status, res.statusText, parsed);
  }
  return { data: await res.json() };
};

export const hb_getChatMessagesKey = (params?: Hb_getChatMessagesParams) => {
  return ["/api/projects/hb-product-center/chat/sessions/{session_id}/messages", params] as const;
};

export function useHb_getChatMessages<TData = { data: HbChatMessageOut[] }>(options: { params: Hb_getChatMessagesParams; query?: Omit<UseQueryOptions<{ data: HbChatMessageOut[] }, ApiError, TData>, "queryKey" | "queryFn"> }) {
  return useQuery({ queryKey: hb_getChatMessagesKey(options.params), queryFn: () => hb_getChatMessages(options.params), ...options?.query });
}

export function useHb_getChatMessagesSuspense<TData = { data: HbChatMessageOut[] }>(options: { params: Hb_getChatMessagesParams; query?: Omit<UseSuspenseQueryOptions<{ data: HbChatMessageOut[] }, ApiError, TData>, "queryKey" | "queryFn"> }) {
  return useSuspenseQuery({ queryKey: hb_getChatMessagesKey(options.params), queryFn: () => hb_getChatMessages(options.params), ...options?.query });
}

export const hb_sendChatMessage = async (params: Hb_sendChatMessageParams, data: HbChatMessageIn, options?: RequestInit): Promise<{ data: HbChatMessageOut }> => {
  const res = await fetch(`/api/projects/hb-product-center/chat/sessions/${params.session_id}/messages`, { ...options, method: "POST", headers: { "Content-Type": "application/json", ...options?.headers }, body: JSON.stringify(data) });
  if (!res.ok) {
    const body = await res.text();
    let parsed: unknown;
    try { parsed = JSON.parse(body); } catch { parsed = body; }
    throw new ApiError(res.status, res.statusText, parsed);
  }
  return { data: await res.json() };
};

export function useHb_sendChatMessage(options?: { mutation?: UseMutationOptions<{ data: HbChatMessageOut }, ApiError, { params: Hb_sendChatMessageParams; data: HbChatMessageIn }> }) {
  return useMutation({ mutationFn: (vars) => hb_sendChatMessage(vars.params, vars.data), ...options?.mutation });
}

export const hb_getDashboardSummary = async (options?: RequestInit): Promise<{ data: HbDashboardSummary }> => {
  const res = await fetch("/api/projects/hb-product-center/dashboard/summary", { ...options, method: "GET" });
  if (!res.ok) {
    const body = await res.text();
    let parsed: unknown;
    try { parsed = JSON.parse(body); } catch { parsed = body; }
    throw new ApiError(res.status, res.statusText, parsed);
  }
  return { data: await res.json() };
};

export const hb_getDashboardSummaryKey = () => {
  return ["/api/projects/hb-product-center/dashboard/summary"] as const;
};

export function useHb_getDashboardSummary<TData = { data: HbDashboardSummary }>(options?: { query?: Omit<UseQueryOptions<{ data: HbDashboardSummary }, ApiError, TData>, "queryKey" | "queryFn"> }) {
  return useQuery({ queryKey: hb_getDashboardSummaryKey(), queryFn: () => hb_getDashboardSummary(), ...options?.query });
}

export function useHb_getDashboardSummarySuspense<TData = { data: HbDashboardSummary }>(options?: { query?: Omit<UseSuspenseQueryOptions<{ data: HbDashboardSummary }, ApiError, TData>, "queryKey" | "queryFn"> }) {
  return useSuspenseQuery({ queryKey: hb_getDashboardSummaryKey(), queryFn: () => hb_getDashboardSummary(), ...options?.query });
}

export const hb_getDashboardTrends = async (options?: RequestInit): Promise<{ data: HbTrendPoint[] }> => {
  const res = await fetch("/api/projects/hb-product-center/dashboard/trends", { ...options, method: "GET" });
  if (!res.ok) {
    const body = await res.text();
    let parsed: unknown;
    try { parsed = JSON.parse(body); } catch { parsed = body; }
    throw new ApiError(res.status, res.statusText, parsed);
  }
  return { data: await res.json() };
};

export const hb_getDashboardTrendsKey = () => {
  return ["/api/projects/hb-product-center/dashboard/trends"] as const;
};

export function useHb_getDashboardTrends<TData = { data: HbTrendPoint[] }>(options?: { query?: Omit<UseQueryOptions<{ data: HbTrendPoint[] }, ApiError, TData>, "queryKey" | "queryFn"> }) {
  return useQuery({ queryKey: hb_getDashboardTrendsKey(), queryFn: () => hb_getDashboardTrends(), ...options?.query });
}

export function useHb_getDashboardTrendsSuspense<TData = { data: HbTrendPoint[] }>(options?: { query?: Omit<UseSuspenseQueryOptions<{ data: HbTrendPoint[] }, ApiError, TData>, "queryKey" | "queryFn"> }) {
  return useSuspenseQuery({ queryKey: hb_getDashboardTrendsKey(), queryFn: () => hb_getDashboardTrends(), ...options?.query });
}

export const hb_getDatabricksResources = async (options?: RequestInit): Promise<{ data: HbDatabricksResourcesOut }> => {
  const res = await fetch("/api/projects/hb-product-center/databricks-resources", { ...options, method: "GET" });
  if (!res.ok) {
    const body = await res.text();
    let parsed: unknown;
    try { parsed = JSON.parse(body); } catch { parsed = body; }
    throw new ApiError(res.status, res.statusText, parsed);
  }
  return { data: await res.json() };
};

export const hb_getDatabricksResourcesKey = () => {
  return ["/api/projects/hb-product-center/databricks-resources"] as const;
};

export function useHb_getDatabricksResources<TData = { data: HbDatabricksResourcesOut }>(options?: { query?: Omit<UseQueryOptions<{ data: HbDatabricksResourcesOut }, ApiError, TData>, "queryKey" | "queryFn"> }) {
  return useQuery({ queryKey: hb_getDatabricksResourcesKey(), queryFn: () => hb_getDatabricksResources(), ...options?.query });
}

export function useHb_getDatabricksResourcesSuspense<TData = { data: HbDatabricksResourcesOut }>(options?: { query?: Omit<UseSuspenseQueryOptions<{ data: HbDatabricksResourcesOut }, ApiError, TData>, "queryKey" | "queryFn"> }) {
  return useSuspenseQuery({ queryKey: hb_getDatabricksResourcesKey(), queryFn: () => hb_getDatabricksResources(), ...options?.query });
}

export const hb_listProducts = async (params?: Hb_listProductsParams, options?: RequestInit): Promise<{ data: HbProductOut[] }> => {
  const searchParams = new URLSearchParams();
  if (params?.category != null) searchParams.set("category", String(params?.category));
  if (params?.collection != null) searchParams.set("collection", String(params?.collection));
  if (params?.season != null) searchParams.set("season", String(params?.season));
  if (params?.search != null) searchParams.set("search", String(params?.search));
  if (params?.limit != null) searchParams.set("limit", String(params?.limit));
  if (params?.offset != null) searchParams.set("offset", String(params?.offset));
  const queryString = searchParams.toString();
  const url = queryString ? `/api/projects/hb-product-center/products?${queryString}` : `/api/projects/hb-product-center/products`;
  const res = await fetch(url, { ...options, method: "GET" });
  if (!res.ok) {
    const body = await res.text();
    let parsed: unknown;
    try { parsed = JSON.parse(body); } catch { parsed = body; }
    throw new ApiError(res.status, res.statusText, parsed);
  }
  return { data: await res.json() };
};

export const hb_listProductsKey = (params?: Hb_listProductsParams) => {
  return ["/api/projects/hb-product-center/products", params] as const;
};

export function useHb_listProducts<TData = { data: HbProductOut[] }>(options?: { params?: Hb_listProductsParams; query?: Omit<UseQueryOptions<{ data: HbProductOut[] }, ApiError, TData>, "queryKey" | "queryFn"> }) {
  return useQuery({ queryKey: hb_listProductsKey(options?.params), queryFn: () => hb_listProducts(options?.params), ...options?.query });
}

export function useHb_listProductsSuspense<TData = { data: HbProductOut[] }>(options?: { params?: Hb_listProductsParams; query?: Omit<UseSuspenseQueryOptions<{ data: HbProductOut[] }, ApiError, TData>, "queryKey" | "queryFn"> }) {
  return useSuspenseQuery({ queryKey: hb_listProductsKey(options?.params), queryFn: () => hb_listProducts(options?.params), ...options?.query });
}

export const hb_getProduct = async (params: Hb_getProductParams, options?: RequestInit): Promise<{ data: HbProductOut }> => {
  const res = await fetch(`/api/projects/hb-product-center/products/${params.product_id}`, { ...options, method: "GET" });
  if (!res.ok) {
    const body = await res.text();
    let parsed: unknown;
    try { parsed = JSON.parse(body); } catch { parsed = body; }
    throw new ApiError(res.status, res.statusText, parsed);
  }
  return { data: await res.json() };
};

export const hb_getProductKey = (params?: Hb_getProductParams) => {
  return ["/api/projects/hb-product-center/products/{product_id}", params] as const;
};

export function useHb_getProduct<TData = { data: HbProductOut }>(options: { params: Hb_getProductParams; query?: Omit<UseQueryOptions<{ data: HbProductOut }, ApiError, TData>, "queryKey" | "queryFn"> }) {
  return useQuery({ queryKey: hb_getProductKey(options.params), queryFn: () => hb_getProduct(options.params), ...options?.query });
}

export function useHb_getProductSuspense<TData = { data: HbProductOut }>(options: { params: Hb_getProductParams; query?: Omit<UseSuspenseQueryOptions<{ data: HbProductOut }, ApiError, TData>, "queryKey" | "queryFn"> }) {
  return useSuspenseQuery({ queryKey: hb_getProductKey(options.params), queryFn: () => hb_getProduct(options.params), ...options?.query });
}

export const hb_getProductImages = async (params: Hb_getProductImagesParams, options?: RequestInit): Promise<{ data: HbProductImageOut[] }> => {
  const res = await fetch(`/api/projects/hb-product-center/products/${params.product_id}/images`, { ...options, method: "GET" });
  if (!res.ok) {
    const body = await res.text();
    let parsed: unknown;
    try { parsed = JSON.parse(body); } catch { parsed = body; }
    throw new ApiError(res.status, res.statusText, parsed);
  }
  return { data: await res.json() };
};

export const hb_getProductImagesKey = (params?: Hb_getProductImagesParams) => {
  return ["/api/projects/hb-product-center/products/{product_id}/images", params] as const;
};

export function useHb_getProductImages<TData = { data: HbProductImageOut[] }>(options: { params: Hb_getProductImagesParams; query?: Omit<UseQueryOptions<{ data: HbProductImageOut[] }, ApiError, TData>, "queryKey" | "queryFn"> }) {
  return useQuery({ queryKey: hb_getProductImagesKey(options.params), queryFn: () => hb_getProductImages(options.params), ...options?.query });
}

export function useHb_getProductImagesSuspense<TData = { data: HbProductImageOut[] }>(options: { params: Hb_getProductImagesParams; query?: Omit<UseSuspenseQueryOptions<{ data: HbProductImageOut[] }, ApiError, TData>, "queryKey" | "queryFn"> }) {
  return useSuspenseQuery({ queryKey: hb_getProductImagesKey(options.params), queryFn: () => hb_getProductImages(options.params), ...options?.query });
}

export const hb_sendQualityAssistantMessage = async (data: HbChatMessageIn, options?: RequestInit): Promise<{ data: unknown }> => {
  const res = await fetch("/api/projects/hb-product-center/quality/assistant-chat", { ...options, method: "POST", headers: { "Content-Type": "application/json", ...options?.headers }, body: JSON.stringify(data) });
  if (!res.ok) {
    const body = await res.text();
    let parsed: unknown;
    try { parsed = JSON.parse(body); } catch { parsed = body; }
    throw new ApiError(res.status, res.statusText, parsed);
  }
  return { data: await res.json() };
};

export function useHb_sendQualityAssistantMessage(options?: { mutation?: UseMutationOptions<{ data: unknown }, ApiError, HbChatMessageIn> }) {
  return useMutation({ mutationFn: (data) => hb_sendQualityAssistantMessage(data), ...options?.mutation });
}

export const hb_listInspections = async (params?: Hb_listInspectionsParams, options?: RequestInit): Promise<{ data: HbQualityInspectionOut[] }> => {
  const searchParams = new URLSearchParams();
  if (params?.status != null) searchParams.set("status", String(params?.status));
  if (params?.product_id != null) searchParams.set("product_id", String(params?.product_id));
  if (params?.limit != null) searchParams.set("limit", String(params?.limit));
  if (params?.offset != null) searchParams.set("offset", String(params?.offset));
  const queryString = searchParams.toString();
  const url = queryString ? `/api/projects/hb-product-center/quality/inspections?${queryString}` : `/api/projects/hb-product-center/quality/inspections`;
  const res = await fetch(url, { ...options, method: "GET" });
  if (!res.ok) {
    const body = await res.text();
    let parsed: unknown;
    try { parsed = JSON.parse(body); } catch { parsed = body; }
    throw new ApiError(res.status, res.statusText, parsed);
  }
  return { data: await res.json() };
};

export const hb_listInspectionsKey = (params?: Hb_listInspectionsParams) => {
  return ["/api/projects/hb-product-center/quality/inspections", params] as const;
};

export function useHb_listInspections<TData = { data: HbQualityInspectionOut[] }>(options?: { params?: Hb_listInspectionsParams; query?: Omit<UseQueryOptions<{ data: HbQualityInspectionOut[] }, ApiError, TData>, "queryKey" | "queryFn"> }) {
  return useQuery({ queryKey: hb_listInspectionsKey(options?.params), queryFn: () => hb_listInspections(options?.params), ...options?.query });
}

export function useHb_listInspectionsSuspense<TData = { data: HbQualityInspectionOut[] }>(options?: { params?: Hb_listInspectionsParams; query?: Omit<UseSuspenseQueryOptions<{ data: HbQualityInspectionOut[] }, ApiError, TData>, "queryKey" | "queryFn"> }) {
  return useSuspenseQuery({ queryKey: hb_listInspectionsKey(options?.params), queryFn: () => hb_listInspections(options?.params), ...options?.query });
}

export const hb_createInspection = async (data: HbQualityInspectionCreate, options?: RequestInit): Promise<{ data: HbQualityInspectionOut }> => {
  const res = await fetch("/api/projects/hb-product-center/quality/inspections", { ...options, method: "POST", headers: { "Content-Type": "application/json", ...options?.headers }, body: JSON.stringify(data) });
  if (!res.ok) {
    const body = await res.text();
    let parsed: unknown;
    try { parsed = JSON.parse(body); } catch { parsed = body; }
    throw new ApiError(res.status, res.statusText, parsed);
  }
  return { data: await res.json() };
};

export function useHb_createInspection(options?: { mutation?: UseMutationOptions<{ data: HbQualityInspectionOut }, ApiError, HbQualityInspectionCreate> }) {
  return useMutation({ mutationFn: (data) => hb_createInspection(data), ...options?.mutation });
}

export const hb_getInspection = async (params: Hb_getInspectionParams, options?: RequestInit): Promise<{ data: HbInspectionDetailOut }> => {
  const res = await fetch(`/api/projects/hb-product-center/quality/inspections/${params.inspection_id}`, { ...options, method: "GET" });
  if (!res.ok) {
    const body = await res.text();
    let parsed: unknown;
    try { parsed = JSON.parse(body); } catch { parsed = body; }
    throw new ApiError(res.status, res.statusText, parsed);
  }
  return { data: await res.json() };
};

export const hb_getInspectionKey = (params?: Hb_getInspectionParams) => {
  return ["/api/projects/hb-product-center/quality/inspections/{inspection_id}", params] as const;
};

export function useHb_getInspection<TData = { data: HbInspectionDetailOut }>(options: { params: Hb_getInspectionParams; query?: Omit<UseQueryOptions<{ data: HbInspectionDetailOut }, ApiError, TData>, "queryKey" | "queryFn"> }) {
  return useQuery({ queryKey: hb_getInspectionKey(options.params), queryFn: () => hb_getInspection(options.params), ...options?.query });
}

export function useHb_getInspectionSuspense<TData = { data: HbInspectionDetailOut }>(options: { params: Hb_getInspectionParams; query?: Omit<UseSuspenseQueryOptions<{ data: HbInspectionDetailOut }, ApiError, TData>, "queryKey" | "queryFn"> }) {
  return useSuspenseQuery({ queryKey: hb_getInspectionKey(options.params), queryFn: () => hb_getInspection(options.params), ...options?.query });
}

export const hb_updateInspection = async (params: Hb_updateInspectionParams, data: HbQualityInspectionUpdate, options?: RequestInit): Promise<{ data: HbQualityInspectionOut }> => {
  const res = await fetch(`/api/projects/hb-product-center/quality/inspections/${params.inspection_id}`, { ...options, method: "PATCH", headers: { "Content-Type": "application/json", ...options?.headers }, body: JSON.stringify(data) });
  if (!res.ok) {
    const body = await res.text();
    let parsed: unknown;
    try { parsed = JSON.parse(body); } catch { parsed = body; }
    throw new ApiError(res.status, res.statusText, parsed);
  }
  return { data: await res.json() };
};

export function useHb_updateInspection(options?: { mutation?: UseMutationOptions<{ data: HbQualityInspectionOut }, ApiError, { params: Hb_updateInspectionParams; data: HbQualityInspectionUpdate }> }) {
  return useMutation({ mutationFn: (vars) => hb_updateInspection(vars.params, vars.data), ...options?.mutation });
}

export const hb_getQualityStats = async (options?: RequestInit): Promise<{ data: HbQualityStats }> => {
  const res = await fetch("/api/projects/hb-product-center/quality/stats", { ...options, method: "GET" });
  if (!res.ok) {
    const body = await res.text();
    let parsed: unknown;
    try { parsed = JSON.parse(body); } catch { parsed = body; }
    throw new ApiError(res.status, res.statusText, parsed);
  }
  return { data: await res.json() };
};

export const hb_getQualityStatsKey = () => {
  return ["/api/projects/hb-product-center/quality/stats"] as const;
};

export function useHb_getQualityStats<TData = { data: HbQualityStats }>(options?: { query?: Omit<UseQueryOptions<{ data: HbQualityStats }, ApiError, TData>, "queryKey" | "queryFn"> }) {
  return useQuery({ queryKey: hb_getQualityStatsKey(), queryFn: () => hb_getQualityStats(), ...options?.query });
}

export function useHb_getQualityStatsSuspense<TData = { data: HbQualityStats }>(options?: { query?: Omit<UseSuspenseQueryOptions<{ data: HbQualityStats }, ApiError, TData>, "queryKey" | "queryFn"> }) {
  return useSuspenseQuery({ queryKey: hb_getQualityStatsKey(), queryFn: () => hb_getQualityStats(), ...options?.query });
}

export const hb_identifyProduct = async (data: ProductIdentifyRequest, options?: RequestInit): Promise<{ data: ProductIdentifyResponse }> => {
  const res = await fetch("/api/projects/hb-product-center/recognition/identify", { ...options, method: "POST", headers: { "Content-Type": "application/json", ...options?.headers }, body: JSON.stringify(data) });
  if (!res.ok) {
    const body = await res.text();
    let parsed: unknown;
    try { parsed = JSON.parse(body); } catch { parsed = body; }
    throw new ApiError(res.status, res.statusText, parsed);
  }
  return { data: await res.json() };
};

export function useHb_identifyProduct(options?: { mutation?: UseMutationOptions<{ data: ProductIdentifyResponse }, ApiError, ProductIdentifyRequest> }) {
  return useMutation({ mutationFn: (data) => hb_identifyProduct(data), ...options?.mutation });
}

export const hb_listRecognitionJobs = async (params?: Hb_listRecognitionJobsParams, options?: RequestInit): Promise<{ data: HbRecognitionJobOut[] }> => {
  const searchParams = new URLSearchParams();
  if (params?.status != null) searchParams.set("status", String(params?.status));
  if (params?.limit != null) searchParams.set("limit", String(params?.limit));
  if (params?.offset != null) searchParams.set("offset", String(params?.offset));
  const queryString = searchParams.toString();
  const url = queryString ? `/api/projects/hb-product-center/recognition/jobs?${queryString}` : `/api/projects/hb-product-center/recognition/jobs`;
  const res = await fetch(url, { ...options, method: "GET" });
  if (!res.ok) {
    const body = await res.text();
    let parsed: unknown;
    try { parsed = JSON.parse(body); } catch { parsed = body; }
    throw new ApiError(res.status, res.statusText, parsed);
  }
  return { data: await res.json() };
};

export const hb_listRecognitionJobsKey = (params?: Hb_listRecognitionJobsParams) => {
  return ["/api/projects/hb-product-center/recognition/jobs", params] as const;
};

export function useHb_listRecognitionJobs<TData = { data: HbRecognitionJobOut[] }>(options?: { params?: Hb_listRecognitionJobsParams; query?: Omit<UseQueryOptions<{ data: HbRecognitionJobOut[] }, ApiError, TData>, "queryKey" | "queryFn"> }) {
  return useQuery({ queryKey: hb_listRecognitionJobsKey(options?.params), queryFn: () => hb_listRecognitionJobs(options?.params), ...options?.query });
}

export function useHb_listRecognitionJobsSuspense<TData = { data: HbRecognitionJobOut[] }>(options?: { params?: Hb_listRecognitionJobsParams; query?: Omit<UseSuspenseQueryOptions<{ data: HbRecognitionJobOut[] }, ApiError, TData>, "queryKey" | "queryFn"> }) {
  return useSuspenseQuery({ queryKey: hb_listRecognitionJobsKey(options?.params), queryFn: () => hb_listRecognitionJobs(options?.params), ...options?.query });
}

export const hb_createRecognitionJob = async (data: HbRecognitionJobCreate, options?: RequestInit): Promise<{ data: HbRecognitionJobOut }> => {
  const res = await fetch("/api/projects/hb-product-center/recognition/jobs", { ...options, method: "POST", headers: { "Content-Type": "application/json", ...options?.headers }, body: JSON.stringify(data) });
  if (!res.ok) {
    const body = await res.text();
    let parsed: unknown;
    try { parsed = JSON.parse(body); } catch { parsed = body; }
    throw new ApiError(res.status, res.statusText, parsed);
  }
  return { data: await res.json() };
};

export function useHb_createRecognitionJob(options?: { mutation?: UseMutationOptions<{ data: HbRecognitionJobOut }, ApiError, HbRecognitionJobCreate> }) {
  return useMutation({ mutationFn: (data) => hb_createRecognitionJob(data), ...options?.mutation });
}

export const hb_createBatchRecognitionJob = async (data: HbRecognitionJobCreate, options?: RequestInit): Promise<{ data: HbRecognitionJobOut }> => {
  const res = await fetch("/api/projects/hb-product-center/recognition/jobs/batch", { ...options, method: "POST", headers: { "Content-Type": "application/json", ...options?.headers }, body: JSON.stringify(data) });
  if (!res.ok) {
    const body = await res.text();
    let parsed: unknown;
    try { parsed = JSON.parse(body); } catch { parsed = body; }
    throw new ApiError(res.status, res.statusText, parsed);
  }
  return { data: await res.json() };
};

export function useHb_createBatchRecognitionJob(options?: { mutation?: UseMutationOptions<{ data: HbRecognitionJobOut }, ApiError, HbRecognitionJobCreate> }) {
  return useMutation({ mutationFn: (data) => hb_createBatchRecognitionJob(data), ...options?.mutation });
}

export const hb_getRecognitionJob = async (params: Hb_getRecognitionJobParams, options?: RequestInit): Promise<{ data: HbRecognitionJobDetailOut }> => {
  const res = await fetch(`/api/projects/hb-product-center/recognition/jobs/${params.job_id}`, { ...options, method: "GET" });
  if (!res.ok) {
    const body = await res.text();
    let parsed: unknown;
    try { parsed = JSON.parse(body); } catch { parsed = body; }
    throw new ApiError(res.status, res.statusText, parsed);
  }
  return { data: await res.json() };
};

export const hb_getRecognitionJobKey = (params?: Hb_getRecognitionJobParams) => {
  return ["/api/projects/hb-product-center/recognition/jobs/{job_id}", params] as const;
};

export function useHb_getRecognitionJob<TData = { data: HbRecognitionJobDetailOut }>(options: { params: Hb_getRecognitionJobParams; query?: Omit<UseQueryOptions<{ data: HbRecognitionJobDetailOut }, ApiError, TData>, "queryKey" | "queryFn"> }) {
  return useQuery({ queryKey: hb_getRecognitionJobKey(options.params), queryFn: () => hb_getRecognitionJob(options.params), ...options?.query });
}

export function useHb_getRecognitionJobSuspense<TData = { data: HbRecognitionJobDetailOut }>(options: { params: Hb_getRecognitionJobParams; query?: Omit<UseSuspenseQueryOptions<{ data: HbRecognitionJobDetailOut }, ApiError, TData>, "queryKey" | "queryFn"> }) {
  return useSuspenseQuery({ queryKey: hb_getRecognitionJobKey(options.params), queryFn: () => hb_getRecognitionJob(options.params), ...options?.query });
}

export const hb_listSupplyChainEvents = async (params?: Hb_listSupplyChainEventsParams, options?: RequestInit): Promise<{ data: HbSupplyChainEventOut[] }> => {
  const searchParams = new URLSearchParams();
  if (params?.product_id != null) searchParams.set("product_id", String(params?.product_id));
  if (params?.event_type != null) searchParams.set("event_type", String(params?.event_type));
  if (params?.country != null) searchParams.set("country", String(params?.country));
  if (params?.limit != null) searchParams.set("limit", String(params?.limit));
  if (params?.offset != null) searchParams.set("offset", String(params?.offset));
  const queryString = searchParams.toString();
  const url = queryString ? `/api/projects/hb-product-center/supply-chain/events?${queryString}` : `/api/projects/hb-product-center/supply-chain/events`;
  const res = await fetch(url, { ...options, method: "GET" });
  if (!res.ok) {
    const body = await res.text();
    let parsed: unknown;
    try { parsed = JSON.parse(body); } catch { parsed = body; }
    throw new ApiError(res.status, res.statusText, parsed);
  }
  return { data: await res.json() };
};

export const hb_listSupplyChainEventsKey = (params?: Hb_listSupplyChainEventsParams) => {
  return ["/api/projects/hb-product-center/supply-chain/events", params] as const;
};

export function useHb_listSupplyChainEvents<TData = { data: HbSupplyChainEventOut[] }>(options?: { params?: Hb_listSupplyChainEventsParams; query?: Omit<UseQueryOptions<{ data: HbSupplyChainEventOut[] }, ApiError, TData>, "queryKey" | "queryFn"> }) {
  return useQuery({ queryKey: hb_listSupplyChainEventsKey(options?.params), queryFn: () => hb_listSupplyChainEvents(options?.params), ...options?.query });
}

export function useHb_listSupplyChainEventsSuspense<TData = { data: HbSupplyChainEventOut[] }>(options?: { params?: Hb_listSupplyChainEventsParams; query?: Omit<UseSuspenseQueryOptions<{ data: HbSupplyChainEventOut[] }, ApiError, TData>, "queryKey" | "queryFn"> }) {
  return useSuspenseQuery({ queryKey: hb_listSupplyChainEventsKey(options?.params), queryFn: () => hb_listSupplyChainEvents(options?.params), ...options?.query });
}

export const hb_getProductJourney = async (params: Hb_getProductJourneyParams, options?: RequestInit): Promise<{ data: HbProductJourney }> => {
  const res = await fetch(`/api/projects/hb-product-center/supply-chain/products/${params.product_id}/journey`, { ...options, method: "GET" });
  if (!res.ok) {
    const body = await res.text();
    let parsed: unknown;
    try { parsed = JSON.parse(body); } catch { parsed = body; }
    throw new ApiError(res.status, res.statusText, parsed);
  }
  return { data: await res.json() };
};

export const hb_getProductJourneyKey = (params?: Hb_getProductJourneyParams) => {
  return ["/api/projects/hb-product-center/supply-chain/products/{product_id}/journey", params] as const;
};

export function useHb_getProductJourney<TData = { data: HbProductJourney }>(options: { params: Hb_getProductJourneyParams; query?: Omit<UseQueryOptions<{ data: HbProductJourney }, ApiError, TData>, "queryKey" | "queryFn"> }) {
  return useQuery({ queryKey: hb_getProductJourneyKey(options.params), queryFn: () => hb_getProductJourney(options.params), ...options?.query });
}

export function useHb_getProductJourneySuspense<TData = { data: HbProductJourney }>(options: { params: Hb_getProductJourneyParams; query?: Omit<UseSuspenseQueryOptions<{ data: HbProductJourney }, ApiError, TData>, "queryKey" | "queryFn"> }) {
  return useSuspenseQuery({ queryKey: hb_getProductJourneyKey(options.params), queryFn: () => hb_getProductJourney(options.params), ...options?.query });
}

export const hb_listSustainabilityMetrics = async (params?: Hb_listSustainabilityMetricsParams, options?: RequestInit): Promise<{ data: HbSustainabilityMetricOut[] }> => {
  const searchParams = new URLSearchParams();
  if (params?.limit != null) searchParams.set("limit", String(params?.limit));
  if (params?.offset != null) searchParams.set("offset", String(params?.offset));
  const queryString = searchParams.toString();
  const url = queryString ? `/api/projects/hb-product-center/supply-chain/sustainability?${queryString}` : `/api/projects/hb-product-center/supply-chain/sustainability`;
  const res = await fetch(url, { ...options, method: "GET" });
  if (!res.ok) {
    const body = await res.text();
    let parsed: unknown;
    try { parsed = JSON.parse(body); } catch { parsed = body; }
    throw new ApiError(res.status, res.statusText, parsed);
  }
  return { data: await res.json() };
};

export const hb_listSustainabilityMetricsKey = (params?: Hb_listSustainabilityMetricsParams) => {
  return ["/api/projects/hb-product-center/supply-chain/sustainability", params] as const;
};

export function useHb_listSustainabilityMetrics<TData = { data: HbSustainabilityMetricOut[] }>(options?: { params?: Hb_listSustainabilityMetricsParams; query?: Omit<UseQueryOptions<{ data: HbSustainabilityMetricOut[] }, ApiError, TData>, "queryKey" | "queryFn"> }) {
  return useQuery({ queryKey: hb_listSustainabilityMetricsKey(options?.params), queryFn: () => hb_listSustainabilityMetrics(options?.params), ...options?.query });
}

export function useHb_listSustainabilityMetricsSuspense<TData = { data: HbSustainabilityMetricOut[] }>(options?: { params?: Hb_listSustainabilityMetricsParams; query?: Omit<UseSuspenseQueryOptions<{ data: HbSustainabilityMetricOut[] }, ApiError, TData>, "queryKey" | "queryFn"> }) {
  return useSuspenseQuery({ queryKey: hb_listSustainabilityMetricsKey(options?.params), queryFn: () => hb_listSustainabilityMetrics(options?.params), ...options?.query });
}

export const hb_getProductSustainability = async (params: Hb_getProductSustainabilityParams, options?: RequestInit): Promise<{ data: HbSustainabilityMetricOut }> => {
  const res = await fetch(`/api/projects/hb-product-center/supply-chain/sustainability/${params.product_id}`, { ...options, method: "GET" });
  if (!res.ok) {
    const body = await res.text();
    let parsed: unknown;
    try { parsed = JSON.parse(body); } catch { parsed = body; }
    throw new ApiError(res.status, res.statusText, parsed);
  }
  return { data: await res.json() };
};

export const hb_getProductSustainabilityKey = (params?: Hb_getProductSustainabilityParams) => {
  return ["/api/projects/hb-product-center/supply-chain/sustainability/{product_id}", params] as const;
};

export function useHb_getProductSustainability<TData = { data: HbSustainabilityMetricOut }>(options: { params: Hb_getProductSustainabilityParams; query?: Omit<UseQueryOptions<{ data: HbSustainabilityMetricOut }, ApiError, TData>, "queryKey" | "queryFn"> }) {
  return useQuery({ queryKey: hb_getProductSustainabilityKey(options.params), queryFn: () => hb_getProductSustainability(options.params), ...options?.query });
}

export function useHb_getProductSustainabilitySuspense<TData = { data: HbSustainabilityMetricOut }>(options: { params: Hb_getProductSustainabilityParams; query?: Omit<UseSuspenseQueryOptions<{ data: HbSustainabilityMetricOut }, ApiError, TData>, "queryKey" | "queryFn"> }) {
  return useSuspenseQuery({ queryKey: hb_getProductSustainabilityKey(options.params), queryFn: () => hb_getProductSustainability(options.params), ...options?.query });
}

export const mac_listAnomalyAlerts = async (params?: Mac_listAnomalyAlertsParams, options?: RequestInit): Promise<{ data: MacAnomalyAlertOut[] }> => {
  const searchParams = new URLSearchParams();
  if (params?.station_id != null) searchParams.set("station_id", String(params?.station_id));
  if (params?.status != null) searchParams.set("status", String(params?.status));
  if (params?.severity != null) searchParams.set("severity", String(params?.severity));
  if (params?.limit != null) searchParams.set("limit", String(params?.limit));
  const queryString = searchParams.toString();
  const url = queryString ? `/api/projects/mol-asm-cockpit/anomalies?${queryString}` : `/api/projects/mol-asm-cockpit/anomalies`;
  const res = await fetch(url, { ...options, method: "GET" });
  if (!res.ok) {
    const body = await res.text();
    let parsed: unknown;
    try { parsed = JSON.parse(body); } catch { parsed = body; }
    throw new ApiError(res.status, res.statusText, parsed);
  }
  return { data: await res.json() };
};

export const mac_listAnomalyAlertsKey = (params?: Mac_listAnomalyAlertsParams) => {
  return ["/api/projects/mol-asm-cockpit/anomalies", params] as const;
};

export function useMac_listAnomalyAlerts<TData = { data: MacAnomalyAlertOut[] }>(options?: { params?: Mac_listAnomalyAlertsParams; query?: Omit<UseQueryOptions<{ data: MacAnomalyAlertOut[] }, ApiError, TData>, "queryKey" | "queryFn"> }) {
  return useQuery({ queryKey: mac_listAnomalyAlertsKey(options?.params), queryFn: () => mac_listAnomalyAlerts(options?.params), ...options?.query });
}

export function useMac_listAnomalyAlertsSuspense<TData = { data: MacAnomalyAlertOut[] }>(options?: { params?: Mac_listAnomalyAlertsParams; query?: Omit<UseSuspenseQueryOptions<{ data: MacAnomalyAlertOut[] }, ApiError, TData>, "queryKey" | "queryFn"> }) {
  return useSuspenseQuery({ queryKey: mac_listAnomalyAlertsKey(options?.params), queryFn: () => mac_listAnomalyAlerts(options?.params), ...options?.query });
}

export const mac_getAnomalyAlert = async (params: Mac_getAnomalyAlertParams, options?: RequestInit): Promise<{ data: MacAnomalyAlertOut }> => {
  const res = await fetch(`/api/projects/mol-asm-cockpit/anomalies/${params.alert_id}`, { ...options, method: "GET" });
  if (!res.ok) {
    const body = await res.text();
    let parsed: unknown;
    try { parsed = JSON.parse(body); } catch { parsed = body; }
    throw new ApiError(res.status, res.statusText, parsed);
  }
  return { data: await res.json() };
};

export const mac_getAnomalyAlertKey = (params?: Mac_getAnomalyAlertParams) => {
  return ["/api/projects/mol-asm-cockpit/anomalies/{alert_id}", params] as const;
};

export function useMac_getAnomalyAlert<TData = { data: MacAnomalyAlertOut }>(options: { params: Mac_getAnomalyAlertParams; query?: Omit<UseQueryOptions<{ data: MacAnomalyAlertOut }, ApiError, TData>, "queryKey" | "queryFn"> }) {
  return useQuery({ queryKey: mac_getAnomalyAlertKey(options.params), queryFn: () => mac_getAnomalyAlert(options.params), ...options?.query });
}

export function useMac_getAnomalyAlertSuspense<TData = { data: MacAnomalyAlertOut }>(options: { params: Mac_getAnomalyAlertParams; query?: Omit<UseSuspenseQueryOptions<{ data: MacAnomalyAlertOut }, ApiError, TData>, "queryKey" | "queryFn"> }) {
  return useSuspenseQuery({ queryKey: mac_getAnomalyAlertKey(options.params), queryFn: () => mac_getAnomalyAlert(options.params), ...options?.query });
}

export const mac_updateAnomalyAlert = async (params: Mac_updateAnomalyAlertParams, data: MacAnomalyAlertUpdate, options?: RequestInit): Promise<{ data: MacAnomalyAlertOut }> => {
  const res = await fetch(`/api/projects/mol-asm-cockpit/anomalies/${params.alert_id}`, { ...options, method: "PATCH", headers: { "Content-Type": "application/json", ...options?.headers }, body: JSON.stringify(data) });
  if (!res.ok) {
    const body = await res.text();
    let parsed: unknown;
    try { parsed = JSON.parse(body); } catch { parsed = body; }
    throw new ApiError(res.status, res.statusText, parsed);
  }
  return { data: await res.json() };
};

export function useMac_updateAnomalyAlert(options?: { mutation?: UseMutationOptions<{ data: MacAnomalyAlertOut }, ApiError, { params: Mac_updateAnomalyAlertParams; data: MacAnomalyAlertUpdate }> }) {
  return useMutation({ mutationFn: (vars) => mac_updateAnomalyAlert(vars.params, vars.data), ...options?.mutation });
}

export const mac_getChatHistory = async (params: Mac_getChatHistoryParams, options?: RequestInit): Promise<{ data: MacChatHistoryOut }> => {
  const res = await fetch(`/api/projects/mol-asm-cockpit/chat/history/${params.session_id}`, { ...options, method: "GET" });
  if (!res.ok) {
    const body = await res.text();
    let parsed: unknown;
    try { parsed = JSON.parse(body); } catch { parsed = body; }
    throw new ApiError(res.status, res.statusText, parsed);
  }
  return { data: await res.json() };
};

export const mac_getChatHistoryKey = (params?: Mac_getChatHistoryParams) => {
  return ["/api/projects/mol-asm-cockpit/chat/history/{session_id}", params] as const;
};

export function useMac_getChatHistory<TData = { data: MacChatHistoryOut }>(options: { params: Mac_getChatHistoryParams; query?: Omit<UseQueryOptions<{ data: MacChatHistoryOut }, ApiError, TData>, "queryKey" | "queryFn"> }) {
  return useQuery({ queryKey: mac_getChatHistoryKey(options.params), queryFn: () => mac_getChatHistory(options.params), ...options?.query });
}

export function useMac_getChatHistorySuspense<TData = { data: MacChatHistoryOut }>(options: { params: Mac_getChatHistoryParams; query?: Omit<UseSuspenseQueryOptions<{ data: MacChatHistoryOut }, ApiError, TData>, "queryKey" | "queryFn"> }) {
  return useSuspenseQuery({ queryKey: mac_getChatHistoryKey(options.params), queryFn: () => mac_getChatHistory(options.params), ...options?.query });
}

export const mac_sendChatMessage = async (data: MacChatMessageIn, params?: Mac_sendChatMessageParams, options?: RequestInit): Promise<{ data: MacChatMessageOut }> => {
  const searchParams = new URLSearchParams();
  if (params?.session_id != null) searchParams.set("session_id", String(params?.session_id));
  const queryString = searchParams.toString();
  const url = queryString ? `/api/projects/mol-asm-cockpit/chat/send?${queryString}` : `/api/projects/mol-asm-cockpit/chat/send`;
  const res = await fetch(url, { ...options, method: "POST", headers: { "Content-Type": "application/json", ...options?.headers }, body: JSON.stringify(data) });
  if (!res.ok) {
    const body = await res.text();
    let parsed: unknown;
    try { parsed = JSON.parse(body); } catch { parsed = body; }
    throw new ApiError(res.status, res.statusText, parsed);
  }
  return { data: await res.json() };
};

export function useMac_sendChatMessage(options?: { mutation?: UseMutationOptions<{ data: MacChatMessageOut }, ApiError, { params: Mac_sendChatMessageParams; data: MacChatMessageIn }> }) {
  return useMutation({ mutationFn: (vars) => mac_sendChatMessage(vars.data, vars.params), ...options?.mutation });
}

export const mac_getDashboardEmbed = async (options?: RequestInit): Promise<{ data: DashboardEmbedOut }> => {
  const res = await fetch("/api/projects/mol-asm-cockpit/dashboard/embed", { ...options, method: "GET" });
  if (!res.ok) {
    const body = await res.text();
    let parsed: unknown;
    try { parsed = JSON.parse(body); } catch { parsed = body; }
    throw new ApiError(res.status, res.statusText, parsed);
  }
  return { data: await res.json() };
};

export const mac_getDashboardEmbedKey = () => {
  return ["/api/projects/mol-asm-cockpit/dashboard/embed"] as const;
};

export function useMac_getDashboardEmbed<TData = { data: DashboardEmbedOut }>(options?: { query?: Omit<UseQueryOptions<{ data: DashboardEmbedOut }, ApiError, TData>, "queryKey" | "queryFn"> }) {
  return useQuery({ queryKey: mac_getDashboardEmbedKey(), queryFn: () => mac_getDashboardEmbed(), ...options?.query });
}

export function useMac_getDashboardEmbedSuspense<TData = { data: DashboardEmbedOut }>(options?: { query?: Omit<UseSuspenseQueryOptions<{ data: DashboardEmbedOut }, ApiError, TData>, "queryKey" | "queryFn"> }) {
  return useSuspenseQuery({ queryKey: mac_getDashboardEmbedKey(), queryFn: () => mac_getDashboardEmbed(), ...options?.query });
}

export const mac_listInventory = async (params?: Mac_listInventoryParams, options?: RequestInit): Promise<{ data: MacInventoryOut[] }> => {
  const searchParams = new URLSearchParams();
  if (params?.station_id != null) searchParams.set("station_id", String(params?.station_id));
  if (params?.product_category != null) searchParams.set("product_category", String(params?.product_category));
  if (params?.days != null) searchParams.set("days", String(params?.days));
  if (params?.limit != null) searchParams.set("limit", String(params?.limit));
  const queryString = searchParams.toString();
  const url = queryString ? `/api/projects/mol-asm-cockpit/inventory?${queryString}` : `/api/projects/mol-asm-cockpit/inventory`;
  const res = await fetch(url, { ...options, method: "GET" });
  if (!res.ok) {
    const body = await res.text();
    let parsed: unknown;
    try { parsed = JSON.parse(body); } catch { parsed = body; }
    throw new ApiError(res.status, res.statusText, parsed);
  }
  return { data: await res.json() };
};

export const mac_listInventoryKey = (params?: Mac_listInventoryParams) => {
  return ["/api/projects/mol-asm-cockpit/inventory", params] as const;
};

export function useMac_listInventory<TData = { data: MacInventoryOut[] }>(options?: { params?: Mac_listInventoryParams; query?: Omit<UseQueryOptions<{ data: MacInventoryOut[] }, ApiError, TData>, "queryKey" | "queryFn"> }) {
  return useQuery({ queryKey: mac_listInventoryKey(options?.params), queryFn: () => mac_listInventory(options?.params), ...options?.query });
}

export function useMac_listInventorySuspense<TData = { data: MacInventoryOut[] }>(options?: { params?: Mac_listInventoryParams; query?: Omit<UseSuspenseQueryOptions<{ data: MacInventoryOut[] }, ApiError, TData>, "queryKey" | "queryFn"> }) {
  return useSuspenseQuery({ queryKey: mac_listInventoryKey(options?.params), queryFn: () => mac_listInventory(options?.params), ...options?.query });
}

export const mac_listCompetitorPrices = async (params?: Mac_listCompetitorPricesParams, options?: RequestInit): Promise<{ data: MacCompetitorPriceOut[] }> => {
  const searchParams = new URLSearchParams();
  if (params?.station_id != null) searchParams.set("station_id", String(params?.station_id));
  if (params?.days != null) searchParams.set("days", String(params?.days));
  if (params?.limit != null) searchParams.set("limit", String(params?.limit));
  const queryString = searchParams.toString();
  const url = queryString ? `/api/projects/mol-asm-cockpit/inventory/competitor-prices?${queryString}` : `/api/projects/mol-asm-cockpit/inventory/competitor-prices`;
  const res = await fetch(url, { ...options, method: "GET" });
  if (!res.ok) {
    const body = await res.text();
    let parsed: unknown;
    try { parsed = JSON.parse(body); } catch { parsed = body; }
    throw new ApiError(res.status, res.statusText, parsed);
  }
  return { data: await res.json() };
};

export const mac_listCompetitorPricesKey = (params?: Mac_listCompetitorPricesParams) => {
  return ["/api/projects/mol-asm-cockpit/inventory/competitor-prices", params] as const;
};

export function useMac_listCompetitorPrices<TData = { data: MacCompetitorPriceOut[] }>(options?: { params?: Mac_listCompetitorPricesParams; query?: Omit<UseQueryOptions<{ data: MacCompetitorPriceOut[] }, ApiError, TData>, "queryKey" | "queryFn"> }) {
  return useQuery({ queryKey: mac_listCompetitorPricesKey(options?.params), queryFn: () => mac_listCompetitorPrices(options?.params), ...options?.query });
}

export function useMac_listCompetitorPricesSuspense<TData = { data: MacCompetitorPriceOut[] }>(options?: { params?: Mac_listCompetitorPricesParams; query?: Omit<UseSuspenseQueryOptions<{ data: MacCompetitorPriceOut[] }, ApiError, TData>, "queryKey" | "queryFn"> }) {
  return useSuspenseQuery({ queryKey: mac_listCompetitorPricesKey(options?.params), queryFn: () => mac_listCompetitorPrices(options?.params), ...options?.query });
}

export const mac_listPriceHistory = async (params?: Mac_listPriceHistoryParams, options?: RequestInit): Promise<{ data: MacPriceHistoryOut[] }> => {
  const searchParams = new URLSearchParams();
  if (params?.station_id != null) searchParams.set("station_id", String(params?.station_id));
  if (params?.fuel_type != null) searchParams.set("fuel_type", String(params?.fuel_type));
  if (params?.days != null) searchParams.set("days", String(params?.days));
  if (params?.limit != null) searchParams.set("limit", String(params?.limit));
  const queryString = searchParams.toString();
  const url = queryString ? `/api/projects/mol-asm-cockpit/inventory/price-history?${queryString}` : `/api/projects/mol-asm-cockpit/inventory/price-history`;
  const res = await fetch(url, { ...options, method: "GET" });
  if (!res.ok) {
    const body = await res.text();
    let parsed: unknown;
    try { parsed = JSON.parse(body); } catch { parsed = body; }
    throw new ApiError(res.status, res.statusText, parsed);
  }
  return { data: await res.json() };
};

export const mac_listPriceHistoryKey = (params?: Mac_listPriceHistoryParams) => {
  return ["/api/projects/mol-asm-cockpit/inventory/price-history", params] as const;
};

export function useMac_listPriceHistory<TData = { data: MacPriceHistoryOut[] }>(options?: { params?: Mac_listPriceHistoryParams; query?: Omit<UseQueryOptions<{ data: MacPriceHistoryOut[] }, ApiError, TData>, "queryKey" | "queryFn"> }) {
  return useQuery({ queryKey: mac_listPriceHistoryKey(options?.params), queryFn: () => mac_listPriceHistory(options?.params), ...options?.query });
}

export function useMac_listPriceHistorySuspense<TData = { data: MacPriceHistoryOut[] }>(options?: { params?: Mac_listPriceHistoryParams; query?: Omit<UseSuspenseQueryOptions<{ data: MacPriceHistoryOut[] }, ApiError, TData>, "queryKey" | "queryFn"> }) {
  return useSuspenseQuery({ queryKey: mac_listPriceHistoryKey(options?.params), queryFn: () => mac_listPriceHistory(options?.params), ...options?.query });
}

export const mac_listFuelSales = async (params?: Mac_listFuelSalesParams, options?: RequestInit): Promise<{ data: MacFuelSaleOut[] }> => {
  const searchParams = new URLSearchParams();
  if (params?.station_id != null) searchParams.set("station_id", String(params?.station_id));
  if (params?.fuel_type != null) searchParams.set("fuel_type", String(params?.fuel_type));
  if (params?.days != null) searchParams.set("days", String(params?.days));
  if (params?.limit != null) searchParams.set("limit", String(params?.limit));
  const queryString = searchParams.toString();
  const url = queryString ? `/api/projects/mol-asm-cockpit/sales/fuel?${queryString}` : `/api/projects/mol-asm-cockpit/sales/fuel`;
  const res = await fetch(url, { ...options, method: "GET" });
  if (!res.ok) {
    const body = await res.text();
    let parsed: unknown;
    try { parsed = JSON.parse(body); } catch { parsed = body; }
    throw new ApiError(res.status, res.statusText, parsed);
  }
  return { data: await res.json() };
};

export const mac_listFuelSalesKey = (params?: Mac_listFuelSalesParams) => {
  return ["/api/projects/mol-asm-cockpit/sales/fuel", params] as const;
};

export function useMac_listFuelSales<TData = { data: MacFuelSaleOut[] }>(options?: { params?: Mac_listFuelSalesParams; query?: Omit<UseQueryOptions<{ data: MacFuelSaleOut[] }, ApiError, TData>, "queryKey" | "queryFn"> }) {
  return useQuery({ queryKey: mac_listFuelSalesKey(options?.params), queryFn: () => mac_listFuelSales(options?.params), ...options?.query });
}

export function useMac_listFuelSalesSuspense<TData = { data: MacFuelSaleOut[] }>(options?: { params?: Mac_listFuelSalesParams; query?: Omit<UseSuspenseQueryOptions<{ data: MacFuelSaleOut[] }, ApiError, TData>, "queryKey" | "queryFn"> }) {
  return useSuspenseQuery({ queryKey: mac_listFuelSalesKey(options?.params), queryFn: () => mac_listFuelSales(options?.params), ...options?.query });
}

export const mac_listLoyaltyMetrics = async (params?: Mac_listLoyaltyMetricsParams, options?: RequestInit): Promise<{ data: MacLoyaltyMetricOut[] }> => {
  const searchParams = new URLSearchParams();
  if (params?.station_id != null) searchParams.set("station_id", String(params?.station_id));
  if (params?.limit != null) searchParams.set("limit", String(params?.limit));
  const queryString = searchParams.toString();
  const url = queryString ? `/api/projects/mol-asm-cockpit/sales/loyalty?${queryString}` : `/api/projects/mol-asm-cockpit/sales/loyalty`;
  const res = await fetch(url, { ...options, method: "GET" });
  if (!res.ok) {
    const body = await res.text();
    let parsed: unknown;
    try { parsed = JSON.parse(body); } catch { parsed = body; }
    throw new ApiError(res.status, res.statusText, parsed);
  }
  return { data: await res.json() };
};

export const mac_listLoyaltyMetricsKey = (params?: Mac_listLoyaltyMetricsParams) => {
  return ["/api/projects/mol-asm-cockpit/sales/loyalty", params] as const;
};

export function useMac_listLoyaltyMetrics<TData = { data: MacLoyaltyMetricOut[] }>(options?: { params?: Mac_listLoyaltyMetricsParams; query?: Omit<UseQueryOptions<{ data: MacLoyaltyMetricOut[] }, ApiError, TData>, "queryKey" | "queryFn"> }) {
  return useQuery({ queryKey: mac_listLoyaltyMetricsKey(options?.params), queryFn: () => mac_listLoyaltyMetrics(options?.params), ...options?.query });
}

export function useMac_listLoyaltyMetricsSuspense<TData = { data: MacLoyaltyMetricOut[] }>(options?: { params?: Mac_listLoyaltyMetricsParams; query?: Omit<UseSuspenseQueryOptions<{ data: MacLoyaltyMetricOut[] }, ApiError, TData>, "queryKey" | "queryFn"> }) {
  return useSuspenseQuery({ queryKey: mac_listLoyaltyMetricsKey(options?.params), queryFn: () => mac_listLoyaltyMetrics(options?.params), ...options?.query });
}

export const mac_listNonfuelSales = async (params?: Mac_listNonfuelSalesParams, options?: RequestInit): Promise<{ data: MacNonfuelSaleOut[] }> => {
  const searchParams = new URLSearchParams();
  if (params?.station_id != null) searchParams.set("station_id", String(params?.station_id));
  if (params?.category != null) searchParams.set("category", String(params?.category));
  if (params?.days != null) searchParams.set("days", String(params?.days));
  if (params?.limit != null) searchParams.set("limit", String(params?.limit));
  const queryString = searchParams.toString();
  const url = queryString ? `/api/projects/mol-asm-cockpit/sales/nonfuel?${queryString}` : `/api/projects/mol-asm-cockpit/sales/nonfuel`;
  const res = await fetch(url, { ...options, method: "GET" });
  if (!res.ok) {
    const body = await res.text();
    let parsed: unknown;
    try { parsed = JSON.parse(body); } catch { parsed = body; }
    throw new ApiError(res.status, res.statusText, parsed);
  }
  return { data: await res.json() };
};

export const mac_listNonfuelSalesKey = (params?: Mac_listNonfuelSalesParams) => {
  return ["/api/projects/mol-asm-cockpit/sales/nonfuel", params] as const;
};

export function useMac_listNonfuelSales<TData = { data: MacNonfuelSaleOut[] }>(options?: { params?: Mac_listNonfuelSalesParams; query?: Omit<UseQueryOptions<{ data: MacNonfuelSaleOut[] }, ApiError, TData>, "queryKey" | "queryFn"> }) {
  return useQuery({ queryKey: mac_listNonfuelSalesKey(options?.params), queryFn: () => mac_listNonfuelSales(options?.params), ...options?.query });
}

export function useMac_listNonfuelSalesSuspense<TData = { data: MacNonfuelSaleOut[] }>(options?: { params?: Mac_listNonfuelSalesParams; query?: Omit<UseSuspenseQueryOptions<{ data: MacNonfuelSaleOut[] }, ApiError, TData>, "queryKey" | "queryFn"> }) {
  return useSuspenseQuery({ queryKey: mac_listNonfuelSalesKey(options?.params), queryFn: () => mac_listNonfuelSales(options?.params), ...options?.query });
}

export const mac_listStations = async (params?: Mac_listStationsParams, options?: RequestInit): Promise<{ data: MacStationOut[] }> => {
  const searchParams = new URLSearchParams();
  if (params?.region_id != null) searchParams.set("region_id", String(params?.region_id));
  if (params?.station_type != null) searchParams.set("station_type", String(params?.station_type));
  const queryString = searchParams.toString();
  const url = queryString ? `/api/projects/mol-asm-cockpit/stations?${queryString}` : `/api/projects/mol-asm-cockpit/stations`;
  const res = await fetch(url, { ...options, method: "GET" });
  if (!res.ok) {
    const body = await res.text();
    let parsed: unknown;
    try { parsed = JSON.parse(body); } catch { parsed = body; }
    throw new ApiError(res.status, res.statusText, parsed);
  }
  return { data: await res.json() };
};

export const mac_listStationsKey = (params?: Mac_listStationsParams) => {
  return ["/api/projects/mol-asm-cockpit/stations", params] as const;
};

export function useMac_listStations<TData = { data: MacStationOut[] }>(options?: { params?: Mac_listStationsParams; query?: Omit<UseQueryOptions<{ data: MacStationOut[] }, ApiError, TData>, "queryKey" | "queryFn"> }) {
  return useQuery({ queryKey: mac_listStationsKey(options?.params), queryFn: () => mac_listStations(options?.params), ...options?.query });
}

export function useMac_listStationsSuspense<TData = { data: MacStationOut[] }>(options?: { params?: Mac_listStationsParams; query?: Omit<UseSuspenseQueryOptions<{ data: MacStationOut[] }, ApiError, TData>, "queryKey" | "queryFn"> }) {
  return useSuspenseQuery({ queryKey: mac_listStationsKey(options?.params), queryFn: () => mac_listStations(options?.params), ...options?.query });
}

export const mac_stationKPIs = async (params?: Mac_stationKPIsParams, options?: RequestInit): Promise<{ data: MacStationKPI[] }> => {
  const searchParams = new URLSearchParams();
  if (params?.days != null) searchParams.set("days", String(params?.days));
  const queryString = searchParams.toString();
  const url = queryString ? `/api/projects/mol-asm-cockpit/stations/kpis?${queryString}` : `/api/projects/mol-asm-cockpit/stations/kpis`;
  const res = await fetch(url, { ...options, method: "GET" });
  if (!res.ok) {
    const body = await res.text();
    let parsed: unknown;
    try { parsed = JSON.parse(body); } catch { parsed = body; }
    throw new ApiError(res.status, res.statusText, parsed);
  }
  return { data: await res.json() };
};

export const mac_stationKPIsKey = (params?: Mac_stationKPIsParams) => {
  return ["/api/projects/mol-asm-cockpit/stations/kpis", params] as const;
};

export function useMac_stationKPIs<TData = { data: MacStationKPI[] }>(options?: { params?: Mac_stationKPIsParams; query?: Omit<UseQueryOptions<{ data: MacStationKPI[] }, ApiError, TData>, "queryKey" | "queryFn"> }) {
  return useQuery({ queryKey: mac_stationKPIsKey(options?.params), queryFn: () => mac_stationKPIs(options?.params), ...options?.query });
}

export function useMac_stationKPIsSuspense<TData = { data: MacStationKPI[] }>(options?: { params?: Mac_stationKPIsParams; query?: Omit<UseSuspenseQueryOptions<{ data: MacStationKPI[] }, ApiError, TData>, "queryKey" | "queryFn"> }) {
  return useSuspenseQuery({ queryKey: mac_stationKPIsKey(options?.params), queryFn: () => mac_stationKPIs(options?.params), ...options?.query });
}

export const mac_listRegions = async (options?: RequestInit): Promise<{ data: MacRegionOut[] }> => {
  const res = await fetch("/api/projects/mol-asm-cockpit/stations/regions", { ...options, method: "GET" });
  if (!res.ok) {
    const body = await res.text();
    let parsed: unknown;
    try { parsed = JSON.parse(body); } catch { parsed = body; }
    throw new ApiError(res.status, res.statusText, parsed);
  }
  return { data: await res.json() };
};

export const mac_listRegionsKey = () => {
  return ["/api/projects/mol-asm-cockpit/stations/regions"] as const;
};

export function useMac_listRegions<TData = { data: MacRegionOut[] }>(options?: { query?: Omit<UseQueryOptions<{ data: MacRegionOut[] }, ApiError, TData>, "queryKey" | "queryFn"> }) {
  return useQuery({ queryKey: mac_listRegionsKey(), queryFn: () => mac_listRegions(), ...options?.query });
}

export function useMac_listRegionsSuspense<TData = { data: MacRegionOut[] }>(options?: { query?: Omit<UseSuspenseQueryOptions<{ data: MacRegionOut[] }, ApiError, TData>, "queryKey" | "queryFn"> }) {
  return useSuspenseQuery({ queryKey: mac_listRegionsKey(), queryFn: () => mac_listRegions(), ...options?.query });
}

export const mac_getStation = async (params: Mac_getStationParams, options?: RequestInit): Promise<{ data: MacStationOut }> => {
  const res = await fetch(`/api/projects/mol-asm-cockpit/stations/${params.station_id}`, { ...options, method: "GET" });
  if (!res.ok) {
    const body = await res.text();
    let parsed: unknown;
    try { parsed = JSON.parse(body); } catch { parsed = body; }
    throw new ApiError(res.status, res.statusText, parsed);
  }
  return { data: await res.json() };
};

export const mac_getStationKey = (params?: Mac_getStationParams) => {
  return ["/api/projects/mol-asm-cockpit/stations/{station_id}", params] as const;
};

export function useMac_getStation<TData = { data: MacStationOut }>(options: { params: Mac_getStationParams; query?: Omit<UseQueryOptions<{ data: MacStationOut }, ApiError, TData>, "queryKey" | "queryFn"> }) {
  return useQuery({ queryKey: mac_getStationKey(options.params), queryFn: () => mac_getStation(options.params), ...options?.query });
}

export function useMac_getStationSuspense<TData = { data: MacStationOut }>(options: { params: Mac_getStationParams; query?: Omit<UseSuspenseQueryOptions<{ data: MacStationOut }, ApiError, TData>, "queryKey" | "queryFn"> }) {
  return useSuspenseQuery({ queryKey: mac_getStationKey(options.params), queryFn: () => mac_getStation(options.params), ...options?.query });
}

export const mac_listCustomerProfiles = async (options?: RequestInit): Promise<{ data: MacCustomerProfileOut[] }> => {
  const res = await fetch("/api/projects/mol-asm-cockpit/workforce/customers", { ...options, method: "GET" });
  if (!res.ok) {
    const body = await res.text();
    let parsed: unknown;
    try { parsed = JSON.parse(body); } catch { parsed = body; }
    throw new ApiError(res.status, res.statusText, parsed);
  }
  return { data: await res.json() };
};

export const mac_listCustomerProfilesKey = () => {
  return ["/api/projects/mol-asm-cockpit/workforce/customers"] as const;
};

export function useMac_listCustomerProfiles<TData = { data: MacCustomerProfileOut[] }>(options?: { query?: Omit<UseQueryOptions<{ data: MacCustomerProfileOut[] }, ApiError, TData>, "queryKey" | "queryFn"> }) {
  return useQuery({ queryKey: mac_listCustomerProfilesKey(), queryFn: () => mac_listCustomerProfiles(), ...options?.query });
}

export function useMac_listCustomerProfilesSuspense<TData = { data: MacCustomerProfileOut[] }>(options?: { query?: Omit<UseSuspenseQueryOptions<{ data: MacCustomerProfileOut[] }, ApiError, TData>, "queryKey" | "queryFn"> }) {
  return useSuspenseQuery({ queryKey: mac_listCustomerProfilesKey(), queryFn: () => mac_listCustomerProfiles(), ...options?.query });
}

export const mac_listCustomerContracts = async (params: Mac_listCustomerContractsParams, options?: RequestInit): Promise<{ data: MacCustomerContractOut[] }> => {
  const res = await fetch(`/api/projects/mol-asm-cockpit/workforce/customers/${params.customer_id}/contracts`, { ...options, method: "GET" });
  if (!res.ok) {
    const body = await res.text();
    let parsed: unknown;
    try { parsed = JSON.parse(body); } catch { parsed = body; }
    throw new ApiError(res.status, res.statusText, parsed);
  }
  return { data: await res.json() };
};

export const mac_listCustomerContractsKey = (params?: Mac_listCustomerContractsParams) => {
  return ["/api/projects/mol-asm-cockpit/workforce/customers/{customer_id}/contracts", params] as const;
};

export function useMac_listCustomerContracts<TData = { data: MacCustomerContractOut[] }>(options: { params: Mac_listCustomerContractsParams; query?: Omit<UseQueryOptions<{ data: MacCustomerContractOut[] }, ApiError, TData>, "queryKey" | "queryFn"> }) {
  return useQuery({ queryKey: mac_listCustomerContractsKey(options.params), queryFn: () => mac_listCustomerContracts(options.params), ...options?.query });
}

export function useMac_listCustomerContractsSuspense<TData = { data: MacCustomerContractOut[] }>(options: { params: Mac_listCustomerContractsParams; query?: Omit<UseSuspenseQueryOptions<{ data: MacCustomerContractOut[] }, ApiError, TData>, "queryKey" | "queryFn"> }) {
  return useSuspenseQuery({ queryKey: mac_listCustomerContractsKey(options.params), queryFn: () => mac_listCustomerContracts(options.params), ...options?.query });
}

export const mac_listIssues = async (params?: Mac_listIssuesParams, options?: RequestInit): Promise<{ data: MacIssueOut[] }> => {
  const searchParams = new URLSearchParams();
  if (params?.station_id != null) searchParams.set("station_id", String(params?.station_id));
  if (params?.status != null) searchParams.set("status", String(params?.status));
  if (params?.category != null) searchParams.set("category", String(params?.category));
  if (params?.limit != null) searchParams.set("limit", String(params?.limit));
  const queryString = searchParams.toString();
  const url = queryString ? `/api/projects/mol-asm-cockpit/workforce/issues?${queryString}` : `/api/projects/mol-asm-cockpit/workforce/issues`;
  const res = await fetch(url, { ...options, method: "GET" });
  if (!res.ok) {
    const body = await res.text();
    let parsed: unknown;
    try { parsed = JSON.parse(body); } catch { parsed = body; }
    throw new ApiError(res.status, res.statusText, parsed);
  }
  return { data: await res.json() };
};

export const mac_listIssuesKey = (params?: Mac_listIssuesParams) => {
  return ["/api/projects/mol-asm-cockpit/workforce/issues", params] as const;
};

export function useMac_listIssues<TData = { data: MacIssueOut[] }>(options?: { params?: Mac_listIssuesParams; query?: Omit<UseQueryOptions<{ data: MacIssueOut[] }, ApiError, TData>, "queryKey" | "queryFn"> }) {
  return useQuery({ queryKey: mac_listIssuesKey(options?.params), queryFn: () => mac_listIssues(options?.params), ...options?.query });
}

export function useMac_listIssuesSuspense<TData = { data: MacIssueOut[] }>(options?: { params?: Mac_listIssuesParams; query?: Omit<UseSuspenseQueryOptions<{ data: MacIssueOut[] }, ApiError, TData>, "queryKey" | "queryFn"> }) {
  return useSuspenseQuery({ queryKey: mac_listIssuesKey(options?.params), queryFn: () => mac_listIssues(options?.params), ...options?.query });
}

export const mac_listWorkforceShifts = async (params?: Mac_listWorkforceShiftsParams, options?: RequestInit): Promise<{ data: MacWorkforceShiftOut[] }> => {
  const searchParams = new URLSearchParams();
  if (params?.station_id != null) searchParams.set("station_id", String(params?.station_id));
  if (params?.days != null) searchParams.set("days", String(params?.days));
  if (params?.limit != null) searchParams.set("limit", String(params?.limit));
  const queryString = searchParams.toString();
  const url = queryString ? `/api/projects/mol-asm-cockpit/workforce/shifts?${queryString}` : `/api/projects/mol-asm-cockpit/workforce/shifts`;
  const res = await fetch(url, { ...options, method: "GET" });
  if (!res.ok) {
    const body = await res.text();
    let parsed: unknown;
    try { parsed = JSON.parse(body); } catch { parsed = body; }
    throw new ApiError(res.status, res.statusText, parsed);
  }
  return { data: await res.json() };
};

export const mac_listWorkforceShiftsKey = (params?: Mac_listWorkforceShiftsParams) => {
  return ["/api/projects/mol-asm-cockpit/workforce/shifts", params] as const;
};

export function useMac_listWorkforceShifts<TData = { data: MacWorkforceShiftOut[] }>(options?: { params?: Mac_listWorkforceShiftsParams; query?: Omit<UseQueryOptions<{ data: MacWorkforceShiftOut[] }, ApiError, TData>, "queryKey" | "queryFn"> }) {
  return useQuery({ queryKey: mac_listWorkforceShiftsKey(options?.params), queryFn: () => mac_listWorkforceShifts(options?.params), ...options?.query });
}

export function useMac_listWorkforceShiftsSuspense<TData = { data: MacWorkforceShiftOut[] }>(options?: { params?: Mac_listWorkforceShiftsParams; query?: Omit<UseSuspenseQueryOptions<{ data: MacWorkforceShiftOut[] }, ApiError, TData>, "queryKey" | "queryFn"> }) {
  return useSuspenseQuery({ queryKey: mac_listWorkforceShiftsKey(options?.params), queryFn: () => mac_listWorkforceShifts(options?.params), ...options?.query });
}

export const vh_send_chat_message = async (params: Vh_send_chat_messageParams, data: VhChatMessageIn, options?: RequestInit): Promise<{ data: unknown }> => {
  const res = await fetch(`/api/projects/vi-home-one/chat/tickets/${params.ticket_id}/chat`, { ...options, method: "POST", headers: { "Content-Type": "application/json", ...options?.headers }, body: JSON.stringify(data) });
  if (!res.ok) {
    const body = await res.text();
    let parsed: unknown;
    try { parsed = JSON.parse(body); } catch { parsed = body; }
    throw new ApiError(res.status, res.statusText, parsed);
  }
  return { data: await res.json() };
};

export function useVh_send_chat_message(options?: { mutation?: UseMutationOptions<{ data: unknown }, ApiError, { params: Vh_send_chat_messageParams; data: VhChatMessageIn }> }) {
  return useMutation({ mutationFn: (vars) => vh_send_chat_message(vars.params, vars.data), ...options?.mutation });
}

export const vh_get_chat_history = async (params: Vh_get_chat_historyParams, options?: RequestInit): Promise<{ data: VhChatHistoryOut }> => {
  const res = await fetch(`/api/projects/vi-home-one/chat/tickets/${params.ticket_id}/history`, { ...options, method: "GET" });
  if (!res.ok) {
    const body = await res.text();
    let parsed: unknown;
    try { parsed = JSON.parse(body); } catch { parsed = body; }
    throw new ApiError(res.status, res.statusText, parsed);
  }
  return { data: await res.json() };
};

export const vh_get_chat_historyKey = (params?: Vh_get_chat_historyParams) => {
  return ["/api/projects/vi-home-one/chat/tickets/{ticket_id}/history", params] as const;
};

export function useVh_get_chat_history<TData = { data: VhChatHistoryOut }>(options: { params: Vh_get_chat_historyParams; query?: Omit<UseQueryOptions<{ data: VhChatHistoryOut }, ApiError, TData>, "queryKey" | "queryFn"> }) {
  return useQuery({ queryKey: vh_get_chat_historyKey(options.params), queryFn: () => vh_get_chat_history(options.params), ...options?.query });
}

export function useVh_get_chat_historySuspense<TData = { data: VhChatHistoryOut }>(options: { params: Vh_get_chat_historyParams; query?: Omit<UseSuspenseQueryOptions<{ data: VhChatHistoryOut }, ApiError, TData>, "queryKey" | "queryFn"> }) {
  return useSuspenseQuery({ queryKey: vh_get_chat_historyKey(options.params), queryFn: () => vh_get_chat_history(options.params), ...options?.query });
}

export const vh_get_current_reading = async (params: Vh_get_current_readingParams, options?: RequestInit): Promise<{ data: VhEnergyReadingOut }> => {
  const res = await fetch(`/api/projects/vi-home-one/energy/households/${params.household_id}/current`, { ...options, method: "GET" });
  if (!res.ok) {
    const body = await res.text();
    let parsed: unknown;
    try { parsed = JSON.parse(body); } catch { parsed = body; }
    throw new ApiError(res.status, res.statusText, parsed);
  }
  return { data: await res.json() };
};

export const vh_get_current_readingKey = (params?: Vh_get_current_readingParams) => {
  return ["/api/projects/vi-home-one/energy/households/{household_id}/current", params] as const;
};

export function useVh_get_current_reading<TData = { data: VhEnergyReadingOut }>(options: { params: Vh_get_current_readingParams; query?: Omit<UseQueryOptions<{ data: VhEnergyReadingOut }, ApiError, TData>, "queryKey" | "queryFn"> }) {
  return useQuery({ queryKey: vh_get_current_readingKey(options.params), queryFn: () => vh_get_current_reading(options.params), ...options?.query });
}

export function useVh_get_current_readingSuspense<TData = { data: VhEnergyReadingOut }>(options: { params: Vh_get_current_readingParams; query?: Omit<UseSuspenseQueryOptions<{ data: VhEnergyReadingOut }, ApiError, TData>, "queryKey" | "queryFn"> }) {
  return useSuspenseQuery({ queryKey: vh_get_current_readingKey(options.params), queryFn: () => vh_get_current_reading(options.params), ...options?.query });
}

export const vh_get_energy_readings = async (params: Vh_get_energy_readingsParams, options?: RequestInit): Promise<{ data: VhEnergyReadingOut[] }> => {
  const searchParams = new URLSearchParams();
  if (params?.hours != null) searchParams.set("hours", String(params?.hours));
  const queryString = searchParams.toString();
  const url = queryString ? `/api/projects/vi-home-one/energy/households/${params.household_id}/readings?${queryString}` : `/api/projects/vi-home-one/energy/households/${params.household_id}/readings`;
  const res = await fetch(url, { ...options, method: "GET" });
  if (!res.ok) {
    const body = await res.text();
    let parsed: unknown;
    try { parsed = JSON.parse(body); } catch { parsed = body; }
    throw new ApiError(res.status, res.statusText, parsed);
  }
  return { data: await res.json() };
};

export const vh_get_energy_readingsKey = (params?: Vh_get_energy_readingsParams) => {
  return ["/api/projects/vi-home-one/energy/households/{household_id}/readings", params] as const;
};

export function useVh_get_energy_readings<TData = { data: VhEnergyReadingOut[] }>(options: { params: Vh_get_energy_readingsParams; query?: Omit<UseQueryOptions<{ data: VhEnergyReadingOut[] }, ApiError, TData>, "queryKey" | "queryFn"> }) {
  return useQuery({ queryKey: vh_get_energy_readingsKey(options.params), queryFn: () => vh_get_energy_readings(options.params), ...options?.query });
}

export function useVh_get_energy_readingsSuspense<TData = { data: VhEnergyReadingOut[] }>(options: { params: Vh_get_energy_readingsParams; query?: Omit<UseSuspenseQueryOptions<{ data: VhEnergyReadingOut[] }, ApiError, TData>, "queryKey" | "queryFn"> }) {
  return useSuspenseQuery({ queryKey: vh_get_energy_readingsKey(options.params), queryFn: () => vh_get_energy_readings(options.params), ...options?.query });
}

export const vh_get_household = async (params: Vh_get_householdParams, options?: RequestInit): Promise<{ data: VhHouseholdOut }> => {
  const res = await fetch(`/api/projects/vi-home-one/households/${params.household_id}`, { ...options, method: "GET" });
  if (!res.ok) {
    const body = await res.text();
    let parsed: unknown;
    try { parsed = JSON.parse(body); } catch { parsed = body; }
    throw new ApiError(res.status, res.statusText, parsed);
  }
  return { data: await res.json() };
};

export const vh_get_householdKey = (params?: Vh_get_householdParams) => {
  return ["/api/projects/vi-home-one/households/{household_id}", params] as const;
};

export function useVh_get_household<TData = { data: VhHouseholdOut }>(options: { params: Vh_get_householdParams; query?: Omit<UseQueryOptions<{ data: VhHouseholdOut }, ApiError, TData>, "queryKey" | "queryFn"> }) {
  return useQuery({ queryKey: vh_get_householdKey(options.params), queryFn: () => vh_get_household(options.params), ...options?.query });
}

export function useVh_get_householdSuspense<TData = { data: VhHouseholdOut }>(options: { params: Vh_get_householdParams; query?: Omit<UseSuspenseQueryOptions<{ data: VhHouseholdOut }, ApiError, TData>, "queryKey" | "queryFn"> }) {
  return useSuspenseQuery({ queryKey: vh_get_householdKey(options.params), queryFn: () => vh_get_household(options.params), ...options?.query });
}

export const vh_get_household_cockpit = async (params: Vh_get_household_cockpitParams, options?: RequestInit): Promise<{ data: VhHouseholdCockpitOut }> => {
  const res = await fetch(`/api/projects/vi-home-one/households/${params.household_id}/cockpit`, { ...options, method: "GET" });
  if (!res.ok) {
    const body = await res.text();
    let parsed: unknown;
    try { parsed = JSON.parse(body); } catch { parsed = body; }
    throw new ApiError(res.status, res.statusText, parsed);
  }
  return { data: await res.json() };
};

export const vh_get_household_cockpitKey = (params?: Vh_get_household_cockpitParams) => {
  return ["/api/projects/vi-home-one/households/{household_id}/cockpit", params] as const;
};

export function useVh_get_household_cockpit<TData = { data: VhHouseholdCockpitOut }>(options: { params: Vh_get_household_cockpitParams; query?: Omit<UseQueryOptions<{ data: VhHouseholdCockpitOut }, ApiError, TData>, "queryKey" | "queryFn"> }) {
  return useQuery({ queryKey: vh_get_household_cockpitKey(options.params), queryFn: () => vh_get_household_cockpit(options.params), ...options?.query });
}

export function useVh_get_household_cockpitSuspense<TData = { data: VhHouseholdCockpitOut }>(options: { params: Vh_get_household_cockpitParams; query?: Omit<UseSuspenseQueryOptions<{ data: VhHouseholdCockpitOut }, ApiError, TData>, "queryKey" | "queryFn"> }) {
  return useSuspenseQuery({ queryKey: vh_get_household_cockpitKey(options.params), queryFn: () => vh_get_household_cockpit(options.params), ...options?.query });
}

export const vh_update_optimization_mode = async (params: Vh_update_optimization_modeParams, data: VhOptimizationModeUpdate, options?: RequestInit): Promise<{ data: VhHouseholdOut }> => {
  const res = await fetch(`/api/projects/vi-home-one/households/${params.household_id}/optimization-mode`, { ...options, method: "PUT", headers: { "Content-Type": "application/json", ...options?.headers }, body: JSON.stringify(data) });
  if (!res.ok) {
    const body = await res.text();
    let parsed: unknown;
    try { parsed = JSON.parse(body); } catch { parsed = body; }
    throw new ApiError(res.status, res.statusText, parsed);
  }
  return { data: await res.json() };
};

export function useVh_update_optimization_mode(options?: { mutation?: UseMutationOptions<{ data: VhHouseholdOut }, ApiError, { params: Vh_update_optimization_modeParams; data: VhOptimizationModeUpdate }> }) {
  return useMutation({ mutationFn: (vars) => vh_update_optimization_mode(vars.params, vars.data), ...options?.mutation });
}

export const vh_acknowledge_alert = async (params: Vh_acknowledge_alertParams, data: VhMaintenanceAlertAcknowledge, options?: RequestInit): Promise<{ data: VhMaintenanceAlertOut }> => {
  const res = await fetch(`/api/projects/vi-home-one/maintenance/alerts/${params.alert_id}/acknowledge`, { ...options, method: "POST", headers: { "Content-Type": "application/json", ...options?.headers }, body: JSON.stringify(data) });
  if (!res.ok) {
    const body = await res.text();
    let parsed: unknown;
    try { parsed = JSON.parse(body); } catch { parsed = body; }
    throw new ApiError(res.status, res.statusText, parsed);
  }
  return { data: await res.json() };
};

export function useVh_acknowledge_alert(options?: { mutation?: UseMutationOptions<{ data: VhMaintenanceAlertOut }, ApiError, { params: Vh_acknowledge_alertParams; data: VhMaintenanceAlertAcknowledge }> }) {
  return useMutation({ mutationFn: (vars) => vh_acknowledge_alert(vars.params, vars.data), ...options?.mutation });
}

export const vh_list_maintenance_alerts = async (params: Vh_list_maintenance_alertsParams, options?: RequestInit): Promise<{ data: VhMaintenanceAlertOut[] }> => {
  const searchParams = new URLSearchParams();
  if (params?.include_acknowledged != null) searchParams.set("include_acknowledged", String(params?.include_acknowledged));
  const queryString = searchParams.toString();
  const url = queryString ? `/api/projects/vi-home-one/maintenance/households/${params.household_id}/alerts?${queryString}` : `/api/projects/vi-home-one/maintenance/households/${params.household_id}/alerts`;
  const res = await fetch(url, { ...options, method: "GET" });
  if (!res.ok) {
    const body = await res.text();
    let parsed: unknown;
    try { parsed = JSON.parse(body); } catch { parsed = body; }
    throw new ApiError(res.status, res.statusText, parsed);
  }
  return { data: await res.json() };
};

export const vh_list_maintenance_alertsKey = (params?: Vh_list_maintenance_alertsParams) => {
  return ["/api/projects/vi-home-one/maintenance/households/{household_id}/alerts", params] as const;
};

export function useVh_list_maintenance_alerts<TData = { data: VhMaintenanceAlertOut[] }>(options: { params: Vh_list_maintenance_alertsParams; query?: Omit<UseQueryOptions<{ data: VhMaintenanceAlertOut[] }, ApiError, TData>, "queryKey" | "queryFn"> }) {
  return useQuery({ queryKey: vh_list_maintenance_alertsKey(options.params), queryFn: () => vh_list_maintenance_alerts(options.params), ...options?.query });
}

export function useVh_list_maintenance_alertsSuspense<TData = { data: VhMaintenanceAlertOut[] }>(options: { params: Vh_list_maintenance_alertsParams; query?: Omit<UseSuspenseQueryOptions<{ data: VhMaintenanceAlertOut[] }, ApiError, TData>, "queryKey" | "queryFn"> }) {
  return useSuspenseQuery({ queryKey: vh_list_maintenance_alertsKey(options.params), queryFn: () => vh_list_maintenance_alerts(options.params), ...options?.query });
}

export const vh_list_neighborhoods = async (options?: RequestInit): Promise<{ data: VhNeighborhoodOut[] }> => {
  const res = await fetch("/api/projects/vi-home-one/neighborhoods", { ...options, method: "GET" });
  if (!res.ok) {
    const body = await res.text();
    let parsed: unknown;
    try { parsed = JSON.parse(body); } catch { parsed = body; }
    throw new ApiError(res.status, res.statusText, parsed);
  }
  return { data: await res.json() };
};

export const vh_list_neighborhoodsKey = () => {
  return ["/api/projects/vi-home-one/neighborhoods"] as const;
};

export function useVh_list_neighborhoods<TData = { data: VhNeighborhoodOut[] }>(options?: { query?: Omit<UseQueryOptions<{ data: VhNeighborhoodOut[] }, ApiError, TData>, "queryKey" | "queryFn"> }) {
  return useQuery({ queryKey: vh_list_neighborhoodsKey(), queryFn: () => vh_list_neighborhoods(), ...options?.query });
}

export function useVh_list_neighborhoodsSuspense<TData = { data: VhNeighborhoodOut[] }>(options?: { query?: Omit<UseSuspenseQueryOptions<{ data: VhNeighborhoodOut[] }, ApiError, TData>, "queryKey" | "queryFn"> }) {
  return useSuspenseQuery({ queryKey: vh_list_neighborhoodsKey(), queryFn: () => vh_list_neighborhoods(), ...options?.query });
}

export const vh_get_neighborhood_summary = async (params: Vh_get_neighborhood_summaryParams, options?: RequestInit): Promise<{ data: VhNeighborhoodSummaryOut }> => {
  const res = await fetch(`/api/projects/vi-home-one/neighborhoods/${params.neighborhood_id}/summary`, { ...options, method: "GET" });
  if (!res.ok) {
    const body = await res.text();
    let parsed: unknown;
    try { parsed = JSON.parse(body); } catch { parsed = body; }
    throw new ApiError(res.status, res.statusText, parsed);
  }
  return { data: await res.json() };
};

export const vh_get_neighborhood_summaryKey = (params?: Vh_get_neighborhood_summaryParams) => {
  return ["/api/projects/vi-home-one/neighborhoods/{neighborhood_id}/summary", params] as const;
};

export function useVh_get_neighborhood_summary<TData = { data: VhNeighborhoodSummaryOut }>(options: { params: Vh_get_neighborhood_summaryParams; query?: Omit<UseQueryOptions<{ data: VhNeighborhoodSummaryOut }, ApiError, TData>, "queryKey" | "queryFn"> }) {
  return useQuery({ queryKey: vh_get_neighborhood_summaryKey(options.params), queryFn: () => vh_get_neighborhood_summary(options.params), ...options?.query });
}

export function useVh_get_neighborhood_summarySuspense<TData = { data: VhNeighborhoodSummaryOut }>(options: { params: Vh_get_neighborhood_summaryParams; query?: Omit<UseSuspenseQueryOptions<{ data: VhNeighborhoodSummaryOut }, ApiError, TData>, "queryKey" | "queryFn"> }) {
  return useSuspenseQuery({ queryKey: vh_get_neighborhood_summaryKey(options.params), queryFn: () => vh_get_neighborhood_summary(options.params), ...options?.query });
}

export const vh_get_optimization_suggestions = async (params: Vh_get_optimization_suggestionsParams, options?: RequestInit): Promise<{ data: VhOptimizationSuggestionOut[] }> => {
  const res = await fetch(`/api/projects/vi-home-one/optimization/households/${params.household_id}/suggestions`, { ...options, method: "GET" });
  if (!res.ok) {
    const body = await res.text();
    let parsed: unknown;
    try { parsed = JSON.parse(body); } catch { parsed = body; }
    throw new ApiError(res.status, res.statusText, parsed);
  }
  return { data: await res.json() };
};

export const vh_get_optimization_suggestionsKey = (params?: Vh_get_optimization_suggestionsParams) => {
  return ["/api/projects/vi-home-one/optimization/households/{household_id}/suggestions", params] as const;
};

export function useVh_get_optimization_suggestions<TData = { data: VhOptimizationSuggestionOut[] }>(options: { params: Vh_get_optimization_suggestionsParams; query?: Omit<UseQueryOptions<{ data: VhOptimizationSuggestionOut[] }, ApiError, TData>, "queryKey" | "queryFn"> }) {
  return useQuery({ queryKey: vh_get_optimization_suggestionsKey(options.params), queryFn: () => vh_get_optimization_suggestions(options.params), ...options?.query });
}

export function useVh_get_optimization_suggestionsSuspense<TData = { data: VhOptimizationSuggestionOut[] }>(options: { params: Vh_get_optimization_suggestionsParams; query?: Omit<UseSuspenseQueryOptions<{ data: VhOptimizationSuggestionOut[] }, ApiError, TData>, "queryKey" | "queryFn"> }) {
  return useSuspenseQuery({ queryKey: vh_get_optimization_suggestionsKey(options.params), queryFn: () => vh_get_optimization_suggestions(options.params), ...options?.query });
}

export const vh_list_providers = async (options?: RequestInit): Promise<{ data: VhEnergyProviderOut[] }> => {
  const res = await fetch("/api/projects/vi-home-one/providers", { ...options, method: "GET" });
  if (!res.ok) {
    const body = await res.text();
    let parsed: unknown;
    try { parsed = JSON.parse(body); } catch { parsed = body; }
    throw new ApiError(res.status, res.statusText, parsed);
  }
  return { data: await res.json() };
};

export const vh_list_providersKey = () => {
  return ["/api/projects/vi-home-one/providers"] as const;
};

export function useVh_list_providers<TData = { data: VhEnergyProviderOut[] }>(options?: { query?: Omit<UseQueryOptions<{ data: VhEnergyProviderOut[] }, ApiError, TData>, "queryKey" | "queryFn"> }) {
  return useQuery({ queryKey: vh_list_providersKey(), queryFn: () => vh_list_providers(), ...options?.query });
}

export function useVh_list_providersSuspense<TData = { data: VhEnergyProviderOut[] }>(options?: { query?: Omit<UseSuspenseQueryOptions<{ data: VhEnergyProviderOut[] }, ApiError, TData>, "queryKey" | "queryFn"> }) {
  return useSuspenseQuery({ queryKey: vh_list_providersKey(), queryFn: () => vh_list_providers(), ...options?.query });
}

export const vh_compare_providers = async (params: Vh_compare_providersParams, options?: RequestInit): Promise<{ data: VhProviderComparisonOut }> => {
  const searchParams = new URLSearchParams();
  if (params.household_id != null) searchParams.set("household_id", String(params.household_id));
  if (params?.current_provider_id != null) searchParams.set("current_provider_id", String(params?.current_provider_id));
  const queryString = searchParams.toString();
  const url = queryString ? `/api/projects/vi-home-one/providers/compare?${queryString}` : `/api/projects/vi-home-one/providers/compare`;
  const res = await fetch(url, { ...options, method: "GET" });
  if (!res.ok) {
    const body = await res.text();
    let parsed: unknown;
    try { parsed = JSON.parse(body); } catch { parsed = body; }
    throw new ApiError(res.status, res.statusText, parsed);
  }
  return { data: await res.json() };
};

export const vh_compare_providersKey = (params?: Vh_compare_providersParams) => {
  return ["/api/projects/vi-home-one/providers/compare", params] as const;
};

export function useVh_compare_providers<TData = { data: VhProviderComparisonOut }>(options: { params: Vh_compare_providersParams; query?: Omit<UseQueryOptions<{ data: VhProviderComparisonOut }, ApiError, TData>, "queryKey" | "queryFn"> }) {
  return useQuery({ queryKey: vh_compare_providersKey(options.params), queryFn: () => vh_compare_providers(options.params), ...options?.query });
}

export function useVh_compare_providersSuspense<TData = { data: VhProviderComparisonOut }>(options: { params: Vh_compare_providersParams; query?: Omit<UseSuspenseQueryOptions<{ data: VhProviderComparisonOut }, ApiError, TData>, "queryKey" | "queryFn"> }) {
  return useSuspenseQuery({ queryKey: vh_compare_providersKey(options.params), queryFn: () => vh_compare_providers(options.params), ...options?.query });
}

export const vh_list_tickets = async (params?: Vh_list_ticketsParams, options?: RequestInit): Promise<{ data: VhTicketOut[] }> => {
  const searchParams = new URLSearchParams();
  if (params?.household_id != null) searchParams.set("household_id", String(params?.household_id));
  if (params?.status != null) searchParams.set("status", String(params?.status));
  const queryString = searchParams.toString();
  const url = queryString ? `/api/projects/vi-home-one/tickets?${queryString}` : `/api/projects/vi-home-one/tickets`;
  const res = await fetch(url, { ...options, method: "GET" });
  if (!res.ok) {
    const body = await res.text();
    let parsed: unknown;
    try { parsed = JSON.parse(body); } catch { parsed = body; }
    throw new ApiError(res.status, res.statusText, parsed);
  }
  return { data: await res.json() };
};

export const vh_list_ticketsKey = (params?: Vh_list_ticketsParams) => {
  return ["/api/projects/vi-home-one/tickets", params] as const;
};

export function useVh_list_tickets<TData = { data: VhTicketOut[] }>(options?: { params?: Vh_list_ticketsParams; query?: Omit<UseQueryOptions<{ data: VhTicketOut[] }, ApiError, TData>, "queryKey" | "queryFn"> }) {
  return useQuery({ queryKey: vh_list_ticketsKey(options?.params), queryFn: () => vh_list_tickets(options?.params), ...options?.query });
}

export function useVh_list_ticketsSuspense<TData = { data: VhTicketOut[] }>(options?: { params?: Vh_list_ticketsParams; query?: Omit<UseSuspenseQueryOptions<{ data: VhTicketOut[] }, ApiError, TData>, "queryKey" | "queryFn"> }) {
  return useSuspenseQuery({ queryKey: vh_list_ticketsKey(options?.params), queryFn: () => vh_list_tickets(options?.params), ...options?.query });
}

export const vh_create_ticket = async (params: Vh_create_ticketParams, data: VhTicketIn, options?: RequestInit): Promise<{ data: VhTicketOut }> => {
  const searchParams = new URLSearchParams();
  if (params.household_id != null) searchParams.set("household_id", String(params.household_id));
  const queryString = searchParams.toString();
  const url = queryString ? `/api/projects/vi-home-one/tickets?${queryString}` : `/api/projects/vi-home-one/tickets`;
  const res = await fetch(url, { ...options, method: "POST", headers: { "Content-Type": "application/json", ...options?.headers }, body: JSON.stringify(data) });
  if (!res.ok) {
    const body = await res.text();
    let parsed: unknown;
    try { parsed = JSON.parse(body); } catch { parsed = body; }
    throw new ApiError(res.status, res.statusText, parsed);
  }
  return { data: await res.json() };
};

export function useVh_create_ticket(options?: { mutation?: UseMutationOptions<{ data: VhTicketOut }, ApiError, { params: Vh_create_ticketParams; data: VhTicketIn }> }) {
  return useMutation({ mutationFn: (vars) => vh_create_ticket(vars.params, vars.data), ...options?.mutation });
}

export const vh_get_ticket = async (params: Vh_get_ticketParams, options?: RequestInit): Promise<{ data: VhTicketOut }> => {
  const res = await fetch(`/api/projects/vi-home-one/tickets/${params.ticket_id}`, { ...options, method: "GET" });
  if (!res.ok) {
    const body = await res.text();
    let parsed: unknown;
    try { parsed = JSON.parse(body); } catch { parsed = body; }
    throw new ApiError(res.status, res.statusText, parsed);
  }
  return { data: await res.json() };
};

export const vh_get_ticketKey = (params?: Vh_get_ticketParams) => {
  return ["/api/projects/vi-home-one/tickets/{ticket_id}", params] as const;
};

export function useVh_get_ticket<TData = { data: VhTicketOut }>(options: { params: Vh_get_ticketParams; query?: Omit<UseQueryOptions<{ data: VhTicketOut }, ApiError, TData>, "queryKey" | "queryFn"> }) {
  return useQuery({ queryKey: vh_get_ticketKey(options.params), queryFn: () => vh_get_ticket(options.params), ...options?.query });
}

export function useVh_get_ticketSuspense<TData = { data: VhTicketOut }>(options: { params: Vh_get_ticketParams; query?: Omit<UseSuspenseQueryOptions<{ data: VhTicketOut }, ApiError, TData>, "queryKey" | "queryFn"> }) {
  return useSuspenseQuery({ queryKey: vh_get_ticketKey(options.params), queryFn: () => vh_get_ticket(options.params), ...options?.query });
}

export const vh_update_ticket = async (params: Vh_update_ticketParams, data: VhTicketUpdate, options?: RequestInit): Promise<{ data: VhTicketOut }> => {
  const res = await fetch(`/api/projects/vi-home-one/tickets/${params.ticket_id}`, { ...options, method: "PATCH", headers: { "Content-Type": "application/json", ...options?.headers }, body: JSON.stringify(data) });
  if (!res.ok) {
    const body = await res.text();
    let parsed: unknown;
    try { parsed = JSON.parse(body); } catch { parsed = body; }
    throw new ApiError(res.status, res.statusText, parsed);
  }
  return { data: await res.json() };
};

export function useVh_update_ticket(options?: { mutation?: UseMutationOptions<{ data: VhTicketOut }, ApiError, { params: Vh_update_ticketParams; data: VhTicketUpdate }> }) {
  return useMutation({ mutationFn: (vars) => vh_update_ticket(vars.params, vars.data), ...options?.mutation });
}

export const vh_upload_ticket_media = async (params: Vh_upload_ticket_mediaParams, data: FormData, options?: RequestInit): Promise<{ data: unknown }> => {
  const res = await fetch(`/api/projects/vi-home-one/tickets/${params.ticket_id}/media`, { ...options, method: "POST", headers: { ...options?.headers }, body: data });
  if (!res.ok) {
    const body = await res.text();
    let parsed: unknown;
    try { parsed = JSON.parse(body); } catch { parsed = body; }
    throw new ApiError(res.status, res.statusText, parsed);
  }
  return { data: await res.json() };
};

export function useVh_upload_ticket_media(options?: { mutation?: UseMutationOptions<{ data: unknown }, ApiError, { params: Vh_upload_ticket_mediaParams; data: FormData }> }) {
  return useMutation({ mutationFn: (vars) => vh_upload_ticket_media(vars.params, vars.data), ...options?.mutation });
}

export const getProject = async (params: GetProjectParams, options?: RequestInit): Promise<{ data: ProjectOut }> => {
  const res = await fetch(`/api/projects/${params.slug}`, { ...options, method: "GET" });
  if (!res.ok) {
    const body = await res.text();
    let parsed: unknown;
    try { parsed = JSON.parse(body); } catch { parsed = body; }
    throw new ApiError(res.status, res.statusText, parsed);
  }
  return { data: await res.json() };
};

export const getProjectKey = (params?: GetProjectParams) => {
  return ["/api/projects/{slug}", params] as const;
};

export function useGetProject<TData = { data: ProjectOut }>(options: { params: GetProjectParams; query?: Omit<UseQueryOptions<{ data: ProjectOut }, ApiError, TData>, "queryKey" | "queryFn"> }) {
  return useQuery({ queryKey: getProjectKey(options.params), queryFn: () => getProject(options.params), ...options?.query });
}

export function useGetProjectSuspense<TData = { data: ProjectOut }>(options: { params: GetProjectParams; query?: Omit<UseSuspenseQueryOptions<{ data: ProjectOut }, ApiError, TData>, "queryKey" | "queryFn"> }) {
  return useSuspenseQuery({ queryKey: getProjectKey(options.params), queryFn: () => getProject(options.params), ...options?.query });
}

export const seedDatabase = async (options?: RequestInit): Promise<{ data: unknown }> => {
  const res = await fetch("/api/seed", { ...options, method: "POST" });
  if (!res.ok) {
    const body = await res.text();
    let parsed: unknown;
    try { parsed = JSON.parse(body); } catch { parsed = body; }
    throw new ApiError(res.status, res.statusText, parsed);
  }
  return { data: await res.json() };
};

export function useSeedDatabase(options?: { mutation?: UseMutationOptions<{ data: unknown }, ApiError, void> }) {
  return useMutation({ mutationFn: () => seedDatabase(), ...options?.mutation });
}

export const version = async (options?: RequestInit): Promise<{ data: VersionOut }> => {
  const res = await fetch("/api/version", { ...options, method: "GET" });
  if (!res.ok) {
    const body = await res.text();
    let parsed: unknown;
    try { parsed = JSON.parse(body); } catch { parsed = body; }
    throw new ApiError(res.status, res.statusText, parsed);
  }
  return { data: await res.json() };
};

export const versionKey = () => {
  return ["/api/version"] as const;
};

export function useVersion<TData = { data: VersionOut }>(options?: { query?: Omit<UseQueryOptions<{ data: VersionOut }, ApiError, TData>, "queryKey" | "queryFn"> }) {
  return useQuery({ queryKey: versionKey(), queryFn: () => version(), ...options?.query });
}

export function useVersionSuspense<TData = { data: VersionOut }>(options?: { query?: Omit<UseSuspenseQueryOptions<{ data: VersionOut }, ApiError, TData>, "queryKey" | "queryFn"> }) {
  return useSuspenseQuery({ queryKey: versionKey(), queryFn: () => version(), ...options?.query });
}

