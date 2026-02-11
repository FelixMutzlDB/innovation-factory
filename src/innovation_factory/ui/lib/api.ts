import { useQuery, useSuspenseQuery, useMutation } from "@tanstack/react-query";
import type { UseQueryOptions, UseSuspenseQueryOptions, UseMutationOptions } from "@tanstack/react-query";

export const AlertSeverity = {
  low: "low",
  medium: "medium",
  high: "high",
  critical: "critical",
} as const;

export type AlertSeverity = (typeof AlertSeverity)[keyof typeof AlertSeverity];

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

export const OptimizationMode = {
  energy_saver: "energy_saver",
  cost_saver: "cost_saver",
} as const;

export type OptimizationMode = (typeof OptimizationMode)[keyof typeof OptimizationMode];

export interface ProjectOut {
  color?: string | null;
  company: string;
  description: string;
  icon?: string | null;
  id: number;
  name: string;
  slug: string;
}

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

