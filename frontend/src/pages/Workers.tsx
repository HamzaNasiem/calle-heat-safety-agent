import { useState, useEffect } from 'react'
import { getSites, getWorkers, createWorker, deleteWorker } from '../lib/api'
import DirectCallModal from '../components/DirectCallModal'
import CalleLiveModal from '../components/CalleLiveModal'
import type { Site, Worker } from '../types'

export default function Workers() {
  const [sites, setSites] = useState<Site[]>([])
  const [selectedSiteId, setSelectedSiteId] = useState<string>('')
  const [workers, setWorkers] = useState<Worker[]>([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)
  
  // Enroll Modal State
  const [showEnrollModal, setShowEnrollModal] = useState(false)
  const [name, setName] = useState('')
  const [phone, setPhone] = useState('')
  const [lang, setLang] = useState<'en' | 'ur'>('en')
  const [enrolling, setEnrolling] = useState(false)

  // Direct Call Modal & Live Stream State
  const [directCallTarget, setDirectCallTarget] = useState<{ name: string; phone: string } | null>(null)
  const [activeCalleCallId, setActiveCalleCallId] = useState<string | null>(null)
  const [deletingId, setDeletingId] = useState<string | null>(null)

  useEffect(() => {
    getSites().then((data) => {
      setSites(data)
      if (data.length > 0) {
        setSelectedSiteId(data[0].id)
      }
    }).catch((err) => {
      setError(err.message || 'Failed to load sites')
    })
  }, [])

  function loadWorkers(siteId: string) {
    if (!siteId) return
    setLoading(true)
    setError(null)
    getWorkers(siteId)
      .then(setWorkers)
      .catch((err) => {
        setError(err.message || 'Failed to load workers')
      })
      .finally(() => setLoading(false))
  }

  useEffect(() => {
    if (selectedSiteId) {
      loadWorkers(selectedSiteId)
    }
  }, [selectedSiteId])

  async function handleEnrollWorker(e: React.FormEvent) {
    e.preventDefault()
    if (!name || !phone || !selectedSiteId) return
    setEnrolling(true)
    try {
      await createWorker({
        site_id: selectedSiteId,
        name,
        phone_number: phone,
        preferred_language: lang,
      })
      setName('')
      setShowEnrollModal(false)
      loadWorkers(selectedSiteId)
    } catch (err: any) {
      alert(err.message || 'Failed to enroll worker')
    } finally {
      setEnrolling(false)
    }
  }

  async function handleDeleteWorker(worker: Worker) {
    if (!window.confirm(`Are you sure you want to remove worker "${worker.name}" from heat safety coverage?`)) {
      return
    }
    setDeletingId(worker.id)
    try {
      await deleteWorker(worker.id)
      setWorkers((prev) => prev.filter((w) => w.id !== worker.id))
    } catch (err: any) {
      alert(err.message || 'Failed to delete worker')
    } finally {
      setDeletingId(null)
    }
  }

  const selectedSite = sites.find((s) => s.id === selectedSiteId)

  return (
    <div className="space-y-6 font-sans">
      {/* Top Banner */}
      <div className="card-surface p-4 sm:p-5 flex flex-col sm:flex-row sm:items-center sm:justify-between gap-3.5">
        <div>
          <h1 className="text-sm sm:text-base font-bold text-[#141414]">
            Enrolled Field Personnel Roster
          </h1>
          <p className="text-[11px] sm:text-xs text-slate-500 font-medium mt-0.5">
            Workers Receiving Autonomous Voice & SMS Alerts During Extreme Heat
          </p>
        </div>

        <div className="grid grid-cols-1 sm:flex sm:items-center gap-2 w-full sm:w-auto">
          <button
            onClick={() => setDirectCallTarget({ name: '', phone: '' })}
            className="btn-secondary w-full sm:w-auto"
          >
            <svg className="w-3.5 h-3.5 text-sky-600 shrink-0" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M3 5a2 2 0 012-2h3.28a1 1 0 01.948.684l1.498 4.493a1 1 0 01-.502 1.21l-2.257 1.13a11.042 11.042 0 005.516 5.516l1.13-2.257a1 1 0 011.21-.502l4.493 1.498a1 1 0 01.684.949V19a2 2 0 01-2 2h-1C9.716 21 3 14.284 3 6V5z" />
            </svg>
            <span>Test CALL-E Voice Call</span>
          </button>

          <button
            onClick={() => setShowEnrollModal(true)}
            className="btn-primary w-full sm:w-auto"
          >
            <svg className="w-4 h-4 shrink-0" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 4v16m8-8H4" />
            </svg>
            <span>Enroll New Worker</span>
          </button>
        </div>
      </div>

      {/* Site Selector Toolbar */}
      <div className="card-surface p-3.5 sm:p-4 flex flex-wrap items-center justify-between gap-3 text-xs">
        <div className="flex items-center gap-2 max-w-full">
          <span className="text-slate-500 font-semibold shrink-0">Work Site:</span>
          <select
            value={selectedSiteId}
            onChange={(e) => setSelectedSiteId(e.target.value)}
            className="bg-[#f4f4f4] text-[#141414] border border-[#e5e5e5] rounded-xl px-2.5 py-1.5 text-xs font-semibold focus:outline-none focus:border-slate-400 cursor-pointer max-w-[200px] sm:max-w-xs truncate"
          >
            {sites.map((s) => (
              <option key={s.id} value={s.id}>{s.name}</option>
            ))}
          </select>
        </div>

        <div className="text-slate-600 text-xs font-medium">
          Personnel on Site: <span className="font-bold text-[#141414] text-sm tabular-nums">{workers.length}</span>
        </div>
      </div>

      {/* Error Alert */}
      {error && (
        <div className="card-surface p-4 rounded-xl bg-rose-50 border border-rose-200 text-rose-800 text-xs flex items-center justify-between shadow-sm">
          <span className="font-medium">⚠️ {error}</span>
          <button onClick={() => selectedSiteId && loadWorkers(selectedSiteId)} className="btn-primary text-xs py-1 px-3">
            Retry
          </button>
        </div>
      )}

      {/* Workers Roster Grid */}
      {loading ? (
        <div className="card-surface p-8 text-center text-xs text-slate-400 font-medium animate-pulse">
          Syncing field personnel for {selectedSite?.name}...
        </div>
      ) : workers.length === 0 ? (
        <div className="card-surface p-12 text-center space-y-3">
          <p className="text-sm font-bold text-[#141414]">No Personnel Enrolled for this Site</p>
          <p className="text-xs text-slate-500 font-medium">
            Click "Enroll New Worker" to assign field workers to {selectedSite?.name}.
          </p>
        </div>
      ) : (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-5">
          {workers.map((worker) => (
            <div
              key={worker.id}
              className="card-surface p-5 space-y-4 flex flex-col justify-between hover:border-slate-300 hover:shadow-md transition-all"
            >
              <div className="space-y-3">
                <div className="flex items-start justify-between gap-2 border-b border-[#e5e5e5] pb-3">
                  <div className="flex items-center gap-3">
                    <div className="w-8 h-8 rounded-xl bg-slate-100 border border-slate-200 text-slate-800 flex items-center justify-center font-bold text-xs">
                      {worker.name.charAt(0)}
                    </div>
                    <div>
                      <h4 className="font-bold text-sm text-[#141414] leading-tight">
                        {worker.name}
                      </h4>
                      <span className="text-[11px] text-slate-500 font-mono block mt-0.5">
                        {worker.phone_number}
                      </span>
                    </div>
                  </div>

                  <span className="badge-emerald text-[10px] font-bold">
                    Safe
                  </span>
                </div>

                <div className="space-y-2 text-xs text-slate-600">
                  <div className="flex justify-between">
                    <span className="text-slate-500 font-medium">Voice Language:</span>
                    <span className="font-bold uppercase text-[#141414]">{worker.preferred_language || 'en'}</span>
                  </div>
                  <div className="flex justify-between">
                    <span className="text-slate-500 font-medium">Safety Consent:</span>
                    <span className="font-bold text-emerald-700">✓ Enrolled & Consented</span>
                  </div>
                  <div className="flex justify-between">
                    <span className="text-slate-500 font-medium">Assigned Plot:</span>
                    <span className="font-semibold text-slate-800 truncate max-w-[160px]">
                      {selectedSite?.name.split('(')[0]}
                    </span>
                  </div>
                </div>
              </div>

              {/* Action Buttons */}
              <div className="flex items-center gap-2 pt-3 border-t border-[#e5e5e5]">
                <button
                  onClick={() => setDirectCallTarget({ name: worker.name, phone: worker.phone_number })}
                  className="flex-1 btn-secondary text-xs py-2 font-semibold"
                >
                  Direct Call
                </button>

                <button
                  onClick={() => handleDeleteWorker(worker)}
                  disabled={deletingId === worker.id}
                  className="py-2 px-3 rounded-xl bg-rose-50 hover:bg-rose-100 text-rose-700 border border-rose-200 text-xs font-bold transition-all"
                  title="Remove worker from site"
                >
                  {deletingId === worker.id ? '...' : 'Remove'}
                </button>
              </div>
            </div>
          ))}
        </div>
      )}

      {/* Enroll Worker Modal */}
      {showEnrollModal && (
        <div className="fixed inset-0 z-[9999] flex items-center justify-center p-4 bg-black/60 backdrop-blur-sm animate-fade-in">
          <div className="bg-[#ffffff] text-[#141414] border border-slate-200 rounded-2xl max-w-md w-full p-5 space-y-4 shadow-2xl">
            <div className="flex items-center justify-between border-b border-slate-200 pb-3">
              <div className="flex items-center gap-2.5">
                <div className="w-7 h-7 rounded-lg bg-slate-100 flex items-center justify-center text-slate-700 font-bold text-xs">
                  👷
                </div>
                <h3 className="font-bold text-[#141414] text-sm">Enroll Field Worker</h3>
              </div>
              <button onClick={() => setShowEnrollModal(false)} className="text-slate-400 hover:text-[#141414] text-lg font-bold">
                ✕
              </button>
            </div>

            <form onSubmit={handleEnrollWorker} className="space-y-3.5 text-xs">
              <div>
                <label className="block text-[10px] text-slate-500 font-semibold uppercase mb-1">Full Name</label>
                <input
                  type="text"
                  required
                  placeholder="e.g. Carlos Rodriguez"
                  value={name}
                  onChange={(e) => setName(e.target.value)}
                  className="w-full bg-[#f9fafb] border border-slate-200 text-[#141414] rounded-xl px-3.5 py-2 text-xs focus:outline-none focus:border-slate-400"
                />
              </div>

              <div>
                <label className="block text-[10px] text-slate-500 font-semibold uppercase mb-1">Phone Number (E.164 format)</label>
                <input
                  type="text"
                  required
                  placeholder="+923172532350"
                  value={phone}
                  onChange={(e) => setPhone(e.target.value)}
                  className="w-full bg-[#f9fafb] border border-slate-200 text-[#141414] rounded-xl px-3.5 py-2 text-xs font-mono focus:outline-none focus:border-slate-400"
                />
              </div>

              <div>
                <label className="block text-[10px] text-slate-500 font-semibold uppercase mb-1">Voice Dispatch Language</label>
                <select
                  value={lang}
                  onChange={(e) => setLang(e.target.value as any)}
                  className="w-full bg-[#f9fafb] border border-slate-200 text-[#141414] rounded-xl px-3.5 py-2 text-xs focus:outline-none focus:border-slate-400"
                >
                  <option value="en">English (International Standard Dispatch)</option>
                </select>
              </div>

              <div className="flex items-center justify-between pt-3 border-t border-slate-200">
                <button type="button" onClick={() => setShowEnrollModal(false)} className="btn-secondary">
                  Cancel
                </button>
                <button type="submit" disabled={enrolling} className="btn-primary">
                  {enrolling ? 'Enrolling...' : 'Save Worker'}
                </button>
              </div>
            </form>
          </div>
        </div>
      )}

      {/* Live Stream Telemetry Modal */}
      {activeCalleCallId && (
        <CalleLiveModal
          callId={activeCalleCallId}
          onClose={() => setActiveCalleCallId(null)}
        />
      )}

      {/* Direct Call Modal */}
      {directCallTarget && (
        <DirectCallModal
          initialWorkerName={directCallTarget.name}
          initialPhoneNumber={directCallTarget.phone}
          onClose={() => setDirectCallTarget(null)}
          onTrackCall={(callId) => {
            setDirectCallTarget(null)
            setActiveCalleCallId(callId)
          }}
        />
      )}
    </div>
  )
}
