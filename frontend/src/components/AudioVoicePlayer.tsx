import { useState, useEffect } from 'react'

interface AudioVoicePlayerProps {
  workerName: string
  siteName: string
  surfaceTempF: number
  refugeName: string
  reliefDeltaF: number
  language?: string
  onDirectCallClick?: () => void
}

export default function AudioVoicePlayer({
  workerName,
  siteName,
  surfaceTempF,
  refugeName,
  reliefDeltaF,
  onDirectCallClick,
}: AudioVoicePlayerProps) {
  const [isPlaying, setIsPlaying] = useState(false)
  const [hasSpeechSupport, setHasSpeechSupport] = useState(true)

  useEffect(() => {
    if (!('speechSynthesis' in window)) {
      setHasSpeechSupport(false)
    }
  }, [])

  const englishScript = `Attention ${workerName || 'Site Supervisor'}! This is the CALL-E Heat Guardian autonomous heat safety dispatch. A hazardous surface asphalt temperature of ${Math.round(surfaceTempF)} degrees Fahrenheit has been detected at ${siteName || 'your industrial worksite'}. In accordance with OSHA emergency heat protocols, halt heavy outdoor operations immediately and relocate all personnel to ${refugeName || 'Zone D Cooling Canopy'} for ${Math.round(reliefDeltaF)} degrees of cooling relief.`

  // Play modern alert chime via Web Audio API before voice
  function playAlertChime() {
    try {
      const AudioContext = window.AudioContext || (window as any).webkitAudioContext
      if (!AudioContext) return
      const ctx = new AudioContext()
      const osc = ctx.createOscillator()
      const gain = ctx.createGain()
      osc.type = 'sine'
      osc.frequency.setValueAtTime(587.33, ctx.currentTime) // D5
      osc.frequency.setValueAtTime(880.00, ctx.currentTime + 0.12) // A5
      gain.gain.setValueAtTime(0.2, ctx.currentTime)
      gain.gain.exponentialRampToValueAtTime(0.001, ctx.currentTime + 0.35)
      osc.connect(gain)
      gain.connect(ctx.destination)
      osc.start()
      osc.stop(ctx.currentTime + 0.35)
    } catch {}
  }

  function handlePlayAudio() {
    if (!('speechSynthesis' in window)) return

    if (isPlaying) {
      window.speechSynthesis.cancel()
      setIsPlaying(false)
      return
    }

    playAlertChime()

    window.speechSynthesis.cancel()
    if (window.speechSynthesis.paused) {
      window.speechSynthesis.resume()
    }

    const utterance = new SpeechSynthesisUtterance(englishScript)
    utterance.rate = 0.96
    utterance.pitch = 1.0
    utterance.lang = 'en-US'

    const voices = window.speechSynthesis.getVoices()
    const enVoice = voices.find((v) => v.lang.startsWith('en') && (v.name.includes('Google') || v.name.includes('Natural') || v.name.includes('Neural') || v.name.includes('David') || v.name.includes('Zira')))
    if (enVoice) utterance.voice = enVoice

    utterance.onstart = () => setIsPlaying(true)
    utterance.onend = () => setIsPlaying(false)
    utterance.onerror = (e) => {
      console.warn('SpeechSynthesis error:', e)
      setIsPlaying(false)
    }

    setTimeout(() => {
      window.speechSynthesis.speak(utterance)
    }, 150)
  }

  if (!hasSpeechSupport) return null

  return (
    <div className="card-surface p-4 space-y-3 font-sans">
      {/* Header */}
      <div className="flex items-center justify-between border-b border-[#e5e5e5] pb-3">
        <div className="flex items-center gap-2">
          <div className="w-6 h-6 rounded-lg bg-emerald-50 border border-emerald-200 flex items-center justify-center text-emerald-700">
            <svg className="w-3.5 h-3.5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15.536 8.464a5 5 0 010 7.072m2.828-9.9a9 9 0 010 12.728M5.586 15H4a1 1 0 01-1-1v-4a1 1 0 011-1h1.586l4.707-4.707C10.923 3.663 12 4.109 12 5v14c0 .891-1.077 1.337-1.707.707L5.586 15z" />
            </svg>
          </div>
          <div>
            <h4 className="text-xs font-bold text-[#141414]">
              Voice Dispatch Simulator
            </h4>
            <p className="text-[10px] text-slate-500 font-medium">
              Autonomous English Emergency Broadcast
            </p>
          </div>
        </div>

        <span className="badge-slate text-[10px] font-semibold">
          en-US Synthesizer
        </span>
      </div>

      {/* Script Box */}
      <div className="p-3 rounded-xl bg-[#f9fafb] border border-slate-200 space-y-1 text-xs">
        <div className="flex items-center justify-between text-[10px] text-slate-500 font-semibold">
          <span>Broadcast Transmission Script:</span>
          <span>English (Standard)</span>
        </div>
        <p className="text-[11px] leading-relaxed text-slate-800 font-medium">
          {englishScript}
        </p>
      </div>

      {/* Controls */}
      <div className="flex items-center justify-between pt-1 gap-2">
        <button
          onClick={handlePlayAudio}
          className={`btn-primary text-xs ${
            isPlaying ? 'bg-rose-600 hover:bg-rose-500 animate-pulse' : ''
          }`}
        >
          {isPlaying ? (
            <>
              <svg className="w-3.5 h-3.5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <rect x="6" y="6" width="12" height="12" strokeWidth={2} strokeLinecap="round" strokeLinejoin="round" />
              </svg>
              <span>Stop Audio</span>
            </>
          ) : (
            <>
              <svg className="w-3.5 h-3.5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <polygon points="5 3 19 12 5 21 5 3" strokeWidth={2} strokeLinecap="round" strokeLinejoin="round" />
              </svg>
              <span>Play Warning Broadcast</span>
            </>
          )}
        </button>

        {onDirectCallClick && (
          <button
            onClick={onDirectCallClick}
            className="btn-secondary text-xs"
            title="Dispatch call to real phone"
          >
            <svg className="w-3.5 h-3.5 text-slate-600" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M3 5a2 2 0 012-2h3.28a1 1 0 01.948.684l1.498 4.493a1 1 0 01-.502 1.21l-2.257 1.13a11.042 11.042 0 005.516 5.516l1.13-2.257a1 1 0 011.21-.502l4.493 1.498a1 1 0 01.684.949V19a2 2 0 01-2 2h-1C9.716 21 3 14.284 3 6V5z" />
            </svg>
            <span>Dial Cellular Phone</span>
          </button>
        )}
      </div>
    </div>
  )
}
