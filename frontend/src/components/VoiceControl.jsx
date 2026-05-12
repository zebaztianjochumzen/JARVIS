import { useState, useEffect, useRef } from 'react'

// ── Tuning ─────────────────────────────────────────────────────────────────────
const WAKE_WORDS      = ['hey jarvis', 'jarvis']  // longest first
const MIN_CONFIDENCE  = 0.45
const CMD_COOLDOWN_MS = 3000
const VOICE_THRESHOLD = 0.018

const mono = { fontFamily: "'Share Tech Mono', monospace" }
const raj  = { fontFamily: "'Rajdhani', sans-serif" }

// ── Pick the built-in Mac microphone, never the iPhone ────────────────────────
async function getBuiltinMicStream() {
  // Trigger permission so device labels become available
  try {
    const perm = await navigator.mediaDevices.getUserMedia({ audio: true })
    perm.getTracks().forEach(t => t.stop())
  } catch {
    return null
  }

  const devices = await navigator.mediaDevices.enumerateDevices()
  const inputs  = devices.filter(d => d.kind === 'audioinput')

  const builtin = inputs.find(d => {
    const label = d.label.toLowerCase()
    return (
      label.includes('built-in') ||
      label.includes('macbook') ||
      label.includes('internal')
    ) && !label.includes('iphone') && !label.includes('continuity')
  })

  if (builtin) {
    console.log(`[voice] mic selected: "${builtin.label}"`)
    return navigator.mediaDevices.getUserMedia({
      audio: { deviceId: { exact: builtin.deviceId } },
      video: false,
    })
  }

  // Fallback: default device
  console.log('[voice] no built-in mic found, using default')
  return navigator.mediaDevices.getUserMedia({ audio: true, video: false })
}

export default function VoiceControl({ onCommand, onInterrupt, onNotUnderstood, onUserSpeaking }) {
  const [supported, setSupported] = useState(true)
  const [micLabel,  setMicLabel]  = useState('')
  const lastCmdRef  = useRef(0)
  const restartRef  = useRef(true)

  // ── Speech recognition ────────────────────────────────────────────────────
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
        console.log(`[voice] heard: "${raw}" (conf: ${conf.toFixed(2)})`)
        if (conf < MIN_CONFIDENCE) { console.log('[voice] rejected — low confidence'); continue }

        let wakeEnd = -1
        for (const w of WAKE_WORDS) {
          if (raw.startsWith(w)) {
            const next = raw[w.length]
            if (next === undefined || next === ' ' || next === ',') {
              wakeEnd = w.length
              break
            }
          }
        }

        if (wakeEnd === -1) { console.log(`[voice] no wake word`); continue }

        onInterrupt?.()

        const command = raw.slice(wakeEnd).replace(/^[\s,]+/, '').trim()
        console.log(`[voice] command: "${command}"`)
        if (command.length > 1) {
          const now = Date.now()
          if (now - lastCmdRef.current < CMD_COOLDOWN_MS) { console.log('[voice] cooldown'); continue }
          lastCmdRef.current = now
          onCommand(command)
        } else {
          onNotUnderstood?.()
        }
      }
    }

    rec.onend   = () => {
      if (restartRef.current) setTimeout(() => { try { rec.start() } catch {} }, 250)
    }
    rec.onerror = (e) => {
      console.log('[voice] error:', e.error)
      if (e.error === 'not-allowed') setSupported(false)
    }

    console.log('[voice] starting speech recognition')
    try { rec.start() } catch {}
    return () => { restartRef.current = false; rec.onend = null; try { rec.stop() } catch {} }
  }, [onCommand, onInterrupt, onNotUnderstood])

  // ── Mic amplitude → voice-reactive orb (always built-in mic) ─────────────
  useEffect(() => {
    if (!onUserSpeaking) return
    let animId = null, audioCtx = null, cleanup = null
    let speaking = false

    getBuiltinMicStream()
      .then(stream => {
        if (!stream) return
        // Show which mic we're using in the UI
        const track = stream.getAudioTracks()[0]
        if (track) setMicLabel(track.label)

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
          if (isSpeaking !== speaking) { speaking = isSpeaking; onUserSpeaking(isSpeaking) }
          animId = requestAnimationFrame(tick)
        }
        tick()
        cleanup = () => {
          cancelAnimationFrame(animId)
          stream.getTracks().forEach(t => t.stop())
          audioCtx?.close()
        }
      })
      .catch(() => {})

    return () => cleanup?.()
  }, [onUserSpeaking])

  if (!supported) return null

  // Shorten the mic label for display
  const shortLabel = micLabel
    ? micLabel.replace(/microphone/i, 'MIC').replace(/\(.*?\)/g, '').trim().toUpperCase()
    : 'DETECTING...'

  const isPhone = micLabel.toLowerCase().includes('iphone') ||
                  micLabel.toLowerCase().includes('continuity')

  return (
    <div style={{
      position: 'fixed', bottom: 90, right: 20, zIndex: 200,
      background: 'rgba(2,6,14,0.72)', backdropFilter: 'blur(8px)',
      border: `1px solid ${isPhone ? 'rgba(255,100,80,0.3)' : 'rgba(79,195,247,0.1)'}`,
      borderRadius: 6, padding: '8px 13px', pointerEvents: 'none',
    }}>
      <div style={{ ...raj, fontSize: 8, letterSpacing: 4, color: 'rgba(79,195,247,0.35)', marginBottom: 6 }}>
        VOICE  CONTROL
      </div>
      <div style={{ display: 'flex', flexDirection: 'column', gap: 4 }}>
        <Row dot label='SPEECH ACTIVE' />
        <Row dot label='"JARVIS, [command]"' dim />
        <Row label={shortLabel} dim color={isPhone ? 'rgba(255,120,80,0.7)' : undefined} />
      </div>
    </div>
  )
}

function Row({ dot, label, dim, color }) {
  return (
    <div style={{ display: 'flex', alignItems: 'center', gap: 6 }}>
      <div style={{
        width: 5, height: 5, borderRadius: '50%',
        background: dot ? (dim ? 'rgba(79,195,247,0.4)' : '#4fc3f7') : 'rgba(79,195,247,0.15)',
        flexShrink: 0,
      }} />
      <span style={{
        ...mono, fontSize: 9,
        color: color || (dim ? 'rgba(79,195,247,0.3)' : 'rgba(79,195,247,0.55)'),
        letterSpacing: 0.5,
      }}>{label}</span>
    </div>
  )
}
