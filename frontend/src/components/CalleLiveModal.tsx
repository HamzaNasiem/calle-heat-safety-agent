import { useEffect, useState, useRef } from 'react'
import { getCalleCallStatus } from '../lib/api'
import type { CalleCallData } from '../types'

interface CalleLiveModalProps {
  callId: string
  onClose: () => void
}

const TERMINAL_STATUSES = new Set(['completed', 'failed', 'canceled', 'ended', 'busy', 'no_answer'])

export default function CalleLiveModal({ callId, onClose }: CalleLiveModalProps) {
  const [data, setData] = useState<CalleCallData | null>(null)
  const [events, setEvents] = useState<any[]>([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)
  const isMountedRef = useRef(true)

  useEffect(() => {
    isMountedRef.current = true
    let intervalId: any = null

    async function fetchStatus() {
      try {
        const json = await getCalleCallStatus(callId)
        if (!isMountedRef.current) return
        setData(json.call)
        if (json.events?.data && Array.isArray(json.events.data)) {
          setEvents(json.events.data)
        }
        setError(null)

        // Clear interval if call has reached a terminal status
        if (json.call?.status && TERMINAL_STATUSES.has(json.call.status.toLowerCase())) {
          if (intervalId) clearInterval(intervalId)
        }
      } catch (err: any) {
        if (isMountedRef.current) {
          setError(err.message)
        }
      } finally {
        if (isMountedRef.current) {
          setLoading(false)
        }
      }
    }

    fetchStatus()
    intervalId = setInterval(fetchStatus, 3000)

    return () => {
      isMountedRef.current = false
      if (intervalId) clearInterval(intervalId)
    }
  }, [callId])

  // Extract structured verification results
  const structuredResult = data?.structured_result || data?.recipients?.[0]?.structured_result
  const workerAcknowledged = structuredResult?.worker_acknowledged ?? structuredResult?.received_clearly

  return (
    <div className="fixed inset-0 z-[9999] flex items-center justify-center p-3 sm:p-6 bg-black/60 backdrop-blur-sm animate-fade-in font-sans">
      <div className="bg-[#ffffff] text-[#141414] border border-slate-200 rounded-2xl max-w-xl w-full max-h-[88vh] flex flex-col shadow-2xl overflow-hidden">
        {/* Header */}
        <div className="shrink-0 p-4 border-b border-slate-200 flex items-center justify-between bg-[#ffffff]">
          <div className="flex items-center gap-2.5">
            <div className="w-8 h-8 rounded-lg bg-emerald-50 border border-emerald-200 flex items-center justify-center text-emerald-700 font-bold">
              <svg className="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M3 5a2 2 0 012-2h3.28a1 1 0 01.948.684l1.498 4.493a1 1 0 01-.502 1.21l-2.257 1.13a11.042 11.042 0 005.516 5.516l1.13-2.257a1 1 0 011.21-.502l4.493 1.498a1 1 0 01.684.949V19a2 2 0 01-2 2h-1C9.716 21 3 14.284 3 6V5z" />
              </svg>
            </div>
            <div>
              <h2 className="text-sm font-bold text-[#141414]">
                CALL-E Autonomous Voice Dispatch
              </h2>
              <p className="text-[11px] text-slate-500 font-medium">
                Live Outbound Call Stream: api.heycall-e.com
              </p>
            </div>
          </div>

          <button
            onClick={onClose}
            className="text-slate-400 hover:text-[#141414] text-lg font-bold"
          >
            ✕
          </button>
        </div>

        {/* Live Call Telemetry */}
        <div className="flex-1 overflow-y-auto p-5 space-y-4 text-xs">
          {loading && !data && (
            <div className="py-8 text-center text-xs text-slate-400 animate-pulse font-medium">
              Connecting to CALL-E server stream...
            </div>
          )}

          {error && (
            <div className="p-3 rounded-xl bg-rose-50 border border-rose-200 text-rose-700 text-xs font-medium">
              {error}
            </div>
          )}

          {data && (
            <div className="space-y-4">
              {/* Status Pills */}
              <div className="grid grid-cols-2 sm:grid-cols-3 gap-2.5 text-xs">
                <div className="bg-[#f9fafb] p-2.5 rounded-xl border border-slate-200">
                  <span className="text-[10px] text-slate-500 font-medium block">Call ID</span>
                  <span className="font-bold text-[#141414] truncate block font-mono text-[11px]">{data.id}</span>
                </div>
                <div className="bg-[#f9fafb] p-2.5 rounded-xl border border-slate-200">
                  <span className="text-[10px] text-slate-500 font-medium block">Live Status</span>
                  <span className={`font-bold uppercase ${data.status === 'completed' ? 'text-emerald-700' : data.status === 'failed' ? 'text-rose-600' : 'text-amber-600 animate-pulse'}`}>
                    ● {data.status}
                  </span>
                </div>
                <div className="bg-[#f9fafb] p-2.5 rounded-xl border border-slate-200 col-span-2 sm:col-span-1">
                  <span className="text-[10px] text-slate-500 font-medium block">Recipient</span>
                  <span className="font-bold text-[#141414] font-mono text-[11px]">
                    {data.recipients?.[0]?.phones?.[0] || 'Worker'}
                  </span>
                </div>
              </div>

              {/* Task Instruction */}
              <div className="bg-[#f9fafb] rounded-2xl p-3.5 border border-slate-200 space-y-1">
                <span className="text-[10px] uppercase font-bold text-slate-600 block">
                  CALL-E Voice Mission Instruction:
                </span>
                <p className="text-xs text-slate-800 leading-relaxed font-medium">
                  {data.task || 'Autonomous bilingual emergency heat evacuation warning.'}
                </p>
              </div>

              {/* Structured Output Verification */}
              {workerAcknowledged !== undefined && (
                <div className={`rounded-2xl p-3.5 border space-y-1 ${
                  workerAcknowledged
                    ? 'bg-emerald-50 border-emerald-200 text-emerald-900'
                    : 'bg-amber-50 border-amber-200 text-amber-900'
                }`}>
                  <div className="flex items-center justify-between">
                    <span className="text-[10px] font-bold uppercase block">
                      Structured Output Verification:
                    </span>
                    <span className={`badge-emerald text-[10px] font-bold uppercase ${workerAcknowledged ? 'bg-emerald-600 text-white' : 'bg-amber-600 text-white'}`}>
                      {workerAcknowledged ? 'Worker Acknowledged (True)' : 'Pending / Unacknowledged'}
                    </span>
                  </div>
                  <p className="text-[11px] font-medium">
                    {workerAcknowledged
                      ? 'Worker verbally confirmed understanding heat hazards and moving to shade.'
                      : 'Awaiting affirmative worker voice confirmation.'}
                  </p>
                </div>
              )}

              {/* Live Transcript / Summary */}
              {data.summary && (
                <div className="bg-emerald-50 border border-emerald-200 rounded-2xl p-3.5 space-y-1">
                  <span className="text-[10px] font-bold text-emerald-800 uppercase block">
                    ✓ Structured Call Summary:
                  </span>
                  <p className="text-xs text-emerald-950 leading-relaxed font-medium">
                    {data.summary}
                  </p>
                </div>
              )}

              {/* Live Telephony Events Stream */}
              {events.length > 0 && (
                <div className="bg-[#f9fafb] rounded-2xl p-3.5 border border-slate-200 space-y-2">
                  <div className="flex items-center justify-between">
                    <span className="text-[10px] font-bold text-slate-700 uppercase block">
                      Telephony Event Stream ({events.length})
                    </span>
                    <span className="text-[10px] text-slate-400 font-mono">Live Sync</span>
                  </div>
                  <div className="space-y-1.5 max-h-40 overflow-y-auto pr-1">
                    {events.map((evt, idx) => (
                      <div key={evt.id || idx} className="p-2 rounded-lg bg-white border border-slate-200 text-[11px] flex items-start justify-between gap-2">
                        <div className="space-y-0.5 min-w-0">
                          <span className="font-mono font-bold text-slate-800 block truncate">
                            {evt.type || evt.message}
                          </span>
                          {evt.message && evt.message !== evt.type && (
                            <span className="text-[10px] text-slate-500 block truncate">{evt.message}</span>
                          )}
                        </div>
                        {evt.created_at && (
                          <span className="text-[10px] text-slate-400 shrink-0 font-mono">
                            {new Date(evt.created_at).toLocaleTimeString()}
                          </span>
                        )}
                      </div>
                    ))}
                  </div>
                </div>
              )}
            </div>
          )}
        </div>

        {/* Footer */}
        <div className="shrink-0 p-3.5 border-t border-slate-200 flex items-center justify-between bg-[#ffffff]">
          <span className="text-[11px] text-slate-500 font-medium">
            Verified CALL-E Telephony
          </span>
          <button
            onClick={onClose}
            className="btn-secondary font-semibold"
          >
            Close Stream
          </button>
        </div>
      </div>
    </div>
  )
}
