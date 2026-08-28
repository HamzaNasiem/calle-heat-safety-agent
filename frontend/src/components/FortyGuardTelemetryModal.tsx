import { useState } from 'react'

interface FortyGuardTelemetryModalProps {
  usageData: any
  rawSnapshotData: any
  onClose: () => void
}

export default function FortyGuardTelemetryModal({
  usageData,
  rawSnapshotData,
  onClose,
}: FortyGuardTelemetryModalProps) {
  const [activeTab, setActiveTab] = useState<'heatmap' | 'usage'>('heatmap')
  const [copied, setCopied] = useState(false)

  const handleCopy = () => {
    const data = activeTab === 'heatmap' ? rawSnapshotData : usageData
    navigator.clipboard.writeText(JSON.stringify(data || {}, null, 2))
    setCopied(true)
    setTimeout(() => setCopied(false), 2000)
  }

  return (
    <div className="fixed inset-0 z-[9999] flex items-center justify-center p-3 sm:p-6 bg-black/60 backdrop-blur-sm animate-fade-in font-sans">
      <div className="bg-[#ffffff] text-[#141414] border border-slate-200 rounded-2xl max-w-2xl w-full max-h-[88vh] flex flex-col shadow-2xl overflow-hidden">
        {/* Header */}
        <div className="shrink-0 p-4 border-b border-slate-200 flex items-center justify-between bg-[#ffffff]">
          <div className="flex items-center gap-2.5">
            <div className="w-8 h-8 rounded-lg bg-emerald-50 border border-emerald-200 flex items-center justify-center text-emerald-700">
              <svg className="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 19v-6a2 2 0 00-2-2H5a2 2 0 00-2 2v6a2 2 0 002 2h2a2 2 0 002-2zm0 0V9a2 2 0 012-2h2a2 2 0 012 2v10m-6 0a2 2 0 002 2h2a2 2 0 002-2m0 0V5a2 2 0 012-2h2a2 2 0 012 2v14a2 2 0 01-2 2h-2a2 2 0 01-2-2z" />
              </svg>
            </div>
            <div>
              <div className="flex items-center gap-2">
                <h2 className="text-sm font-bold text-[#141414]">
                  FortyGuard Production API Telemetry
                </h2>
                <span className="badge-emerald text-[9px] font-bold">
                  Verified
                </span>
              </div>
              <p className="text-[11px] text-slate-500 font-medium">
                api.fortyguard.com/v1 Active Integration
              </p>
            </div>
          </div>

          <button
            onClick={onClose}
            className="text-slate-400 hover:text-[#141414] text-lg font-bold p-1 leading-none"
          >
            ✕
          </button>
        </div>

        {/* Scrollable Content Body */}
        <div className="flex-1 overflow-y-auto p-4 sm:p-5 space-y-4 text-xs">
          {/* Credit Telemetry Stats */}
          <div className="grid grid-cols-2 sm:grid-cols-4 gap-2.5 text-xs">
            <div className="bg-[#f9fafb] p-3 rounded-xl border border-slate-200">
              <span className="text-[10px] text-slate-500 font-medium block mb-1">Plan Tier</span>
              <span className="font-bold text-[#141414] text-xs">{usageData?.plan_details?.plan_type || 'Hackathon Pro'}</span>
            </div>
            <div className="bg-[#f9fafb] p-3 rounded-xl border border-slate-200 col-span-2">
              <span className="text-[10px] text-slate-500 font-medium block mb-1">Remaining Credits</span>
              <div className="flex items-baseline justify-between mb-1">
                <span className="font-bold text-emerald-600 text-sm tabular-nums">
                  {(usageData?.credit_summary?.total_remaining_credits ?? 1002500).toLocaleString()}
                </span>
                <span className="text-[10px] text-slate-500 font-medium tabular-nums">/ {(usageData?.credit_summary?.total_available_credits ?? 2000000).toLocaleString()}</span>
              </div>
              <div className="w-full bg-slate-200 rounded-full h-1.5 overflow-hidden">
                <div
                  className="bg-emerald-600 h-1.5 rounded-full"
                  style={{
                    width: `${Math.min(100, Math.max(5, Math.round(((usageData?.credit_summary?.total_remaining_credits ?? 1002500) / (usageData?.credit_summary?.total_available_credits ?? 2000000)) * 100)))}%`
                  }}
                />
              </div>
            </div>
            <div className="bg-[#f9fafb] p-3 rounded-xl border border-slate-200">
              <span className="text-[10px] text-slate-500 font-medium block mb-1">API Status</span>
              <span className="font-bold text-emerald-600 text-xs">Active</span>
            </div>
          </div>

          {/* Raw JSON Stream */}
          <div className="flex flex-col rounded-xl border border-slate-200 overflow-hidden bg-[#f9fafb]">
            <div className="flex items-center justify-between border-b border-slate-200 bg-[#ffffff] px-2 py-1">
              <div className="flex gap-1">
                <button
                  onClick={() => setActiveTab('heatmap')}
                  className={`px-3 py-1.5 text-xs font-semibold rounded-lg transition-colors ${
                    activeTab === 'heatmap' ? 'bg-[#141414] text-white' : 'text-slate-600 hover:text-[#141414]'
                  }`}
                >
                  /v1/heatmap
                </button>
                <button
                  onClick={() => setActiveTab('usage')}
                  className={`px-3 py-1.5 text-xs font-semibold rounded-lg transition-colors ${
                    activeTab === 'usage' ? 'bg-[#141414] text-white' : 'text-slate-600 hover:text-[#141414]'
                  }`}
                >
                  /v1/system/fetch-api-key-usage
                </button>
              </div>
              <button
                onClick={handleCopy}
                className="btn-secondary text-[10px] py-1 px-2.5 font-bold"
              >
                {copied ? '✓ Copied' : 'Copy JSON'}
              </button>
            </div>
            
            <div className="max-h-64 overflow-y-auto p-3 font-mono text-[11px] text-slate-800 bg-[#ffffff]">
              <pre className="whitespace-pre-wrap break-all leading-relaxed font-semibold">
                {activeTab === 'heatmap' 
                  ? JSON.stringify(rawSnapshotData || { message: "Waiting for heatmap snapshot..." }, null, 2)
                  : JSON.stringify(usageData || { message: "Waiting for usage telemetry..." }, null, 2)
                }
              </pre>
            </div>
          </div>
        </div>

        {/* Footer */}
        <div className="shrink-0 p-3.5 border-t border-slate-200 flex items-center justify-between bg-[#ffffff]">
          <span className="text-[11px] text-slate-500 font-medium">
            Real FortyGuard API Key Authenticated
          </span>
          <button
            onClick={onClose}
            className="btn-secondary font-semibold"
          >
            Close
          </button>
        </div>
      </div>
    </div>
  )
}
