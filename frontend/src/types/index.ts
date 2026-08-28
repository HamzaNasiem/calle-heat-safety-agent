export interface Site {
  id: string
  name: string
  polygon_geojson: GeoJSONPolygon
  extreme_threshold_f: number
  elevated_threshold_f: number
  poll_interval_minutes: number
  manager_id: string | null
  created_at: string
}

export interface GeoJSONPolygon {
  type: 'Polygon'
  coordinates: number[][][]
}

export interface SiteCreatePayload {
  name: string
  polygon_geojson: GeoJSONPolygon
  elevated_threshold_f?: number
  extreme_threshold_f?: number
  poll_interval_minutes?: number
  manager_id?: string | null
}

export interface Worker {
  id: string
  site_id: string
  name: string
  phone_number: string
  preferred_language: 'ur' | 'en' | string
  status: 'safe' | 'elevated' | 'notified' | 'acknowledged' | string
  consented_at: string | null
  created_at: string
}

export interface WorkerCreatePayload {
  site_id: string
  name: string
  phone_number: string
  preferred_language?: 'ur' | 'en' | string
}

export interface HeatSnapshot {
  id: string
  site_id: string
  fortyguard_activity_id: string | null
  temperature_f: number
  analysis_layer: 'snapshot' | 'exceedance' | 'persistence' | string
  risk_level: 'normal' | 'elevated' | 'extreme' | string
  raw_response?: any
  captured_at: string
}

export interface ActionLog {
  id: string
  worker_id: string
  heat_snapshot_id: string | null
  channel: 'voice' | 'sms' | string
  provider_ref: string | null
  status: 'queued' | 'delivered' | 'failed' | 'acknowledged' | string
  transcript: string | null
  created_at: string
}

export interface TriggerCheckResponse {
  snapshot_id: string
  risk_level: string
  temperature_f: number
  triggered_at: string
  alerts_dispatched: boolean
}

export type RiskLevel = 'normal' | 'elevated' | 'extreme'

export interface MicrocellDetail {
  id: string
  row: number
  col: number
  lat: number
  lng: number
  temp_f: number
  temp_c: number
  surface_temp_f: number
  surface_type: 'asphalt' | 'concrete' | 'shaded_canopy' | 'green_buffer' | 'soil' | string
  solar_exposure: 'direct_sun' | 'partial_shade' | 'full_canopy_shade' | string
  solar_radiation_w_m2: number
  wbgt_f?: number
  surface_heat_delta_f?: number
  albedo?: number
  hydration_l_hr?: number
  work_rest_cycle?: string
  is_hotspot: boolean
  is_refuge: boolean
}

export interface MicroclimateAnalysis {
  site_id: string
  site_name: string
  ambient_temp_f: number
  surface_temp_f: number
  uhi_delta_f: number
  solar_radiation_w_m2: number
  hotspot_zone: string
  cooling_refuge: string
  recommended_shift_distance_m: number
  cooling_delta_f: number
  action_plan: string
  microcells: MicrocellDetail[]
  vector_origin_lat: number
  vector_origin_lng: number
  vector_target_lat: number
  vector_target_lng: number
  compass_bearing_deg?: number
  compass_direction?: string
  wbgt_reduction_pct?: number
  fortyguard_max_temp_c?: number | null
  fortyguard_mean_temp_c?: number | null
  fortyguard_n_cells?: number
  fortyguard_activity_id?: string
  is_satellite_verified?: boolean
}

export interface HourlyForecastPoint {
  time_label: string
  hour: number
  ambient_temp_f: number
  surface_temp_f: number
  canopy_temp_f: number
  wbgt_f: number
  solar_radiation_w_m2: number
  risk_level: string
  work_rest_ratio: string
  hydration_liters_per_hour: number
  point_type?: 'recorded' | 'forecast' | string
  snapshot_id?: string | null
}

export interface HourlyForecastResponse {
  site_id: string
  site_name: string
  peak_hour: string
  peak_surface_temp_f: number
  points: HourlyForecastPoint[]
}

export interface DirectCallPayload {
  phone_number: string
  worker_name: string
}

export interface DirectCallResponse {
  call_id: string
  status: string
  phone_number: string
  worker_name: string
  message: string
}

export interface CalleCallRecipient {
  id?: string
  name?: string
  phones?: string[]
  structured_result?: any
  summary?: string
  status?: string
  [key: string]: any
}

export interface CalleCallData {
  id: string
  status: string
  task?: string
  summary?: string
  recipients?: CalleCallRecipient[]
  created_at?: string
  completed_at?: string
  duration_seconds?: number
  [key: string]: any
}

export interface CalleCallStatusResponse {
  call: CalleCallData
  events?: Record<string, any>
}

export interface FortyGuardCreditSummary {
  total_available_credits?: number
  total_remaining_credits?: number
  total_consumed_credits?: number
}

export interface FortyGuardPlanDetails {
  plan_type?: string
  status?: string
  valid_until?: string
}

export interface FortyGuardUsageResponse {
  credit_summary?: FortyGuardCreditSummary
  plan_details?: FortyGuardPlanDetails
  [key: string]: any
}

export interface HealthCheckResponse {
  status: string
  service: string
}