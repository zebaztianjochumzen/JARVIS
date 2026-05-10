import { useState, useEffect, useRef } from 'react'

// ── Tuning ─────────────────────────────────────────────────────────────────────
const WAKE_WORDS        = ['hey jarvis', 'jarvis']  // longest first
const MIN_CONFIDENCE    = 0.45
const CMD_COOLDOWN_MS   = 3000
const VOICE_THRESHOLD   = 0.018   // RMS amplitude to count as "user speaking"

const mono = { fontFamily: "'Share Tech Mono', monospace" }
const raj  = { fontFamily: "'Rajdhani', sans-serif" }

export default function VoiceControl({ onCommand, onInterrupt, onNotUnderstood, onUserSpeaking }) {
  const [supported, setSupported] = useState(true)
  const lastCmdRef  = useRef(0)
  const restartRef  = useRef(true)

  useEffect(() => {
    const SpeechRec = window.SpeechRecognition || window.webkitSpeechRecognition
    if (!SpeechRec) { setSupported(false); return }

    const rec = new SpeechRec()
    rec.continuous     = true
    rec.interimResults = false
    rec.lang           = 'en-US'
    restartRef.current = true

    rec.onresult = (event) => {
      for (let i = event.resultIndex; i < event.results.length; i++) {
        if (!event.results[i].isFinal) continue
        const conf = event.results[i][0].confidence
        const raw  = event.results[i][0].transcript.toLowerCase().trim()
        console.log(`[voice] heard: "${raw}" (confidence: ${conf.toFixed(2)})`)
        if (conf < MIN_CONFIDENCE) { console.log(`[voice] rejected — confidence too low`); continue }

        // Wake word must be at the very start
        let wakeEnd = -1
        for (const w of WAKE_WORDS) {
          if (raw.startsWith(w)) {
            const end  = w.length
            const next = raw[end]
            if (next === undefined || next === ' ' || next === ',') {
              wakeEnd = end
              break
            }
          }
        }

        if (wakeEnd === -1) { console.log(`[voice] no wake word in: "${raw}"`); continue }

        // Wake word heard — interrupt immediately
        onInterrupt?.()

        const command = raw.slice(wakeEnd).replace(/^[\s,]+/, '').trim()
        console.log(`[voice] wake word! command: "${command}"`)
        if (command.length > 1) {
          const now = Date.now()
          if (now - lastCmdRef.current < CMD_COOLDOWN_MS) { console.log('[voice] cooldown, skipped'); continue }
          lastCmdRef.current = now
          onCommand(command)
        } else {
          onNotUnderstood?.()
        }
      }
    }

    rec.onend   = () => { if (restartRef.current) { console.log('[voice] restarting...'); setTimeout(() => { try { rec.start() } catch {} }, 250) } }
    rec.onerror = (e) => { console.log('[voice] error:', e.error); if (e.error === 'not-allowed') setSupported(false) }

    console.log('[voice] starting speech recognition')
    try { rec.start() } catch {}
    return () => { restartRef.current = false; rec.onend = null; try { rec.stop() } catch {} }
  }, [onCommand, onInterrupt, onNotUnderstood])

  // ── Mic amplitude → voice-reactive orb ────────────────────────────────────
  useEffect(() => {
    if (!onUserSpeaking) return
    let animId = null, audioCtx = null, cleanup = null
    let speaking = false

    navigator.mediaDevices.getUserMedia({ audio: true, video: false })
      .then(stream => {
        audioCtx = new AudioContext()
        const src      = audioCtx.createMediaStreamSource(stream)
        const analyser = audioCtx.createAnalyser()
        analyser.fftSize = 512
        analyser.smoothingTimeConstant = 0.4
        src.connect(analyser)
        const buf = new Float32Array(analyser.fftSize)

        function tick() {
          analyser.getFloatTimeDomainData(buf)
          let sum = 0
          for (const v of buf) sum += v * v
          const rms = Math.sqrt(sum / buf.length)
          const isSpeaking = rms > VOICE_THRESHOLD
          if (isSpeaking !== speaking) {
            speaking = isSpeaking
            onUserSpeaking(isSpeaking)
          }
          animId = requestAnimationFrame(tick)
        }
        tick()
        cleanup = () => { cancelAnimationFrame(animId); stream.getTracks().forEach(t => t.stop()); audioCtx?.close() }
      })
      .catch(() => {})

    return () => cleanup?.()
  }, [onUserSpeaking])

  if (!supported) return null

  return (
    <div style={{
      position: 'fixed', bottom: 90, right: 20, zIndex: 200,
      background: 'rgba(2,6,14,0.72)', backdropFilter: 'blur(8px)',
      border: '1px solid rgba(79,195,247,0.1)', borderRadius: 6,
      padding: '8px 13px', pointerEvents: 'none',
    }}>
      <div style={{ ...raj, fontSize: 8, letterSpacing: 4, color: 'rgba(79,195,247,0.35)', marginBottom: 6 }}>
        VOICE  CONTROL
      </div>
      <div style={{ display: 'flex', flexDirection: 'column', gap: 4 }}>
        <Row dot label='SPEECH ACTIVE' />
        <Row dot label='"JARVIS, [command]"' dim />
      </div>
    </div>
  )
}

function Row({ dot, label, dim }) {
  return (
    <div style={{ display: 'flex', alignItems: 'center', gap: 6 }}>
      <div style={{
        width: 5, height: 5, borderRadius: '50%',
        background: dot ? (dim ? 'rgba(79,195,247,0.4)' : '#4fc3f7') : 'rgba(79,195,247,0.15)',
        flexShrink: 0,
      }} />
      <span style={{
        ...mono, fontSize: 9,
        color: dim ? 'rgba(79,195,247,0.3)' : 'rgba(79,195,247,0.55)',
        letterSpacing: 0.5,
      }}>{label}</span>
    </div>
  )
}
