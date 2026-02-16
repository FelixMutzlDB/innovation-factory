import { useQuery, useSuspenseQuery, useMutation } from "@tanstack/react-query";
import type { UseQueryOptions, UseSuspenseQueryOptions, UseMutationOptions } from "@tanstack/react-query";

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
  author_role: UserRole;
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

export interface DatabricksResourcesOut {
  dashboard_embed_url: string;
  dashboard_id: string;
  genie_space_id: string;
  mas_endpoint_name: string;
  mas_tile_id: string;
  warehouse_id: string;
  workspace_url: string;
}

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

export interface HTTPValidationError {
  detail?: ValidationError[];
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

export interface ProjectOut {
  color?: string | null;
  company: string;
  description: string;
  icon?: string | null;
  id: number;
  name: string;
  slug: string;
}

export const RuleConditionType = {
  threshold: "threshold",
  trend: "trend",
  deviation: "deviation",
} as const;

export type RuleConditionType = (typeof RuleConditionType)[keyof typeof RuleConditionType];

export const UserRole = {
  customer: "customer",
  technician: "technician",
  system: "system",
} as const;

export type UserRole = (typeof UserRole)[keyof typeof UserRole];

export interface ValidationError {
  ctx?: Record<string, unknown>;
  input?: unknown;
  loc: (string | number)[];
  msg: string;
  type: string;
}

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

export interface CurrentUserParams {
  "X-Forwarded-Access-Token"?: string | null;
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

