import type { RiskLevel } from '../types'

interface SafetyProtocolCardProps {
  temperatureF: number
  riskLevel: RiskLevel
}

export default function SafetyProtocolCard({ temperatureF, riskLevel }: SafetyProtocolCardProps) {
  const isExtreme = riskLevel === 'extreme' || temperatureF >= 108
  const isElevated = riskLevel === 'elevated' || (temperatureF >= 100 && temperatureF < 108)

  return (
    <div className="card-surface p-4 space-y-3 font-sans">
      <div className="flex items-center justify-between border-b border-[#e5e5e5] pb-2">
        <div>
          <h3 className="text-xs font-bold text-[#141414]">OSHA & ILO Heat Protocols</h3>
          <span className="text-[10px] text-slate-500 font-medium">Automated Physiological Thresholds</span>
        </div>
        <span className={
          isExtreme
            ? 'badge-rose text-[10px] font-bold'
            : isElevated
            ? 'badge-amber text-[10px] font-bold'
            : 'badge-emerald text-[10px] font-bold'
        }>
          {isExtreme ? 'EMERGENCY' : isElevated ? 'CAUTION' : 'NORMAL'}
        </span>
      </div>

      <div className="grid grid-cols-2 gap-3 text-xs">
        <div className="p-2.5 rounded-xl bg-[#f9fafb] border border-slate-200 space-y-1">
          <span className="text-[10px] text-slate-500 font-semibold block uppercase">Work/Rest Cycle:</span>
          <span className="font-bold text-[#141414] text-xs">
            {isExtreme ? '15 min work / 45 min shade' : isElevated ? '30 min work / 30 min rest' : '50 min work / 10 min rest'}
          </span>
        </div>

        <div className="p-2.5 rounded-xl bg-[#f9fafb] border border-slate-200 space-y-1">
          <span className="text-[10px] text-slate-500 font-semibold block uppercase">Hydration Quota:</span>
          <span className="font-bold text-sky-700 text-xs">
            {isExtreme ? '1.0 Liter / hour' : isElevated ? '0.75 Liter / hour' : '0.50 Liter / hour'}
          </span>
        </div>
      </div>
    </div>
  )
}
