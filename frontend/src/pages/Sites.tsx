import { useState, useEffect } from 'react'
import { useNavigate } from 'react-router-dom'
import { getSites, getWorkers, deleteSite } from '../lib/api'
import RegisterSiteModal from '../components/RegisterSiteModal'
import type { Site, Worker } from '../types'

export default function Sites() {
  const [sites, setSites] = useState<Site[]>([])
  const [workers, setWorkers] = useState<Worker[]>([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)
  const [showModal, setShowModal] = useState(false)
  const [deletingId, setDeletingId] = useState<string | null>(null)
  const navigate = useNavigate()

  function loadData() {
    setLoading(true)
    setError(null)
    Promise.all([getSites(), getWorkers()])
      .then(([sitesData, workersData]) => {
        setSites(sitesData)
        setWorkers(workersData)
      })
      .catch((err) => {
        setError(err.message || 'Failed to sync job sites')
      })
      .finally(() => setLoading(false))
  }

  useEffect(() => {
    loadData()
  }, [])

  async function handleDeleteSite(site: Site) {
    if (!window.confirm(`Are you sure you want to remove "${site.name}" from autonomous heat monitoring?`)) {
      return
    }
    setDeletingId(site.id)
    try {
      await deleteSite(site.id)
      setSites((prev) => prev.filter((s) => s.id !== site.id))
      setWorkers((prev) => prev.filter((w) => w.site_id !== site.id))
    } catch (err: any) {
      alert(err.message || 'Failed to delete site')
    } finally {
      setDeletingId(null)
    }
  }

  return (
    <div className="space-y-6 font-sans">
      {/* Header Bar */}
      <div className="card-surface p-4 sm:p-5 flex flex-col sm:flex-row sm:items-center sm:justify-between gap-3.5">
        <div>
          <h1 className="text-sm sm:text-base font-bold text-[#141414]">
            Registered Geo-Fenced Work Sites
          </h1>
          <p className="text-[11px] sm:text-xs text-slate-500 font-medium mt-0.5">
            Hyperlocal Industrial & Construction Polygons Monitored 24/7 by FortyGuard AI
          </p>
        </div>

        <button
          onClick={() => setShowModal(true)}
          className="btn-primary w-full sm:w-auto"
        >
          <svg className="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 4v16m8-8H4" />
          </svg>
          <span>Register New Work Site</span>
        </button>
      </div>

      {/* Error Alert */}
      {error && (
        <div className="card-surface p-4 rounded-xl bg-rose-50 border border-rose-200 text-rose-800 text-xs flex items-center justify-between shadow-sm">
          <span className="font-medium">⚠️ {error}</span>
          <button onClick={loadData} className="btn-primary text-xs py-1 px-3">
            Retry
          </button>
        </div>
      )}

      {/* Sites Grid */}
      {loading ? (
        <div className="card-surface p-8 text-center text-xs text-slate-400 font-medium animate-pulse">
          Syncing registered job sites...
        </div>
      ) : sites.length === 0 ? (
        <div className="card-surface p-12 text-center space-y-3">
          <p className="text-sm font-bold text-[#141414]">No Work Sites Registered</p>
          <p className="text-xs text-slate-500 font-medium">
            Click "Register New Work Site" to add outdoor job sites.
          </p>
        </div>
      ) : (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-5">
          {sites.map((site) => {
            const siteWorkers = workers.filter((w) => w.site_id === site.id)

            return (
              <div
                key={site.id}
                className="card-surface p-5 flex flex-col justify-between space-y-4 hover:border-slate-300 hover:shadow-md transition-all"
              >
                <div className="space-y-3 text-xs">
                  <div className="flex items-start justify-between gap-2 border-b border-[#e5e5e5] pb-3">
                    <div>
                      <h3 className="font-bold text-[#141414] text-sm leading-tight">
                        {site.name}
                      </h3>
                      <span className="text-[10px] text-slate-400 font-mono block mt-0.5">
                        ID: {site.id.slice(0, 8)}...
                      </span>
                    </div>
                    <span className="badge-emerald text-[10px] font-bold shrink-0">
                      Active Feed
                    </span>
                  </div>

                  <div className="space-y-2 text-xs text-slate-600">
                    <div className="flex justify-between">
                      <span className="text-slate-500 font-medium">Protected Personnel:</span>
                      <span className="font-bold text-[#141414]">{siteWorkers.length} workers</span>
                    </div>
                    <div className="flex justify-between">
                      <span className="text-slate-500 font-medium">Caution Threshold:</span>
                      <span className="font-bold text-amber-600">{site.elevated_threshold_f}°F</span>
                    </div>
                    <div className="flex justify-between">
                      <span className="text-slate-500 font-medium">Extreme Hazard:</span>
                      <span className="font-bold text-rose-600">{site.extreme_threshold_f}°F</span>
                    </div>
                    <div className="flex justify-between">
                      <span className="text-slate-500 font-medium">Auto-Poll Interval:</span>
                      <span className="font-bold text-[#141414]">{site.poll_interval_minutes || 10} min</span>
                    </div>
                  </div>
                </div>

                {/* Action Buttons */}
                <div className="flex items-center gap-2 pt-3 border-t border-[#e5e5e5]">
                  <button
                    onClick={() => navigate(`/?site_id=${site.id}`)}
                    className="flex-1 btn-primary text-xs py-2"
                  >
                    Open Live Radar
                  </button>

                  <button
                    onClick={() => handleDeleteSite(site)}
                    disabled={deletingId === site.id}
                    className="py-2 px-3 rounded-xl bg-rose-50 hover:bg-rose-100 text-rose-700 border border-rose-200 text-xs font-bold transition-all"
                    title="Remove this work site from monitoring"
                  >
                    {deletingId === site.id ? '...' : 'Remove'}
                  </button>
                </div>
              </div>
            )
          })}
        </div>
      )}

      {/* Register Site Modal */}
      {showModal && (
        <RegisterSiteModal
          onSiteCreated={() => {
            loadData()
            setShowModal(false)
          }}
          onClose={() => setShowModal(false)}
        />
      )}
    </div>
  )
}
