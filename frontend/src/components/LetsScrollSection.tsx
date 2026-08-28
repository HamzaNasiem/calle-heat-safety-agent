import { useEffect, useRef } from 'react'
import { mountLetsScroll } from '../lib/lets-scroll/scrub-engine'

export default function LetsScrollSection() {
  const containerRef = useRef<HTMLDivElement>(null)

  useEffect(() => {
    if (!containerRef.current) return

    try {
      mountLetsScroll(containerRef.current, {
        brand: { name: 'ThermaShift AI', href: '#' },
        diveScroll: 1.2,
        connScroll: 0.8,
        hint: 'Scroll to fly through heat safety zone',
        nav: false,
        atmosphere: true,
        sections: [
          {
            id: 'thermal-radar-feed',
            label: 'Thermal Radar Feed',
            eyebrow: 'Real-Time Thermal Telemetry',
            title: 'Continuous Heat Monitoring',
            body: 'Ingesting micro-climate temperature data across outdoor construction zones every 10 minutes.',
            accent: '#f97316',
          },
          {
            id: 'risk-classification',
            label: 'Autonomous Risk Engine',
            eyebrow: 'P0 Risk Assessment',
            title: 'Dynamic Heat Index Classification',
            body: 'Automatically categorizes heat risks into Normal, Elevated, and Extreme thresholds per OSHA standards.',
            accent: '#ef4444',
          },
          {
            id: 'retell-dispatch',
            label: 'Retell AI Voice Alert',
            eyebrow: 'Multilingual Worker Protection',
            title: 'Instant Voice Call & SMS Alerting',
            body: 'Dispatches targeted voice phone calls in Urdu and English directly to outdoor field workers upon extreme heat detection.',
            accent: '#3b82f6',
          },
        ],
      })
    } catch (err) {
      console.warn('Lets-scroll initialisation notice:', err)
    }
  }, [])

  return (
    <div className="rounded-xl border border-slate-800 bg-[#0b101d] overflow-hidden shadow-2xl p-4 my-4">
      <div className="flex items-center justify-between mb-3 border-b border-slate-800 pb-2">
        <div className="flex items-center gap-2">
          <span className="text-sm font-bold text-orange-400 uppercase tracking-wider">
            Lets-Scroll Scrub Engine
          </span>
          <span className="text-[10px] px-2 py-0.5 rounded bg-orange-500/10 text-orange-400 font-mono">
            v1.0 Ready
          </span>
        </div>
        <span className="text-xs text-slate-500 font-mono">Interactive Camera-Flight Telemetry</span>
      </div>

      <div
        ref={containerRef}
        className="relative min-h-[360px] rounded-lg bg-[#0d1527] flex items-center justify-center text-slate-400 text-xs font-mono border border-slate-800/80 overflow-hidden"
      >
        <div className="text-center space-y-2 p-6 z-10">
          <div className="w-10 h-10 mx-auto rounded-full bg-orange-500/20 text-orange-400 flex items-center justify-center text-xl animate-pulse">
            🛰️
          </div>
          <p className="font-semibold text-slate-200 text-sm">ThermaShift AI Scroll Telemetry Active</p>
          <p className="text-slate-400 text-xs max-w-md">
            Interactive scroll engine mounted cleanly for autonomous multi-zone heat monitoring walkthrough.
          </p>
        </div>
      </div>
    </div>
  )
}
