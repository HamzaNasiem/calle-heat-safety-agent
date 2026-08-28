import type {
  Site,
  Worker,
  HeatSnapshot,
  ActionLog,
  TriggerCheckResponse,
  HourlyForecastResponse,
  MicroclimateAnalysis,
  SiteCreatePayload,
  WorkerCreatePayload,
  DirectCallPayload,
  DirectCallResponse,
  CalleCallStatusResponse,
  FortyGuardUsageResponse,
  HealthCheckResponse,
} from '../types'

export const API_BASE = String((import.meta as any).env?.VITE_API_BASE || 'https://thermashift-ai.onrender.com').replace(/\/$/, '')

/**
 * Universal JSON response handler that extracts FastAPI error detail messages
 */
async function handleResponse<T>(res: Response, fallbackErrorMsg: string): Promise<T> {
  if (!res.ok) {
    const errData = await res.json().catch(() => ({ detail: res.statusText }))
    const detailMsg = typeof errData.detail === 'string'
      ? errData.detail
      : Array.isArray(errData.detail)
      ? errData.detail.map((d: any) => d.msg || JSON.stringify(d)).join(', ')
      : res.statusText || fallbackErrorMsg
    throw new Error(detailMsg || fallbackErrorMsg)
  }
  return res.json()
}

export async function getHealthCheck(): Promise<HealthCheckResponse> {
  const res = await fetch(`${API_BASE}/health`)
  return handleResponse<HealthCheckResponse>(res, 'Failed to verify backend health')
}

export async function getSites(): Promise<Site[]> {
  const res = await fetch(`${API_BASE}/sites`)
  return handleResponse<Site[]>(res, 'Failed to fetch sites')
}

export async function getSite(siteId: string): Promise<Site> {
  const res = await fetch(`${API_BASE}/sites/${siteId}`)
  return handleResponse<Site>(res, 'Failed to fetch site')
}

export async function createSite(payload: SiteCreatePayload): Promise<Site> {
  const res = await fetch(`${API_BASE}/sites`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(payload),
  })
  return handleResponse<Site>(res, 'Failed to create site')
}

export async function deleteSite(siteId: string): Promise<void> {
  const res = await fetch(`${API_BASE}/sites/${siteId}`, { method: 'DELETE' })
  if (!res.ok) {
    const errData = await res.json().catch(() => ({ detail: res.statusText }))
    throw new Error(errData.detail || `Failed to delete site: ${res.statusText}`)
  }
}

export async function getWorkers(siteId?: string): Promise<Worker[]> {
  const url = siteId ? `${API_BASE}/workers?site_id=${siteId}` : `${API_BASE}/workers`
  const res = await fetch(url)
  return handleResponse<Worker[]>(res, 'Failed to fetch workers')
}

export async function getWorker(workerId: string): Promise<Worker> {
  const res = await fetch(`${API_BASE}/workers/${workerId}`)
  return handleResponse<Worker>(res, 'Failed to fetch worker')
}

export async function createWorker(payload: WorkerCreatePayload): Promise<Worker> {
  const res = await fetch(`${API_BASE}/workers`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(payload),
  })
  return handleResponse<Worker>(res, 'Failed to create worker')
}

export async function deleteWorker(workerId: string): Promise<void> {
  const res = await fetch(`${API_BASE}/workers/${workerId}`, { method: 'DELETE' })
  if (!res.ok) {
    const errData = await res.json().catch(() => ({ detail: res.statusText }))
    throw new Error(errData.detail || `Failed to delete worker: ${res.statusText}`)
  }
}

export async function getLatestHeat(siteId: string): Promise<HeatSnapshot | null> {
  const res = await fetch(`${API_BASE}/heat?site_id=${siteId}`)
  if (res.status === 404) return null
  return handleResponse<HeatSnapshot>(res, 'Failed to fetch heat snapshot')
}

export async function getHeatHistory(siteId: string, limit = 20): Promise<HeatSnapshot[]> {
  const res = await fetch(`${API_BASE}/heat/history?site_id=${siteId}&limit=${limit}`)
  return handleResponse<HeatSnapshot[]>(res, 'Failed to fetch heat history')
}

export async function getMicroclimateAnalysis(siteId: string): Promise<MicroclimateAnalysis> {
  const res = await fetch(`${API_BASE}/heat/microclimate?site_id=${siteId}`)
  return handleResponse<MicroclimateAnalysis>(res, 'Failed to fetch microclimate analysis')
}

export async function getHourlyForecast(siteId: string): Promise<HourlyForecastResponse> {
  const res = await fetch(`${API_BASE}/heat/hourly-forecast?site_id=${siteId}`)
  return handleResponse<HourlyForecastResponse>(res, 'Failed to fetch hourly forecast')
}

export async function getAlerts(siteId?: string, limit = 20): Promise<ActionLog[]> {
  const params = new URLSearchParams()
  if (siteId) params.append('site_id', siteId)
  if (limit) params.append('limit', String(limit))
  const queryString = params.toString() ? `?${params.toString()}` : ''
  const url = `${API_BASE}/alerts${queryString}`
  const res = await fetch(url)
  return handleResponse<ActionLog[]>(res, 'Failed to fetch alerts')
}

export async function triggerCheck(siteId: string, forceExtreme = false): Promise<TriggerCheckResponse> {
  const url = `${API_BASE}/internal/trigger-check?site_id=${siteId}&force_extreme=${forceExtreme}`
  const res = await fetch(url, { method: 'POST' })
  return handleResponse<TriggerCheckResponse>(res, 'Trigger check failed')
}

export async function triggerDirectCall(payload: DirectCallPayload): Promise<DirectCallResponse> {
  const res = await fetch(`${API_BASE}/internal/calle/direct-call`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(payload),
  })
  return handleResponse<DirectCallResponse>(res, 'CALL-E direct call failed')
}

export async function getCalleCallStatus(callId: string): Promise<CalleCallStatusResponse> {
  const res = await fetch(`${API_BASE}/internal/calle/call/${callId}`)
  return handleResponse<CalleCallStatusResponse>(res, 'Failed to fetch call status')
}

export async function getFortyGuardUsage(): Promise<FortyGuardUsageResponse> {
  const res = await fetch(`${API_BASE}/internal/fortyguard/usage`)
  return handleResponse<FortyGuardUsageResponse>(res, 'Failed to fetch FortyGuard usage')
}

export async function getFortyGuardEnvParams(payload: {
  latitude: number
  longitude: number
  temperature: number
  target_date?: string
  target_time?: string
}): Promise<any> {
  const res = await fetch(`${API_BASE}/internal/fortyguard/env-params`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(payload),
  })
  return handleResponse<any>(res, 'Failed to fetch FortyGuard environmental parameters')
}

