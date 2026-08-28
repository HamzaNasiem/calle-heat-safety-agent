import { useState } from 'react'
import type { HourlyForecastPoint } from '../types'

interface HourlyThermalForecastChartProps {
  data: HourlyForecastPoint[]
}

export function HourlyThermalForecastChart({ data }: HourlyThermalForecastChartProps) {
  const [hoverIdx, setHoverIdx] = useState<number | null>(null)

  if (!data || data.length === 0) {
    return null
  }

  const width = 800
  const height = 260
  const margin = { top: 20, right: 30, bottom: 50, left: 45 }

  const innerWidth = width - margin.left - margin.right
  const innerHeight = height - margin.top - margin.bottom

  const allTemps = data.flatMap((d) => [d.surface_temp_f, d.ambient_temp_f, d.canopy_temp_f])
  const maxTemp = Math.max(...allTemps, 130)
  const minTemp = Math.min(...allTemps, 70)

  const getX = (index: number) => margin.left + (index / (data.length - 1 || 1)) * innerWidth
  const getY = (temp: number) => margin.top + innerHeight - ((temp - minTemp) / (maxTemp - minTemp || 1)) * innerHeight

  const surfacePath = data.map((d, i) => `${i === 0 ? 'M' : 'L'} ${getX(i)} ${getY(d.surface_temp_f)}`).join(' ')
  const airPath = data.map((d, i) => `${i === 0 ? 'M' : 'L'} ${getX(i)} ${getY(d.ambient_temp_f)}`).join(' ')
  const canopyPath = data.map((d, i) => `${i === 0 ? 'M' : 'L'} ${getX(i)} ${getY(d.canopy_temp_f)}`).join(' ')

  const getOshaBadge = (ratio: string) => {
    switch (ratio) {
      case '15/45':
        return 'bg-rose-50 text-rose-700 border-rose-200'
      case '30/30':
        return 'bg-orange-50 text-orange-800 border-orange-200'
      case '50/10':
        return 'bg-amber-50 text-amber-800 border-amber-200'
      default:
        return 'bg-emerald-50 text-emerald-700 border-emerald-200'
    }
  }

  return (
    <div className="card-surface p-5 space-y-4 shadow-sm">
      <div className="flex flex-wrap items-center justify-between border-b border-[#e5e5e5] pb-3 gap-2">
        <div>
          <h3 className="text-xs font-bold text-[#141414] tracking-tight">
            Diurnal Heat Curve & OSHA Shift Trajectory (09:00 - 18:00)
          </h3>
          <span className="text-[11px] text-slate-500 font-medium">
            Hourly Surface Asphalt Absorption vs Shaded Canopy Microclimate
          </span>
        </div>

        {/* Legend */}
        <div className="flex flex-wrap items-center gap-2.5 sm:gap-4 text-xs font-semibold">
          <div className="flex items-center gap-1.5">
            <span className="w-2.5 h-2.5 rounded-full bg-[#EF4444]" />
            <span className="text-rose-600">Surface Asphalt</span>
          </div>
          <div className="flex items-center gap-1.5">
            <span className="w-2.5 h-2.5 rounded-full bg-[#F59E0B]" />
            <span className="text-amber-600">Ambient Air</span>
          </div>
          <div className="flex items-center gap-1.5">
            <span className="w-2.5 h-2.5 rounded-full bg-[#10B981]" />
            <span className="text-emerald-600">Canopy Refuge</span>
          </div>
          <div className="flex items-center gap-1.5">
            <span className="w-2.5 h-2.5 rounded-full bg-purple-600 ring-2 ring-purple-300 animate-pulse" />
            <span className="text-purple-700">Recorded Snapshots</span>
          </div>
        </div>
      </div>

      <div className="relative w-full overflow-x-auto">
        <svg viewBox={`0 0 ${width} ${height}`} className="w-full h-auto min-w-[650px]">
          {/* Y Axis Grid Lines */}
          {[...Array(5)].map((_, i) => {
            const temp = minTemp + (i / 4) * (maxTemp - minTemp)
            return (
              <g key={i}>
                <line
                  x1={margin.left}
                  y1={getY(temp)}
                  x2={width - margin.right}
                  y2={getY(temp)}
                  stroke="#E5E7EB"
                  strokeDasharray="3 3"
                />
                <text
                  x={margin.left - 8}
                  y={getY(temp)}
                  fill="#6B7280"
                  fontSize="10"
                  fontWeight="600"
                  textAnchor="end"
                  dominantBaseline="middle"
                  fontFamily="monospace"
                >
                  {Math.round(temp)}°F
                </text>
              </g>
            )
          })}

          {/* Area Fill Gradient */}
          <path
            d={`${surfacePath} L ${getX(data.length - 1)} ${height - margin.bottom} L ${getX(0)} ${height - margin.bottom} Z`}
            fill="rgba(239, 68, 68, 0.05)"
          />

          {/* Spline Paths */}
          <path d={surfacePath} fill="none" stroke="#EF4444" strokeWidth="2.5" />
          <path d={airPath} fill="none" stroke="#F59E0B" strokeWidth="2.5" />
          <path d={canopyPath} fill="none" stroke="#10B981" strokeWidth="2.5" />

          {/* Points & Interactive Hover Columns */}
          {data.map((d, i) => {
            const isRecorded = d.point_type === 'recorded'
            return (
              <g
                key={i}
                onMouseEnter={() => setHoverIdx(i)}
                onMouseLeave={() => setHoverIdx(null)}
                className="cursor-pointer"
              >
                <rect
                  x={getX(i) - innerWidth / (data.length * 2)}
                  y={margin.top}
                  width={innerWidth / data.length}
                  height={innerHeight}
                  fill="transparent"
                />

                {hoverIdx === i && (
                  <line
                    x1={getX(i)}
                    y1={margin.top}
                    x2={getX(i)}
                    y2={height - margin.bottom}
                    stroke="#94A3B8"
                    strokeWidth="1.5"
                    strokeDasharray="4 4"
                  />
                )}

                {/* If recorded snapshot, render glowing halo */}
                {isRecorded && (
                  <circle
                    cx={getX(i)}
                    cy={getY(d.ambient_temp_f)}
                    r={8}
                    fill="none"
                    stroke="#9333EA"
                    strokeWidth="2"
                    className="animate-ping opacity-50"
                  />
                )}

                <circle cx={getX(i)} cy={getY(d.surface_temp_f)} r={hoverIdx === i ? 5 : 3.5} fill="#EF4444" />
                <circle cx={getX(i)} cy={getY(d.ambient_temp_f)} r={hoverIdx === i ? 5 : (isRecorded ? 4.5 : 3.5)} fill={isRecorded ? '#9333EA' : '#F59E0B'} />
                <circle cx={getX(i)} cy={getY(d.canopy_temp_f)} r={hoverIdx === i ? 5 : 3.5} fill="#10B981" />

                {/* X Axis Time Labels */}
                <text
                  x={getX(i)}
                  y={height - margin.bottom + 18}
                  fill={isRecorded ? '#9333EA' : '#4B5563'}
                  fontWeight={isRecorded ? 'bold' : '600'}
                  fontSize="10"
                  textAnchor="middle"
                  fontFamily="monospace"
                >
                  {d.time_label || `${d.hour}:00`}
                </text>
              </g>
            )
          })}
        </svg>

        {/* Hover Tooltip Box */}
        {hoverIdx !== null && data[hoverIdx] && (
          <div
            className="absolute bg-[#ffffff]/95 backdrop-blur-md border border-slate-200 p-3 rounded-xl shadow-xl text-xs text-[#141414] pointer-events-none z-10 space-y-1 w-64"
            style={{
              left: Math.min(Math.max(getX(hoverIdx) - 100, 10), width - 270) + 'px',
              top: '10px'
            }}
          >
            <div className="font-bold text-[#141414] border-b border-slate-100 pb-1 flex justify-between">
              <span>{data[hoverIdx].time_label}</span>
              <span className={`text-[10px] font-bold px-1.5 py-0.5 rounded ${data[hoverIdx].point_type === 'recorded' ? 'bg-purple-50 text-purple-700 border border-purple-200' : 'text-slate-600'}`}>
                {data[hoverIdx].point_type === 'recorded' ? '🟣 DB Snapshot' : '📈 Diurnal Model'}
              </span>
            </div>
            <div className="text-rose-600 flex justify-between font-medium">
              <span>Ground Asphalt:</span>
              <strong className="font-bold">{data[hoverIdx].surface_temp_f}°F</strong>
            </div>
            <div className="text-amber-600 flex justify-between font-medium">
              <span>Ambient Weather:</span>
              <strong className="font-bold">{data[hoverIdx].ambient_temp_f}°F</strong>
            </div>
            <div className="text-emerald-600 flex justify-between font-medium">
              <span>Shaded Canopy:</span>
              <strong className="font-bold">{data[hoverIdx].canopy_temp_f}°F</strong>
            </div>
            <div className="pt-1 text-[10px] text-slate-500 border-t border-slate-100 flex justify-between font-semibold">
              <span>Solar: {data[hoverIdx].solar_radiation_w_m2} W/m²</span>
              <span className="text-[#141414]">OSHA: {data[hoverIdx].work_rest_ratio}</span>
            </div>
          </div>
        )}
      </div>

      {/* Bottom OSHA Shift Schedule Badges */}
      <div className="flex overflow-x-auto gap-2 pt-1">
        {data.map((d, i) => (
          <div key={i} className="flex-1 min-w-[65px] text-center space-y-0.5">
            <div className={`text-[10px] font-bold py-1 px-1 rounded-lg border shadow-sm ${getOshaBadge(d.work_rest_ratio)}`}>
              {d.work_rest_ratio}
            </div>
            <span className="text-[9px] text-slate-500 font-semibold block">{d.time_label}</span>
          </div>
        ))}
      </div>
    </div>
  )
}
