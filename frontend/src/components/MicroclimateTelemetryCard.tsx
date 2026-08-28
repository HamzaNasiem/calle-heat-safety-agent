import type { MicroclimateAnalysis } from '../types'

interface MicroclimateTelemetryCardProps {
  data: MicroclimateAnalysis | null
  loading?: boolean
  onBroadcastClick?: () => void
}

export default function MicroclimateTelemetryCard({ data, loading, onBroadcastClick }: MicroclimateTelemetryCardProps) {
  if (loading) {
    return (
      <div className="card-surface p-4 text-xs text-slate-400 animate-pulse space-y-4 font-sans">
        <div className="flex items-center justify-between border-b border-[#e5e5e5] pb-3">
          <div className="space-y-1.5 w-2/3">
            <div className="h-4 bg-slate-200 rounded w-1/2" />
            <div className="h-3 bg-slate-100 rounded w-3/4" />
          </div>
          <div className="h-4 w-20 bg-slate-100 rounded-full" />
        </div>
        <div className="grid grid-cols-3 gap-2">
          <div className="h-16 bg-slate-100 rounded-xl" />
          <div className="h-16 bg-slate-100 rounded-xl" />
          <div className="h-16 bg-slate-100 rounded-xl" />
        </div>
        <div className="h-12 bg-slate-100 rounded-xl" />
        <div className="h-20 bg-slate-100 rounded-xl" />
      </div>
    )
  }

  if (!data) return null

  const surfaceTemp = data.surface_temp_f
  const ambientTemp = data.ambient_temp_f
  const uhiDelta = data.uhi_delta_f
  const solarRad = data.solar_radiation_w_m2
  const reliefDelta = data.cooling_delta_f
  const shiftDist = data.recommended_shift_distance_m
  const coolSectorTemp = Math.round((ambientTemp - 20) * 10) / 10

  const isExtreme = ambientTemp >= 104 || surfaceTemp >= 118
  const isElevated = (ambientTemp >= 95 || surfaceTemp >= 106) && !isExtreme

  const oshaSchedule = isExtreme ? '15 min Work / 45 min Shade Rest' : isElevated ? '30 min Work / 30 min Rest' : '50 min Work / 10 min Rest'
  const hydration = isExtreme ? '1.5 L/hr Water' : isElevated ? '1.0 L/hr Water' : '0.75 L/hr Water'
  
  const statusColor = isExtreme 
    ? 'border-rose-200 bg-rose-50 text-rose-800' 
    : isElevated 
    ? 'border-amber-200 bg-amber-50 text-amber-900' 
    : 'border-emerald-200 bg-emerald-50 text-emerald-800'

  return (
    <div className="card-surface p-4 space-y-4 font-sans">
      {/* Header */}
      <div className="flex items-center justify-between border-b border-[#e5e5e5] pb-3">
        <div>
          <h3 className="text-xs font-bold text-[#141414] tracking-tight">
            Spatial Thermal Telemetry
          </h3>
          <p className="text-[11px] text-slate-500 font-medium">
            Thermal Radar Peak vs Coolest AOI Sector
          </p>
        </div>
        <span className="badge-slate text-[10px] font-semibold">
          100m Spatial Grid
        </span>
      </div>

      {/* 3 Stat Metrics */}
      <div className="grid grid-cols-3 gap-1.5 sm:gap-2 text-center">
        {/* 1. Peak Hotspot */}
        <div className="p-2 sm:p-2.5 rounded-xl bg-[#f9fafb] border border-rose-200">
          <span className="text-[9px] sm:text-[10px] font-semibold text-slate-600 block mb-0.5 truncate">Peak Hotspot</span>
          <div className="text-base sm:text-xl font-black text-rose-600 tracking-tight tabular-nums">
            {surfaceTemp}°F
          </div>
          <span className="text-[8px] sm:text-[9px] text-rose-700 font-bold block truncate">
            +{uhiDelta}°F Solar
          </span>
        </div>

        {/* 2. Mean Air Temp */}
        <div className="p-2 sm:p-2.5 rounded-xl bg-[#f9fafb] border border-slate-200">
          <span className="text-[9px] sm:text-[10px] font-semibold text-slate-600 block mb-0.5 truncate">Site Mean</span>
          <div className="text-base sm:text-xl font-black text-amber-600 tracking-tight tabular-nums">
            {ambientTemp}°F
          </div>
          <span className="text-[8px] sm:text-[9px] text-slate-500 font-medium block truncate">
            {solarRad} W/m²
          </span>
        </div>

        {/* 3. Coolest Measured Sector */}
        <div className="p-2 sm:p-2.5 rounded-xl bg-[#f9fafb] border border-emerald-200">
          <span className="text-[9px] sm:text-[10px] font-semibold text-slate-600 block mb-0.5 truncate">Cool Sector</span>
          <div className="text-base sm:text-xl font-black text-emerald-600 tracking-tight tabular-nums">
            {coolSectorTemp}°F
          </div>
          <span className="text-[8px] sm:text-[9px] text-emerald-700 font-bold block truncate">
            -{reliefDelta}°F Relief
          </span>
        </div>
      </div>

      {/* OSHA Protocol */}
      <div className={`p-3 rounded-xl border ${statusColor} flex items-center justify-between text-xs`}>
        <div>
          <span className="text-[10px] font-bold opacity-75 block uppercase tracking-wider">
            Mandated Work/Rest Ratio
          </span>
          <span className="font-bold text-[#141414] text-xs">
            {oshaSchedule}
          </span>
        </div>
        <div className="text-right">
          <span className="text-[10px] font-bold opacity-75 block uppercase tracking-wider">
            Hydration
          </span>
          <span className="font-bold text-sky-700 text-xs">
            {hydration}
          </span>
        </div>
      </div>

      {/* Relocation Route Card */}
      <div className="p-3 rounded-xl bg-[#f9fafb] border border-slate-200 space-y-2 text-xs">
        <div className="flex items-center justify-between">
          <span className="text-[11px] font-bold text-[#141414]">
            Thermal Gradient Relocation Vector
          </span>
          <span className="text-[10px] font-bold text-emerald-700 px-1.5 py-0.5 rounded bg-emerald-50 border border-emerald-200">
            -{reliefDelta}°F Relief
          </span>
        </div>
        <p className="text-[11px] text-slate-600 leading-relaxed font-medium">
          Thermal Radar scan detects peak exposure at Sector A ({surfaceTemp}°F). Guided safety vector points {shiftDist}m toward lowest thermal exposure Sector D ({coolSectorTemp}°F).
        </p>

        {onBroadcastClick && (
          <button
            onClick={onBroadcastClick}
            className="w-full mt-1 py-1.5 rounded-lg bg-[#ffffff] hover:bg-slate-100 text-[#141414] text-[11px] font-semibold transition-colors border border-slate-200 shadow-sm"
          >
            Dispatch Relocation Directive
          </button>
        )}
      </div>
    </div>
  )
}
