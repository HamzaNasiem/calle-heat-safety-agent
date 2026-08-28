import { useEffect, useRef } from 'react'
import { mountLetsScroll } from '../lib/lets-scroll/scrub-engine'

interface MissionScrubberProps {
  onReturnToDashboard: () => void
}

export default function MissionScrubber({ onReturnToDashboard }: MissionScrubberProps) {
  const containerRef = useRef<HTMLDivElement>(null)

  useEffect(() => {
    if (!containerRef.current) return

    mountLetsScroll(containerRef.current, {
      brand: { name: 'ThermaShift AI', href: '#top' },
      diveScroll: 1.2,
      connScroll: 0.8,
      hint: 'Scroll to fly through the FortyGuard Heat Safety Chain',
      nav: true,
      atmosphere: true,
      sections: [
        {
          id: 'detection',
          label: '1. Hyperlocal Heat',
          still: 'https://images.unsplash.com/photo-1509114397022-ed747cca3f65?auto=format&fit=crop&w=1200&q=80',
          accent: '#A27B5C',
          eyebrow: 'FortyGuard Spatial Intelligence',
          title: '100m Microclimate Street Grid',
          body: 'Capturing urban heat island variations 2m above ground level over registered work site boundaries.',
          tags: ['100m Resolution', '70 Microcells', 'FortyGuard API']
        },
        {
          id: 'safety',
          label: '2. OSHA Safety Engine',
          still: 'https://images.unsplash.com/photo-1541888946425-d0fbb18086f6?auto=format&fit=crop&w=1200&q=80',
          accent: '#C23B22',
          eyebrow: 'Algorithmic Compliance',
          title: 'Autonomous Work/Rest Scheduling',
          body: 'Stull WBGT formula and black globe thermal model dynamically calculating mandatory shaded rest.',
          tags: ['Stull WBGT', '15/45 Work-Rest', '1.0L/hr Hydration']
        },
        {
          id: 'dispatch',
          label: '3. Autonomous Voice',
          still: 'https://images.unsplash.com/photo-1581092160607-ee22621dd758?auto=format&fit=crop&w=1200&q=80',
          accent: '#2E7D32',
          eyebrow: 'Retell AI & Twilio SMS',
          title: 'Native Voice Call Alerts',
          body: 'Zero-human-delay outbound phone calls in native Urdu and English guiding workers to immediate shade.',
          tags: ['Retell AI Voice', 'Twilio Fallback', 'Bilingual AI']
        },
        {
          id: 'operations',
          label: '4. Mission Control',
          still: 'https://images.unsplash.com/photo-1504384308090-c894fdcc538d?auto=format&fit=crop&w=1200&q=80',
          accent: '#2C3639',
          eyebrow: 'Enterprise Operations',
          title: 'Live Telemetry & Audit Logs',
          body: 'Complete compliance records, Gaussian distribution curves, and multi-site roster management.',
          tags: ['Enterprise GIS', 'Audit Trail', 'PostgreSQL'],
          cta: {
            primary: { label: 'Enter Mission Control', href: '#' },
            secondary: { label: 'Documentation', href: '#' }
          }
        }
      ],
      connectors: []
    })
  }, [])

  return (
    <div className="relative w-full min-h-screen bg-[#DCD7C9]">
      <div className="fixed top-4 right-6 z-[9999]">
        <button
          onClick={onReturnToDashboard}
          className="bg-[#2C3639] hover:bg-[#3F4E4F] text-[#DCD7C9] px-4 py-2 rounded-xl text-xs font-mono font-bold shadow-warm-lg transition-all"
        >
          ← Return to Dashboard
        </button>
      </div>
      <div id="top"></div>
      <div ref={containerRef} id="world"></div>
    </div>
  )
}
