import { useState } from 'react'

interface ProductStoryModalProps {
  onClose: () => void
  onTriggerTest?: () => void
}

const STORY_STEPS = [
  {
    step: '01',
    category: 'SATELLITE & AI INGESTION',
    title: 'FortyGuard Geospatial Thermal Radar',
    tagline: 'Hyperlocal 100m heat variance across critical outdoor worksites.',
    accent: '#0284C7',
    description:
      'ThermaShift AI autonomously queries FortyGuard’s Temperature API for registered infrastructure polygons. Instead of generic city weather, it measures the exact ground thermal footprint and urban heat island penalty.',
    metrics: [
      { label: 'Spatial Resolution', value: '100 × 100 m' },
      { label: 'Live Data Source', value: 'FortyGuard API' },
      { label: 'Credit Safeguard', value: '4-Hr DB Cache' },
    ],
    highlight: 'Transforms passive satellite heat maps into real-time operational safety parameters.',
  },
  {
    step: '02',
    category: 'THERMODYNAMIC INTELLIGENCE',
    title: 'Microclimate Physics & Relocation Vectors',
    tagline: 'Computing true surface hazard vs shaded canopy relief.',
    accent: '#D97706',
    description:
      'While ambient air might read 104°F, black asphalt ground under direct solar radiation surges to 129°F. ThermaShift AI calculates the exact thermodynamic gradient and computes an immediate escape vector to the nearest shaded canopy.',
    metrics: [
      { label: 'Asphalt Surface', value: '129.1°F (Extreme)' },
      { label: 'Canopy Refuge', value: '85.0°F (Safe)' },
      { label: 'Cooling Delta', value: '-44.1°F Relief' },
    ],
    highlight: 'Automates OSHA & ILO mandated work-rest ratios (15m work / 45m shade rest).',
  },
  {
    step: '03',
    category: 'AUTONOMOUS TELEPHONY',
    title: 'CALL-E Outbound Voice AI Dispatch',
    tagline: 'Instant bilingual phone calls to workers in danger.',
    accent: '#059669',
    description:
      'When thermal thresholds are breached, ThermaShift AI does not wait for human intervention. It connects to the CALL-E telephony network and places direct voice calls to site foremen and crews in Urdu and English.',
    metrics: [
      { label: 'Voice Network', value: 'CALL-E Real Telephony' },
      { label: 'Supported Languages', value: 'Urdu + English' },
      { label: 'Dispatch Latency', value: '< 2.5 Seconds' },
    ],
    highlight: 'Captures worker voice acknowledgment and streams structured transcripts to PostgreSQL.',
  },
  {
    step: '04',
    category: 'LEGAL & REGULATORY',
    title: 'Automated OSHA Compliance Audit Trail',
    tagline: '1-Click verified audit certificates for safety inspectors.',
    accent: '#7C3AED',
    description:
      'Every temperature snapshot, voice dispatch, and worker consent event is immutably logged into PostgreSQL, generating 100% verified compliance reports for OSHA, ILO, and UAE MoHRE regulators.',
    metrics: [
      { label: 'Audit Standard', value: 'OSHA / ILO / MoHRE' },
      { label: 'Compliance Rating', value: '100% Grade A' },
      { label: 'Export Format', value: '1-Click Print / PDF' },
    ],
    highlight: 'Protects enterprise industrial contractors against heatstroke liability and regulatory penalties.',
  },
]

export default function ProductStoryModal({ onClose, onTriggerTest }: ProductStoryModalProps) {
  const [activeStep, setActiveStep] = useState(0)
  const current = STORY_STEPS[activeStep]

  return (
    <div className="fixed inset-0 z-[9999] flex items-center justify-center p-3 sm:p-6 bg-black/60 backdrop-blur-sm animate-fade-in font-sans">
      <div className="bg-[#ffffff] text-[#141414] border border-slate-200 rounded-2xl max-w-3xl w-full max-h-[90vh] flex flex-col shadow-2xl overflow-hidden">
        {/* Top Header */}
        <div className="shrink-0 p-4 border-b border-slate-200 flex items-center justify-between bg-[#ffffff]">
          <div className="flex items-center gap-2.5">
            <div className="w-8 h-8 rounded-lg bg-emerald-50 border border-emerald-200 flex items-center justify-center text-emerald-700">
              <svg className="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13 10V3L4 14h7v7l9-11h-7z" />
              </svg>
            </div>
            <div>
              <h2 className="text-sm font-bold text-[#141414]">
                How ThermaShift AI Works
              </h2>
              <p className="text-[11px] text-slate-500 font-medium">
                Autonomous Heat Safety Architecture & Pipeline
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

        {/* Step Navigation Pills */}
        <div className="shrink-0 p-2.5 sm:p-3 bg-[#f9fafb] border-b border-slate-200 grid grid-cols-2 sm:grid-cols-4 gap-1.5 sm:gap-2">
          {STORY_STEPS.map((s, idx) => (
            <button
              key={s.step}
              onClick={() => setActiveStep(idx)}
              className={`p-2 rounded-xl text-left transition-all border ${
                activeStep === idx
                  ? 'bg-[#ffffff] border-slate-400 shadow-sm'
                  : 'bg-[#f4f4f4] border-slate-200 hover:border-slate-300'
              }`}
            >
              <div className="flex items-center justify-between mb-0.5">
                <span className="text-[10px] font-black" style={{ color: s.accent }}>
                  STAGE {s.step}
                </span>
                {activeStep === idx && (
                  <span className="w-1.5 h-1.5 rounded-full" style={{ backgroundColor: s.accent }} />
                )}
              </div>
              <span className="text-[11px] font-bold text-[#141414] block truncate">
                {s.title.split(' ')[0]} {s.title.split(' ')[1]}
              </span>
            </button>
          ))}
        </div>

        {/* Main Content Area */}
        <div className="flex-1 overflow-y-auto p-5 space-y-4 text-xs">
          {/* Category Banner */}
          <div className="flex items-center gap-2">
            <span
              className="text-[10px] font-bold tracking-wider uppercase px-2 py-0.5 rounded-md border"
              style={{
                color: current.accent,
                borderColor: `${current.accent}40`,
                backgroundColor: `${current.accent}12`,
              }}
            >
              {current.category}
            </span>
          </div>

          {/* Title & Tagline */}
          <div className="space-y-1">
            <h3 className="text-lg font-black text-[#141414] tracking-tight">
              {current.title}
            </h3>
            <p className="text-xs text-slate-700 font-semibold">
              {current.tagline}
            </p>
          </div>

          {/* Body Paragraph */}
          <p className="text-xs text-slate-600 leading-relaxed bg-[#f9fafb] p-4 rounded-xl border border-slate-200 font-medium">
            {current.description}
          </p>

          {/* Metrics Grid */}
          <div className="grid grid-cols-3 gap-2.5">
            {current.metrics.map((m) => (
              <div key={m.label} className="p-3 rounded-xl bg-[#f9fafb] border border-slate-200 text-center">
                <span className="text-[10px] text-slate-500 font-medium block mb-0.5">{m.label}</span>
                <span className="text-xs font-bold text-[#141414] block">{m.value}</span>
              </div>
            ))}
          </div>

          {/* Highlight Callout */}
          <div
            className="p-3 rounded-xl border flex items-start gap-2.5 text-xs"
            style={{
              borderColor: `${current.accent}30`,
              backgroundColor: `${current.accent}0A`,
            }}
          >
            <div className="w-5 h-5 rounded-md flex items-center justify-center shrink-0 mt-0.5 font-bold" style={{ color: current.accent }}>
              ✓
            </div>
            <p className="text-slate-800 text-[11px] leading-relaxed font-medium">
              <strong className="text-[#141414] font-bold">Key Impact: </strong>
              {current.highlight}
            </p>
          </div>
        </div>

        {/* Footer Controls */}
        <div className="shrink-0 p-3.5 border-t border-slate-200 flex flex-col sm:flex-row items-center justify-between gap-2.5 bg-[#ffffff]">
          <div className="flex items-center gap-1.5 w-full sm:w-auto justify-between sm:justify-start">
            <button
              disabled={activeStep === 0}
              onClick={() => setActiveStep((prev) => Math.max(0, prev - 1))}
              className="btn-secondary text-xs disabled:opacity-30 font-semibold"
            >
              Previous
            </button>
            <button
              disabled={activeStep === STORY_STEPS.length - 1}
              onClick={() => setActiveStep((prev) => Math.min(STORY_STEPS.length - 1, prev + 1))}
              className="btn-secondary text-xs disabled:opacity-30 font-semibold"
            >
              Next Stage
            </button>
          </div>

          <div className="flex items-center gap-2 w-full sm:w-auto justify-end">
            {onTriggerTest && (
              <button
                onClick={() => {
                  onClose()
                  onTriggerTest()
                }}
                className="btn-danger text-xs font-bold"
              >
                Test Live Voice Dispatch
              </button>
            )}
            <button onClick={onClose} className="btn-secondary text-xs font-semibold">
              Close Walkthrough
            </button>
          </div>
        </div>
      </div>
    </div>
  )
}
