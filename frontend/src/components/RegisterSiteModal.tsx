import { useState } from 'react'
import { createSite } from '../lib/api'
import type { Site } from '../types'

interface RegisterSiteModalProps {
  onSiteCreated: (site: Site) => void
  onClose: () => void
}

const PRESET_LOCATIONS = [
  { name: 'Los Angeles Downtown Thermal Corridor, CA', lat: 34.0407, lng: -118.2468 },
  { name: 'Port of Los Angeles & Long Beach Terminal, CA', lat: 33.7432, lng: -118.2673 },
  { name: 'Fresno Central Valley Solar & Ag Zone, CA', lat: 36.7468, lng: -119.7726 },
  { name: 'Inland Empire Ontario Logistics Hub, CA', lat: 34.0633, lng: -117.6509 },
  { name: 'Bakersfield Energy & Agriculture Corridor, CA', lat: 35.3733, lng: -119.0187 },
  { name: 'Silicon Valley San Jose Construction Yard, CA', lat: 37.3382, lng: -121.8863 },
]

export default function RegisterSiteModal({ onSiteCreated, onClose }: RegisterSiteModalProps) {
  const [name, setName] = useState('')
  const [lat, setLat] = useState('36.7468')
  const [lng, setLng] = useState('-119.7726')
  const [radiusKm, setRadiusKm] = useState('1.0')
  const [elevatedF, setElevatedF] = useState('100')
  const [extremeF, setExtremeF] = useState('108')
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)

  function handlePresetSelect(preset: typeof PRESET_LOCATIONS[0]) {
    setName(preset.name)
    setLat(preset.lat.toString())
    setLng(preset.lng.toString())
  }

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault()
    if (!name || !lat || !lng) return
    setLoading(true)
    setError(null)

    const centerLat = parseFloat(lat)
    const centerLng = parseFloat(lng)
    const size = parseFloat(radiusKm)

    const dlat = (size / 2) / 111.0
    const dlng = (size / 2) / (111.0 * Math.cos((centerLat * Math.PI) / 180))

    const polygon_geojson = {
      type: 'Polygon' as const,
      coordinates: [[
        [Math.round((centerLng - dlng) * 1e6) / 1e6, Math.round((centerLat - dlat) * 1e6) / 1e6],
        [Math.round((centerLng + dlng) * 1e6) / 1e6, Math.round((centerLat - dlat) * 1e6) / 1e6],
        [Math.round((centerLng + dlng) * 1e6) / 1e6, Math.round((centerLat + dlat) * 1e6) / 1e6],
        [Math.round((centerLng - dlng) * 1e6) / 1e6, Math.round((centerLat + dlat) * 1e6) / 1e6],
        [Math.round((centerLng - dlng) * 1e6) / 1e6, Math.round((centerLat - dlat) * 1e6) / 1e6],
      ]]
    }

    try {
      const site = await createSite({
        name,
        polygon_geojson,
        elevated_threshold_f: parseFloat(elevatedF),
        extreme_threshold_f: parseFloat(extremeF),
      })

      onSiteCreated(site)
      onClose()
    } catch (err: any) {
      setError(err.message || 'Failed to create site')
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="fixed inset-0 z-[9999] flex items-center justify-center p-3 sm:p-6 bg-black/60 backdrop-blur-sm animate-fade-in font-sans">
      <div className="bg-[#ffffff] text-[#141414] border border-slate-200 rounded-2xl max-w-lg w-full max-h-[88vh] flex flex-col shadow-2xl overflow-hidden">
        <div className="p-4 border-b border-slate-200 flex items-center justify-between bg-[#ffffff]">
          <div className="flex items-center gap-2.5">
            <div className="w-8 h-8 rounded-lg bg-emerald-50 border border-emerald-200 flex items-center justify-center text-emerald-700 font-bold">
              <svg className="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M17.657 16.657L13.414 20.9a1.998 1.998 0 01-2.827 0l-4.244-4.243a8 8 0 1111.314 0z" />
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15 11a3 3 0 11-6 0 3 3 0 016 0z" />
              </svg>
            </div>
            <div>
              <h2 className="text-sm font-bold text-[#141414]">
                Register Work Site AOI
              </h2>
              <p className="text-[11px] text-slate-500 font-medium">
                Autonomous Voice Safety & Heat Polling Area
              </p>
            </div>
          </div>
          <button onClick={onClose} className="text-slate-400 hover:text-[#141414] text-lg font-bold">
            ✕
          </button>
        </div>

        <div className="flex-1 overflow-y-auto p-5 space-y-4 text-xs">
          {/* Quick Presets */}
          <div>
            <label className="block text-[10px] text-slate-500 font-semibold uppercase mb-1.5">
              Quick Global Worksite Presets
            </label>
            <div className="grid grid-cols-1 sm:grid-cols-2 gap-1.5">
              {PRESET_LOCATIONS.map((preset) => (
                <button
                  key={preset.name}
                  type="button"
                  onClick={() => handlePresetSelect(preset)}
                  className="p-2 rounded-xl bg-[#f9fafb] border border-slate-200 hover:border-slate-300 text-left text-[11px] transition-colors"
                >
                  <span className="font-semibold text-[#141414] block truncate">{preset.name.split(',')[0]}</span>
                  <span className="text-[10px] text-slate-500">{preset.lat}, {preset.lng}</span>
                </button>
              ))}
            </div>
          </div>

          <form id="register-site-form" onSubmit={handleSubmit} className="space-y-3">
            <div>
              <label className="block text-[10px] text-slate-500 font-semibold uppercase mb-1">Site / Facility Name</label>
              <input
                type="text"
                required
                placeholder="e.g. Phoenix Sky Harbor Logistics Yard"
                value={name}
                onChange={(e) => setName(e.target.value)}
                className="w-full bg-[#f9fafb] border border-slate-200 text-[#141414] rounded-xl px-3.5 py-2 text-xs focus:outline-none focus:border-slate-400"
              />
            </div>

            <div className="grid grid-cols-2 gap-3">
              <div>
                <label className="block text-[10px] text-slate-500 font-semibold uppercase mb-1">Latitude</label>
                <input
                  type="number"
                  step="any"
                  required
                  value={lat}
                  onChange={(e) => setLat(e.target.value)}
                  className="w-full bg-[#f9fafb] border border-slate-200 text-[#141414] rounded-xl px-3.5 py-2 text-xs font-mono focus:outline-none focus:border-slate-400"
                />
              </div>
              <div>
                <label className="block text-[10px] text-slate-500 font-semibold uppercase mb-1">Longitude</label>
                <input
                  type="number"
                  step="any"
                  required
                  value={lng}
                  onChange={(e) => setLng(e.target.value)}
                  className="w-full bg-[#f9fafb] border border-slate-200 text-[#141414] rounded-xl px-3.5 py-2 text-xs font-mono focus:outline-none focus:border-slate-400"
                />
              </div>
            </div>

            <div className="grid grid-cols-3 gap-3">
              <div>
                <label className="block text-[10px] text-slate-500 font-semibold uppercase mb-1">Radius (km)</label>
                <input
                  type="number"
                  step="0.1"
                  min="0.2"
                  max="10"
                  value={radiusKm}
                  onChange={(e) => setRadiusKm(e.target.value)}
                  className="w-full bg-[#f9fafb] border border-slate-200 text-[#141414] rounded-xl px-3 py-2 text-xs focus:outline-none focus:border-slate-400"
                />
              </div>
              <div>
                <label className="block text-[10px] text-slate-500 font-semibold uppercase mb-1">Caution (°F)</label>
                <input
                  type="number"
                  value={elevatedF}
                  onChange={(e) => setElevatedF(e.target.value)}
                  className="w-full bg-[#f9fafb] border border-slate-200 text-[#141414] rounded-xl px-3 py-2 text-xs focus:outline-none focus:border-slate-400"
                />
              </div>
              <div>
                <label className="block text-[10px] text-slate-500 font-semibold uppercase mb-1">Extreme (°F)</label>
                <input
                  type="number"
                  value={extremeF}
                  onChange={(e) => setExtremeF(e.target.value)}
                  className="w-full bg-[#f9fafb] border border-slate-200 text-[#141414] rounded-xl px-3 py-2 text-xs focus:outline-none focus:border-slate-400"
                />
              </div>
            </div>

            {error && (
              <div className="p-3 rounded-xl bg-rose-50 border border-rose-200 text-rose-700 text-xs font-medium">
                {error}
              </div>
            )}
          </form>
        </div>

        <div className="p-3.5 border-t border-slate-200 flex items-center justify-between bg-[#ffffff]">
          <button type="button" onClick={onClose} className="btn-secondary font-semibold">
            Cancel
          </button>
          <button
            type="submit"
            form="register-site-form"
            disabled={loading}
            className="btn-primary"
          >
            {loading ? 'Creating Site...' : 'Save & Start Monitoring'}
          </button>
        </div>
      </div>
    </div>
  )
}
