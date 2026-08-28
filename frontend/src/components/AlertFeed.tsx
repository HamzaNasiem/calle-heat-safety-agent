import type { ActionLog } from '../types'

interface AlertFeedProps {
  alerts: ActionLog[]
  onPlayVoice?: (workerName: string, phone: string, lang: 'ur' | 'en') => void
  onTrackCall?: (callId: string) => void
}

const CHANNEL_ICON: Record<string, string> = { voice: '📞', sms: '💬' }

function formatTime(iso: string): string {
  return new Date(iso).toLocaleTimeString('en-US', { hour: '2-digit', minute: '2-digit' })
}

export default function AlertFeed({ alerts, onPlayVoice, onTrackCall }: AlertFeedProps) {
  if (alerts.length === 0) {
    return (
      <div className="flex flex-col items-center justify-center py-8 text-slate-400 font-sans">
        <span className="text-xl mb-1">✓</span>
        <p className="text-xs font-medium">No active alerts</p>
      </div>
    )
  }

  return (
    <div className="space-y-2.5 font-sans">
      {alerts.map((log) => (
        <div
          key={log.id}
          className="p-3 rounded-xl bg-[#f9fafb] border border-slate-200 text-xs shadow-sm space-y-2"
        >
          <div className="flex items-start gap-2.5">
            <span className="text-base shrink-0">
              {CHANNEL_ICON[log.channel]}
            </span>
            <div className="flex-1 min-w-0">
              <div className="flex items-center justify-between gap-2">
                <span className="font-bold text-[#141414] capitalize">
                  {log.channel} dispatch
                </span>
                <span className="text-[10px] text-slate-500 shrink-0 font-medium">{formatTime(log.created_at)}</span>
              </div>
              <p className="text-[10px] text-slate-600 capitalize font-medium mt-0.5">
                Status: <span className="font-bold text-[#141414]">{log.status}</span>
                {log.provider_ref && (
                  <span className="text-slate-700 ml-1 font-mono text-[9px] bg-slate-100 border border-slate-200 px-1.5 py-0.5 rounded">
                    {log.provider_ref}
                  </span>
                )}
              </p>
            </div>
          </div>

          {log.channel === 'voice' && (
            <div className="flex items-center gap-1.5 pt-1">
              {log.provider_ref && log.provider_ref.startsWith('call_') && onTrackCall && (
                <button
                  onClick={() => onTrackCall(log.provider_ref!)}
                  className="flex-1 py-1 text-[10px] font-bold text-white bg-[#141414] hover:bg-[#262626] rounded-lg transition-all flex items-center justify-center gap-1 shadow-sm"
                >
                  <span>🛰️</span>
                  <span>Track CALL-E Live</span>
                </button>
              )}

              {onPlayVoice && (
                <button
                  onClick={() => onPlayVoice('Worker', '+14155552671', 'ur')}
                  className="flex-1 py-1 text-[10px] font-bold text-slate-700 hover:text-[#141414] bg-slate-100 hover:bg-slate-200 rounded-lg transition-all flex items-center justify-center gap-1 border border-slate-200"
                >
                  <span>▶ Play Audio</span>
                </button>
              )}
            </div>
          )}
        </div>
      ))}
    </div>
  )
}
