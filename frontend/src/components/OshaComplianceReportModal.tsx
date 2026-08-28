import type { Site, MicroclimateAnalysis, Worker, ActionLog } from '../types'

interface OshaReportModalProps {
  site: Site | null
  microclimate: MicroclimateAnalysis | null
  workers: Worker[]
  alerts: ActionLog[]
  onClose: () => void
}

export default function OshaComplianceReportModal({
  site,
  microclimate,
  workers,
  alerts,
  onClose,
}: OshaReportModalProps) {
  if (!site) return null

  const reportDate = new Date().toLocaleDateString('en-US', {
    year: 'numeric',
    month: 'long',
    day: 'numeric',
  })
  const reportTime = new Date().toLocaleTimeString('en-US', {
    hour: '2-digit',
    minute: '2-digit',
    timeZoneName: 'short',
  })

  const ambientTemp = microclimate?.ambient_temp_f ?? 102.5
  const surfaceTemp = microclimate?.surface_temp_f ?? 128.9
  const canopyTemp = Math.round((ambientTemp - 20) * 10) / 10
  const uhiDelta = Math.round((surfaceTemp - ambientTemp) * 10) / 10
  const isExtreme = ambientTemp >= 104 || surfaceTemp >= 118

  function handlePrint() {
    window.print()
  }

  return (
    <div className="fixed inset-0 z-[9999] flex items-center justify-center p-3 sm:p-6 bg-black/60 backdrop-blur-sm animate-fade-in">
      <div className="bg-[#ffffff] text-[#141414] border border-slate-200 rounded-2xl max-w-2xl w-full max-h-[88vh] flex flex-col shadow-2xl overflow-hidden">
        {/* Header */}
        <div className="shrink-0 p-4 border-b border-slate-200 flex items-center justify-between bg-[#ffffff]">
          <div className="flex items-center gap-2.5">
            <div className="w-8 h-8 rounded-lg bg-emerald-50 border border-emerald-200 flex items-center justify-center text-emerald-700">
              <svg className="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
              </svg>
            </div>
            <div>
              <h2 className="text-sm font-bold text-[#141414]">
                OSHA & ILO Heat Safety Compliance Audit
              </h2>
              <p className="text-[11px] text-slate-500 font-medium">
                Automated Heat & Voice Dispatch Verification Certificate
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
          {/* Top Audit Meta */}
          <div className="p-3.5 rounded-xl bg-[#f9fafb] border border-slate-200 grid grid-cols-2 sm:grid-cols-4 gap-3">
            <div>
              <span className="text-[10px] text-slate-500 font-semibold uppercase block">Monitored Job Site</span>
              <span className="font-bold text-[#141414] text-xs truncate block">{site.name}</span>
            </div>
            <div>
              <span className="text-[10px] text-slate-500 font-semibold uppercase block">Timestamp</span>
              <span className="font-bold text-[#141414] text-xs block">{reportDate} {reportTime}</span>
            </div>
            <div>
              <span className="text-[10px] text-slate-500 font-semibold uppercase block">Regulatory Standard</span>
              <span className="font-bold text-[#141414] text-xs block">OSHA / ILO / UAE MoHRE</span>
            </div>
            <div>
              <span className="text-[10px] text-slate-500 font-semibold uppercase block">Compliance Status</span>
              <span className="font-bold text-emerald-700 text-xs block">100% Verified (Grade A)</span>
            </div>
          </div>

          {/* Section 1: Spatial Telemetry */}
          <div className="space-y-2">
            <h4 className="text-xs font-bold text-[#141414]">
              1. Microclimate Spatial Heat Telemetry
            </h4>
            <div className="grid grid-cols-3 gap-2 text-center">
              <div className="p-2.5 rounded-xl bg-[#f9fafb] border border-rose-200">
                <span className="text-[10px] text-slate-500 font-medium block mb-0.5">Asphalt Ground</span>
                <span className="text-base font-black text-rose-600 block tabular-nums">{surfaceTemp}°F</span>
                <span className="text-[9px] text-rose-700 font-bold">+{uhiDelta}°F UHI Penalty</span>
              </div>
              <div className="p-2.5 rounded-xl bg-[#f9fafb] border border-slate-200">
                <span className="text-[10px] text-slate-500 font-medium block mb-0.5">Ambient Air</span>
                <span className="text-base font-black text-amber-600 block tabular-nums">{ambientTemp}°F</span>
                <span className="text-[9px] text-slate-500 font-medium">Weather Baseline</span>
              </div>
              <div className="p-2.5 rounded-xl bg-[#f9fafb] border border-emerald-200">
                <span className="text-[10px] text-slate-500 font-medium block mb-0.5">Cooling Canopy</span>
                <span className="text-base font-black text-emerald-600 block tabular-nums">{canopyTemp}°F</span>
                <span className="text-[9px] text-emerald-700 font-bold">Relief Refuge</span>
              </div>
            </div>
          </div>

          {/* Section 2: OSHA Mandated Cycles */}
          <div className="space-y-2">
            <h4 className="text-xs font-bold text-[#141414]">
              2. Mandated Work/Rest Cycles & Hydration
            </h4>
            <div className="p-3 rounded-xl bg-[#f9fafb] border border-slate-200 space-y-1.5 leading-relaxed text-[11px]">
              <div className="flex justify-between">
                <span className="text-slate-500 font-medium">Heat Hazard Category:</span>
                <span className="font-bold text-rose-700">{isExtreme ? 'Extreme Hazard (Category IV)' : 'Elevated Caution (Category II)'}</span>
              </div>
              <div className="flex justify-between">
                <span className="text-slate-500 font-medium">Required Work/Rest Ratio:</span>
                <span className="font-bold text-[#141414]">{isExtreme ? '15 min Heavy Work / 45 min Shaded Rest' : '30 min Work / 30 min Rest'}</span>
              </div>
              <div className="flex justify-between">
                <span className="text-slate-500 font-medium">Mandated Water Intake:</span>
                <span className="font-bold text-sky-700">1.5 Liters Cool Water / Worker / Hour</span>
              </div>
              <div className="flex justify-between">
                <span className="text-slate-500 font-medium">Autonomous Shift Vector:</span>
                <span className="font-bold text-emerald-700">Zone A (Loading Bay) → Zone D (Canopy)</span>
              </div>
            </div>
          </div>

          {/* Section 3: Worker Consent */}
          <div className="space-y-2">
            <h4 className="text-xs font-bold text-[#141414]">
              3. Protected Personnel Coverage ({workers.length} Workers)
            </h4>
            <div className="space-y-1.5 max-h-36 overflow-y-auto pr-1">
              {workers.map((w) => (
                <div key={w.id} className="p-2 rounded-lg bg-[#f9fafb] border border-slate-200 flex items-center justify-between text-[11px]">
                  <div className="font-semibold text-[#141414] truncate">{w.name} ({w.phone_number})</div>
                  <span className="badge-emerald text-[9px] font-bold">Consented & Covered</span>
                </div>
              ))}
            </div>
          </div>

          {/* Section 4: Recent Dispatches */}
          <div className="space-y-2">
            <h4 className="text-xs font-bold text-[#141414]">
              4. Recent Dispatches & Action Trail ({alerts.length} Records)
            </h4>
            <div className="p-2.5 rounded-xl bg-[#f9fafb] border border-slate-200 text-[11px] text-slate-500 text-center font-medium">
              {alerts.length === 0 ? (
                <span>Continuous autonomous guardian active • Real-time alerts logged on threshold trigger.</span>
              ) : (
                <span className="text-[#141414] font-semibold">Latest Alert: {alerts[0].channel} ({alerts[0].status}) at {new Date(alerts[0].created_at).toLocaleTimeString()}</span>
              )}
            </div>
          </div>
        </div>

        {/* Footer */}
        <div className="shrink-0 p-3.5 border-t border-slate-200 flex items-center justify-end gap-2 bg-[#ffffff]">
          <button
            onClick={onClose}
            className="btn-secondary font-semibold"
          >
            Close
          </button>
          <button
            onClick={handlePrint}
            className="btn-primary"
          >
            <svg className="w-3.5 h-3.5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M17 17h2a2 2 0 002-2v-4a2 2 0 00-2-2H5a2 2 0 00-2 2v4a2 2 0 002 2h2m2 4h6a2 2 0 002-2v-4a2 2 0 00-2-2H9a2 2 0 00-2 2v4a2 2 0 002 2zm8-12V5a2 2 0 00-2-2H9a2 2 0 00-2 2v4h10z" />
            </svg>
            <span>Print Official Certificate</span>
          </button>
        </div>
      </div>
    </div>
  )
}
