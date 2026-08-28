import { useState } from 'react'
import { triggerDirectCall } from '../lib/api'

interface DirectCallModalProps {
  initialWorkerName?: string
  initialPhoneNumber?: string
  onClose: () => void
  onTrackCall?: (callId: string) => void
}

export default function DirectCallModal({
  initialWorkerName = '',
  initialPhoneNumber = '',
  onClose,
  onTrackCall,
}: DirectCallModalProps) {
  const [phoneNumber, setPhoneNumber] = useState(initialPhoneNumber)
  const [workerName, setWorkerName] = useState(initialWorkerName)
  const [loading, setLoading] = useState(false)
  const [result, setResult] = useState<any>(null)
  const [error, setError] = useState<string | null>(null)

  async function handleCall() {
    if (!phoneNumber) return
    setLoading(true)
    setError(null)
    setResult(null)

    try {
      const data = await triggerDirectCall({
        phone_number: phoneNumber,
        worker_name: workerName || 'Field Worker',
      })
      setResult(data)
    } catch (err: any) {
      setError(err.message)
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="fixed inset-0 z-[9999] flex items-center justify-center p-3 sm:p-6 bg-black/60 backdrop-blur-sm animate-fade-in font-sans">
      <div className="bg-[#ffffff] text-[#141414] border border-slate-200 rounded-2xl max-w-md w-full max-h-[88vh] flex flex-col shadow-2xl overflow-hidden">
        <div className="p-4 border-b border-slate-200 flex items-center justify-between bg-[#ffffff]">
          <div className="flex items-center gap-2.5">
            <div className="w-8 h-8 rounded-lg bg-sky-50 border border-sky-200 flex items-center justify-center text-sky-700 font-bold">
              <svg className="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M3 5a2 2 0 012-2h3.28a1 1 0 01.948.684l1.498 4.493a1 1 0 01-.502 1.21l-2.257 1.13a11.042 11.042 0 005.516 5.516l1.13-2.257a1 1 0 011.21-.502l4.493 1.498a1 1 0 01.684.949V19a2 2 0 01-2 2h-1C9.716 21 3 14.284 3 6V5z" />
              </svg>
            </div>
            <div>
              <h2 className="text-sm font-bold text-[#141414]">
                Dial Real Mobile Phone via CALL-E
              </h2>
              <p className="text-[11px] text-slate-500 font-medium">
                Live Outbound Call Dispatch
              </p>
            </div>
          </div>
          <button onClick={onClose} className="text-slate-400 hover:text-[#141414] text-lg font-bold">
            ✕
          </button>
        </div>

        <div className="flex-1 overflow-y-auto p-5 space-y-4 text-xs">
          <div>
            <label className="block text-[10px] text-slate-500 font-semibold uppercase mb-1">Your Name</label>
            <input
              type="text"
              placeholder="e.g. Asad Ali"
              value={workerName}
              onChange={(e) => setWorkerName(e.target.value)}
              className="w-full bg-[#f9fafb] border border-slate-200 text-[#141414] rounded-xl px-3.5 py-2 text-xs focus:outline-none focus:border-slate-400"
            />
          </div>

          <div>
            <label className="block text-[10px] text-slate-500 font-semibold uppercase mb-1">Phone Number (with Country Code)</label>
            <input
              type="text"
              placeholder="e.g. +923001234567 or +14155552671"
              value={phoneNumber}
              onChange={(e) => setPhoneNumber(e.target.value)}
              className="w-full bg-[#f9fafb] border border-slate-200 text-[#141414] rounded-xl px-3.5 py-2 text-xs font-mono focus:outline-none focus:border-slate-400"
            />
            <p className="text-[11px] text-slate-500 mt-1 font-medium">Include "+" and country code (e.g. +92 for PK, +1 for US, 7-15 digits)</p>
          </div>

          {error && (
            <div className="p-3 rounded-xl bg-rose-50 border border-rose-200 text-rose-700 text-xs font-medium">
              {error}
            </div>
          )}

          {result && (
            <div className="p-3.5 rounded-xl bg-emerald-50 border border-emerald-200 text-emerald-800 text-xs space-y-2">
              <div className="font-bold flex items-center gap-1.5">
                <span>✓</span>
                <span>Call Initiated! Ringing your phone now...</span>
              </div>
              <div className="font-mono text-[11px] text-emerald-900/80">Call ID: {result.call_id}</div>
              <p className="text-[11px] text-emerald-900/70 font-medium">Answer the call to hear CALL-E Heat Guardian's bilingual voice dispatch.</p>
              
              {onTrackCall && result.call_id && (
                <button
                  type="button"
                  onClick={() => onTrackCall(result.call_id)}
                  className="w-full mt-2 btn-primary bg-emerald-700 hover:bg-emerald-600 text-white text-xs py-1.5"
                >
                  Inspect Live Call Stream & Transcripts →
                </button>
              )}
            </div>
          )}
        </div>

        <div className="p-3.5 border-t border-slate-200 flex items-center justify-between bg-[#ffffff]">
          <button type="button" onClick={onClose} className="btn-secondary font-semibold">
            Close
          </button>
          <button
            type="button"
            onClick={handleCall}
            disabled={loading || !phoneNumber}
            className="btn-primary"
          >
            {loading ? 'Dialing CALL-E...' : 'Call My Phone Now'}
          </button>
        </div>
      </div>
    </div>
  )
}
