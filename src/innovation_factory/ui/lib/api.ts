import { useQuery, useSuspenseQuery, useMutation } from "@tanstack/react-query";
import type { UseQueryOptions, UseSuspenseQueryOptions, UseMutationOptions } from "@tanstack/react-query";

export const AlertSeverity = {
  low: "low",
  medium: "medium",
  high: "high",
  critical: "critical",
} as const;

export type AlertSeverity = (typeof AlertSeverity)[keyof typeof AlertSeverity];

export const AlertStatus = {
  active: "active",
  acknowledged: "acknowledged",
  resolved: "resolved",
  dismissed: "dismissed",
} as const;

export type AlertStatus = (typeof AlertStatus)[keyof typeof AlertStatus];

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

export const ConsumptionCategory = {
  household_appliances: "household_appliances",
  climate_control: "climate_control",
  ev_charging: "ev_charging",
  garden: "garden",
  other: "other",
} as const;

export type ConsumptionCategory = (typeof ConsumptionCategory)[keyof typeof ConsumptionCategory];

export interface DashboardEmbedOut {
  configured?: boolean;
  dashboard_id?: string | null;
  embed_url?: string | null;
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

export const IssueCategory = {
  equipment: "equipment",
  supply_chain: "supply_chain",
  quality: "quality",
  customer_complaint: "customer_complaint",
  staffing: "staffing",
  safety: "safety",
  it_system: "it_system",
} as const;

export type IssueCategory = (typeof IssueCategory)[keyof typeof IssueCategory];

export const IssueStatus = {
  open: "open",
  in_progress: "in_progress",
  resolved: "resolved",
  closed: "closed",
} as const;

export type IssueStatus = (typeof IssueStatus)[keyof typeof IssueStatus];

export const LoyaltyTier = {
  bronze: "bronze",
  silver: "silver",
  gold: "gold",
  platinum: "platinum",
} as const;

export type LoyaltyTier = (typeof LoyaltyTier)[keyof typeof LoyaltyTier];

export interface MacAnomalyAlertOut {
  description: string;
  detected_at: string;
  id: number;
  metric_type: string;
  resolved_at?: string | null;
  severity: AlertSeverity;
  station_id: number;
  status: AlertStatus;
  suggested_action: string;
  title: string;
}

export interface MacAnomalyAlertUpdate {
  resolved_at?: string | null;
  status?: AlertStatus | null;
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
  product_category: ProductCategory;
  record_date: string;
  reorder_point: number;
  spoilage_count: number;
  station_id: number;
  stock_level: number;
  stock_out_events: number;
}

export interface MacIssueOut {
  category: IssueCategory;
  created_at: string;
  description: string;
  id: number;
  priority: number;
  resolution?: string | null;
  resolved_at?: string | null;
  station_id: number;
  status: IssueStatus;
  title: string;
}

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

export const ProductCategory = {
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

export type ProductCategory = (typeof ProductCategory)[keyof typeof ProductCategory];

export interface ProjectOut {
  color?: string | null;
  company: string;
  description: string;
  icon?: string | null;
  id: number;
  name: string;
  slug: string;
}

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

