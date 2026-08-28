import type { HeatSnapshot } from '../types'

interface AnalyticsPanelProps {
  snapshot: HeatSnapshot | null
}

export default function AnalyticsPanel({ snapshot }: AnalyticsPanelProps) {
  const raw = snapshot?.raw_response
  const stats = raw?.data?.result?.stats_data || raw?.result?.stats_data || {}
  const tempStats = stats.temperature_stats || {}
  const normDist = stats.normal_temperature_distribution || {}
  const xVals = (normDist.x_axis || []) as number[]
  const yVals = (normDist.y_axis || []) as number[]

  const points = xVals.map((x, i) => {
    const tempF = (x * 9) / 5 + 32
    return { x: tempF, y: yVals[i] ?? 0 }
  })

  const maxY = Math.max(...yVals, 1)
  const minX = points.length > 0 ? points[0].x : 95
  const maxX = points.length > 0 ? points[points.length - 1].x : 115

  const svgWidth = 300
  const svgHeight = 110

  const polylinePoints = points.map((p) => {
    const px = ((p.x - minX) / (maxX - minX || 1)) * (svgWidth - 20) + 10
    const py = svgHeight - 15 - (p.y / maxY) * (svgHeight - 30)
    return `${px.toFixed(1)},${py.toFixed(1)}`
  }).join(' ')

  const maxTempC = tempStats.maximum ?? 39.75
  const meanTempC = tempStats.mean ?? 39.71
  const minTempC = tempStats.minimum ?? 39.66
  const stdDev = tempStats.standard_deviation ?? 0.02

  const maxTempF = Math.round(((maxTempC * 9) / 5 + 32) * 10) / 10
  const meanTempF = Math.round(((meanTempC * 9) / 5 + 32) * 10) / 10
  const minTempF = Math.round(((minTempC * 9) / 5 + 32) * 10) / 10

  return (
    <div className="space-y-3.5 font-sans">
      <div className="flex items-center justify-between">
        <span className="text-[11px] font-bold uppercase tracking-wider text-[#141414]">
          Spatial Thermal Distribution
        </span>
        <span className="badge-slate text-[10px] font-bold">
          70 Cells (100m)
        </span>
      </div>

      {/* SVG Gaussian Curve */}
      <div className="bg-[#f9fafb] border border-slate-200 rounded-xl p-3 text-[#141414] shadow-sm">
        <div className="flex justify-between text-[10px] text-slate-500 mb-1.5 font-semibold">
          <span>Gaussian Probability Density</span>
          <span className="text-emerald-700 font-bold">Peak: {meanTempF}°F</span>
        </div>
        <svg viewBox={`0 0 ${svgWidth} ${svgHeight}`} className="w-full h-20 overflow-visible">
          <defs>
            <linearGradient id="curveGrad" x1="0%" y1="0%" x2="100%" y2="0%">
              <stop offset="0%" stopColor="#10B981" />
              <stop offset="50%" stopColor="#F59E0B" />
              <stop offset="100%" stopColor="#EF4444" />
            </linearGradient>
          </defs>

          {/* Baseline */}
          <line x1="10" y1={svgHeight - 15} x2={svgWidth - 10} y2={svgHeight - 15} stroke="#E5E7EB" strokeWidth="1" />

          {/* Curve */}
          {points.length > 1 ? (
            <polyline
              fill="none"
              stroke="url(#curveGrad)"
              strokeWidth="2.5"
              strokeLinecap="round"
              strokeLinejoin="round"
              points={polylinePoints}
            />
          ) : (
            <path
              d="M 10 85 Q 150 15 290 85"
              fill="none"
              stroke="url(#curveGrad)"
              strokeWidth="2.5"
            />
          )}
        </svg>
        <div className="flex justify-between text-[10px] text-slate-600 mt-1 border-t border-slate-200 pt-1.5 font-medium">
          <span>Min: {minTempF}°F</span>
          <span>Mean: {meanTempF}°F</span>
          <span>Max: {maxTempF}°F</span>
        </div>
      </div>

      {/* Statistical Summary Grid */}
      <div className="grid grid-cols-2 gap-2.5 text-xs">
        <div className="p-2.5 rounded-xl bg-[#f9fafb] border border-slate-200 shadow-sm">
          <span className="text-[10px] text-slate-500 block font-medium">Variance / Std Dev</span>
          <span className="font-bold text-[#141414]">±{stdDev.toFixed(3)}°C</span>
        </div>
        <div className="p-2.5 rounded-xl bg-[#f9fafb] border border-slate-200 shadow-sm">
          <span className="text-[10px] text-slate-500 block font-medium">Analysis Mode</span>
          <span className="font-bold text-emerald-700 capitalize">{snapshot?.analysis_layer ?? 'Persistence'}</span>
        </div>
      </div>
    </div>
  )
}
