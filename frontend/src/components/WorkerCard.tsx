import type { Worker } from '../types'

interface WorkerCardProps {
  worker: Worker
}

export default function WorkerCard({ worker }: WorkerCardProps) {
  const isNotified = worker.status === 'notified'
  const isSafe = worker.status === 'safe'

  return (
    <div className="p-3 rounded-xl bg-[#ffffff] border border-slate-200 text-xs flex items-center justify-between gap-3 hover:border-slate-300 transition-colors shadow-sm">
      <div className="flex items-center gap-2.5 min-w-0">
        <div className="w-7 h-7 rounded-lg bg-slate-100 border border-slate-200 text-slate-800 flex items-center justify-center font-bold text-xs shrink-0">
          {worker.name.charAt(0)}
        </div>
        <div className="min-w-0">
          <span className="font-semibold text-[#141414] text-xs block truncate">
            {worker.name}
          </span>
          <span className="text-[11px] text-slate-500 block truncate font-mono">
            {worker.phone_number} · <span className="uppercase text-slate-600 font-semibold">{worker.preferred_language || 'en'}</span>
          </span>
        </div>
      </div>

      <span
        className={
          isNotified
            ? 'badge-rose text-[10px] uppercase font-bold'
            : isSafe
            ? 'badge-emerald text-[10px] uppercase font-bold'
            : 'badge-amber text-[10px] uppercase font-bold'
        }
      >
        {isNotified ? 'Alerted' : isSafe ? 'Safe' : 'Cooling'}
      </span>
    </div>
  )
}
