import { useEffect, useState, useCallback, useRef } from 'react'
import { getLatestHeat, getAlerts, getWorkers } from '../lib/api'
import type { HeatSnapshot, ActionLog, Worker } from '../types'

interface CachedLiveHeat {
  snapshot: HeatSnapshot | null
  alerts: ActionLog[]
  workers: Worker[]
  lastUpdated: Date
}

const liveHeatCache = new Map<string, CachedLiveHeat>()

export interface LiveHeatData {
  snapshot: HeatSnapshot | null
  alerts: ActionLog[]
  workers: Worker[]
  loading: boolean
  error: string | null
  lastUpdated: Date | null
  refetch: () => Promise<void>
}

export function useLiveHeat(siteId: string, intervalMs = 20_000): LiveHeatData {
  const cached = siteId ? liveHeatCache.get(siteId) : undefined

  const [snapshot, setSnapshot] = useState<HeatSnapshot | null>(cached?.snapshot ?? null)
  const [alerts, setAlerts] = useState<ActionLog[]>(cached?.alerts ?? [])
  const [workers, setWorkers] = useState<Worker[]>(cached?.workers ?? [])
  const [loading, setLoading] = useState<boolean>(!cached)
  const [error, setError] = useState<string | null>(null)
  const [lastUpdated, setLastUpdated] = useState<Date | null>(cached?.lastUpdated ?? null)

  const activeSiteRef = useRef(siteId)
  activeSiteRef.current = siteId

  // Synchronize state when siteId changes
  useEffect(() => {
    if (!siteId) {
      setSnapshot(null)
      setAlerts([])
      setWorkers([])
      setLoading(false)
      setError(null)
      setLastUpdated(null)
      return
    }

    const currentCache = liveHeatCache.get(siteId)
    if (currentCache) {
      setSnapshot(currentCache.snapshot)
      setAlerts(currentCache.alerts)
      setWorkers(currentCache.workers)
      setLastUpdated(currentCache.lastUpdated)
      setLoading(false)
    } else {
      setSnapshot(null)
      setAlerts([])
      setWorkers([])
      setLoading(true)
    }
  }, [siteId])

  const fetchAll = useCallback(async () => {
    if (!siteId) return
    const targetSiteId = siteId

    try {
      const [heat, alertData, workerData] = await Promise.allSettled([
        getLatestHeat(targetSiteId),
        getAlerts(targetSiteId, 20),
        getWorkers(targetSiteId),
      ])

      // Guard against race conditions if siteId changed during in-flight network request
      if (activeSiteRef.current !== targetSiteId) return

      const nextSnapshot = heat.status === 'fulfilled' ? heat.value : null
      const nextAlerts = alertData.status === 'fulfilled' ? alertData.value : []
      const nextWorkers = workerData.status === 'fulfilled' ? workerData.value : []
      const now = new Date()

      setSnapshot(nextSnapshot)
      setAlerts(nextAlerts)
      setWorkers(nextWorkers)
      setError(null)
      setLastUpdated(now)

      liveHeatCache.set(targetSiteId, {
        snapshot: nextSnapshot,
        alerts: nextAlerts,
        workers: nextWorkers,
        lastUpdated: now,
      })
    } catch (err) {
      if (activeSiteRef.current === targetSiteId) {
        setError(err instanceof Error ? err.message : 'Unknown error')
      }
    } finally {
      if (activeSiteRef.current === targetSiteId) {
        setLoading(false)
      }
    }
  }, [siteId])

  useEffect(() => {
    if (!siteId) return

    fetchAll()
    const id = setInterval(fetchAll, intervalMs)
    return () => clearInterval(id)
  }, [fetchAll, intervalMs, siteId])

  return { snapshot, alerts, workers, loading, error, lastUpdated, refetch: fetchAll }
}

