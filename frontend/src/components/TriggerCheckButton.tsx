import { useState } from 'react'
import { triggerCheck } from '../lib/api'
import type { TriggerCheckResponse } from '../types'

interface TriggerCheckButtonProps {
  siteId: string
  onResult?: (result: TriggerCheckResponse) => void
}

export default function TriggerCheckButton({ siteId, onResult }: TriggerCheckButtonProps) {
  const [loading, setLoading] = useState(false)
  const [forceExtreme, setForceExtreme] = useState(false)
  const [lastResult, setLastResult] = useState<TriggerCheckResponse | null>(null)
  const [error, setError] = useState<string | null>(null)

  async function handleTrigger() {
    setLoading(true)
    setError(null)
    try {
      const result = await triggerCheck(siteId, forceExtreme)
      setLastResult(result)
      onResult?.(result)
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Trigger failed')
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="flex flex-col gap-3">
      <div className="flex items-center gap-3 flex-wrap">
        <button
          id="trigger-check-btn"
          onClick={handleTrigger}
          disabled={loading || !siteId}
          className={`flex items-center gap-2 ${
            forceExtreme
              ? 'bg-red-800 hover:bg-red-900 text-white font-mono text-xs font-bold px-4 py-2.5 rounded-xl shadow-warm transition-all active:scale-95'
              : 'btn-bronze'
          } disabled:opacity-40 disabled:cursor-not-allowed`}
        >
          {loading ? (
            <>
              <svg className="animate-spin h-3.5 w-3.5 text-white" fill="none" viewBox="0 0 24 24">
                <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" />
                <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8v8z" />
              </svg>
              <span>Dispatching Voice Check...</span>
            </>
          ) : (
            <>
              <span>⚡</span>
              <span>{forceExtreme ? 'Simulate Extreme Heat (112°F)' : 'Trigger Emergency Voice Check'}</span>
            </>
          )}
        </button>

        <label className="flex items-center gap-2 text-xs text-[#3F4E4F] cursor-pointer select-none font-mono">
          <input
            type="checkbox"
            id="force-extreme-toggle"
            checked={forceExtreme}
            onChange={(e) => setForceExtreme(e.target.checked)}
            className="w-4 h-4 accent-[#A27B5C] rounded"
          />
          <span>Force 112°F Demo Mode</span>
        </label>
      </div>

      {error && (
        <p className="text-xs text-red-800 bg-red-100 border border-red-300 rounded-xl px-3 py-2 font-mono">
          {error}
        </p>
      )}

      {lastResult && (
        <div className="text-xs text-[#2C3639] bg-[#F5F2EB] border border-[#3F4E4F]/20 rounded-xl px-3.5 py-2.5 font-mono shadow-sm">
          Risk: <span className="font-bold uppercase text-[#A27B5C]">{lastResult.risk_level}</span>
          {' | '}{lastResult.temperature_f}°F
          {' | '}{lastResult.alerts_dispatched ? '🔔 Retell Voice & SMS Dispatched' : 'No alerts'}
        </div>
      )}
    </div>
  )
}
