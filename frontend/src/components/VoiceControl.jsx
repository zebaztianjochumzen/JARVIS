import { useState, useEffect, useRef, useCallback } from 'react'

// ── Constants ─────────────────────────────────────────────────────────────────
const WAKE_WORDS      = ['hey jarvis', 'jarvis']
const MIN_CONFIDENCE  = 0.45
const CMD_COOLDOWN_MS = 3000
const VOICE_THRESHOLD = 0.018
const SILENCE_MS      = 1400   // stop recording after this ms of silence
const MAX_RECORD_MS   = 15000  // hard cap on recording length

const WS_WAKEWORD_URL    = 'ws://localhost:8000/ws/wakeword'
const TRANSCRIBE_URL     = 'http://localhost:8000/api/transcribe'

const mono = { fontFamily: "'Share Tech Mono', monospace" }
const raj  = { fontFamily: "'Rajdhani', sans-serif" }

// ── Voice state machine ────────────────────────────────────────────────────────
// IDLE → RECORDING → TRANSCRIBING → IDLE
// IDLE is also the state while the browser SpeechAPI is passively listening

// ── Helper: pick the built-in mic ────────────────────────────────────────────
async function getBuiltinMicStream(constraints = {}) {
  try {
    const perm = await navigator.mediaDevices.getUserMedia({ audio: true })
    perm.getTracks().forEach(t => t.stop())
  } catch { return null }

  const devices = await navigator.mediaDevices.enumerateDevices()
  const inputs  = devices.filter(d => d.kind === 'audioinput')
  const builtin = inputs.find(d => {
    const l = d.label.toLowerCase()
    return (l.includes('built-in') || l.includes('macbook') || l.includes('internal'))
      && !l.includes('iphone') && !l.includes('continuity')
  })

  const deviceId = builtin?.deviceId
  return navigator.mediaDevices.getUserMedia({
    audio: deviceId ? { deviceId: { exact: deviceId }, ...constraints } : constraints,
    video: false,
  })
}

// ── Silence-aware MediaRecorder helper ────────────────────────────────────────
async function recordUntilSilence(stream, onData) {
  return new Promise((resolve) => {
    const mimeType = MediaRecorder.isTypeSupported('audio/webm;codecs=opus')
      ? 'audio/webm;codecs=opus'
      : 'audio/webm'

    const recorder = new MediaRecorder(stream, { mimeType })
    const chunks   = []

    const audioCtx  = new AudioContext()
    const src       = audioCtx.createMediaStreamSource(stream)
    const analyser  = audioCtx.createAnalyser()
    analyser.fftSize = 512
    analyser.smoothingTimeConstant = 0.4
    src.connect(analyser)
    const buf = new Float32Array(analyser.fftSize)

    let silenceStart = null
    let stopped      = false
    let rafId        = null

    function stop() {
      if (stopped) return
      stopped = true
      cancelAnimationFrame(rafId)
      try { recorder.stop() } catch {}
      audioCtx.close()
    }

    const hardStop = setTimeout(stop, MAX_RECORD_MS)

    function tick() {
      analyser.getFloatTimeDomainData(buf)
      let sum = 0
      for (const v of buf) sum += v * v
      const rms = Math.sqrt(sum / buf.length)

      if (rms > VOICE_THRESHOLD) {
        silenceStart = null
      } else {
        if (!silenceStart) silenceStart = Date.now()
        if (Date.now() - silenceStart > SILENCE_MS) { stop(); return }
      }
      rafId = requestAnimationFrame(tick)
    }

    recorder.ondataavailable = e => { if (e.data?.size > 0) chunks.push(e.data) }
    recorder.onstop = () => {
      clearTimeout(hardStop)
      const blob = new Blob(chunks, { type: mimeType })
      onData?.(blob)
      resolve(blob)
    }

    recorder.start(100)
    tick()
  })
}

// ── Main component ────────────────────────────────────────────────────────────
export default function VoiceControl({ onCommand, onInterrupt, onNotUnderstood, onUserSpeaking }) {
  const [supported,    setSupported]    = useState(true)
  const [micLabel,     setMicLabel]     = useState('')
  const [voiceMode,    setVoiceMode]    = useState('browser') // 'browser' | 'whisper'
  const [recState,     setRecState]     = useState('idle')    // 'idle' | 'recording' | 'transcribing'
  const [wakeActive,   setWakeActive]   = useState(false)     // backend wake word connected
  const [pttHeld,      setPttHeld]      = useState(false)

  const lastCmdRef   = useRef(0)
  const restartRef   = useRef(true)
  const streamRef    = useRef(null)   // mic stream reused across recordings
  const recActiveRef = useRef(false)  // prevent double-recordings
  const wwWsRef      = useRef(null)   // wakeword WebSocket

  // ── Whisper transcription ─────────────────────────────────────────────────
  const transcribeAndSend = useCallback(async (blob) => {
    if (!blob || blob.size < 500) { setRecState('idle'); return }
    setRecState('transcribing')
    try {
      const form = new FormData()
      form.append('audio', blob, 'audio.webm')
      form.append('format', 'webm')

      const res  = await fetch(TRANSCRIBE_URL, { method: 'POST', body: form })
      const data = await res.json()
      const text = (data.transcript || '').trim()

      console.log('[Whisper] transcript:', text)

      if (text.length > 1) {
        const now = Date.now()
        if (now - lastCmdRef.current >= CMD_COOLDOWN_MS) {
          lastCmdRef.current = now
          onCommand(text)
        }
      } else {
        onNotUnderstood?.()
      }
    } catch (err) {
      console.warn('[Whisper] transcription failed:', err)
      onNotUnderstood?.()
    } finally {
      setRecState('idle')
      recActiveRef.current = false
    }
  }, [onCommand, onNotUnderstood])

  // ── Start a Whisper recording session ─────────────────────────────────────
  const startWhisperRecording = useCallback(async () => {
    if (recActiveRef.current) return
    recActiveRef.current = true
    onInterrupt?.()
    setRecState('recording')

    try {
      if (!streamRef.current || streamRef.current.getTracks().every(t => t.readyState === 'ended')) {
        streamRef.current = await getBuiltinMicStream()
      }
      if (!streamRef.current) { recActiveRef.current = false; setRecState('idle'); return }

      const blob = await recordUntilSilence(streamRef.current, null)
      await transcribeAndSend(blob)
    } catch (err) {
      console.warn('[Whisper] recording error:', err)
      recActiveRef.current = false
      setRecState('idle')
    }
  }, [onInterrupt, transcribeAndSend])

  // ── Backend wake-word WebSocket ───────────────────────────────────────────
  useEffect(() => {
    if (voiceMode !== 'whisper') return

    let ws   = null
    let dead = false

    function connect() {
      if (dead) return
      ws = new WebSocket(WS_WAKEWORD_URL)
      wwWsRef.current = ws

      ws.onopen = () => {
        setWakeActive(true)
        console.log('[WakeWord] backend connected')
      }
      ws.onmessage = (e) => {
        try {
          const msg = JSON.parse(e.data)
          if (msg.type === 'wake_word_detected') {
            console.log('[WakeWord] triggered from backend')
            startWhisperRecording()
          }
        } catch {}
      }
      ws.onclose = () => {
        setWakeActive(false)
        if (!dead) setTimeout(connect, 4000)
      }
      ws.onerror = () => ws.close()
    }

    connect()
    return () => {
      dead = true
      setWakeActive(false)
      try { ws?.close() } catch {}
    }
  }, [voiceMode, startWhisperRecording])

  // ── Browser Speech API (always-on fallback + browser mode) ───────────────
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
        console.log(`[BrowserSTT] heard: "${raw}" (conf: ${conf.toFixed(2)})`)
        if (conf < MIN_CONFIDENCE) continue

        let wakeEnd = -1
        for (const w of WAKE_WORDS) {
          if (raw.startsWith(w)) {
            const next = raw[w.length]
            if (next === undefined || next === ' ' || next === ',') { wakeEnd = w.length; break }
          }
        }
        if (wakeEnd === -1) continue

        onInterrupt?.()

        const command = raw.slice(wakeEnd).replace(/^[\s,]+/, '').trim()
        console.log(`[BrowserSTT] command: "${command}"`)

        if (voiceMode === 'whisper' && !wakeActive) {
          // Backend ws not connected yet — use browser STT as fallback text
          if (command.length > 1) {
            const now = Date.now()
            if (now - lastCmdRef.current >= CMD_COOLDOWN_MS) {
              lastCmdRef.current = now
              onCommand(command)
            }
          } else {
            onNotUnderstood?.()
          }
          return
        }

        if (voiceMode === 'browser') {
          if (command.length > 1) {
            const now = Date.now()
            if (now - lastCmdRef.current >= CMD_COOLDOWN_MS) {
              lastCmdRef.current = now
              onCommand(command)
            }
          } else {
            // Wake word said alone — in whisper mode kick off a recording
            if (voiceMode === 'whisper') startWhisperRecording()
            else onNotUnderstood?.()
          }
        }
        // In whisper mode, backend listener handles the actual recording
        // The browser STT just handles text preview / fallback above
      }
    }

    rec.onend   = () => { if (restartRef.current) setTimeout(() => { try { rec.start() } catch {} }, 250) }
    rec.onerror = (e) => { if (e.error === 'not-allowed') setSupported(false) }

    try { rec.start() } catch {}
    return () => { restartRef.current = false; rec.onend = null; try { rec.stop() } catch {} }
  }, [voiceMode, wakeActive, onCommand, onInterrupt, onNotUnderstood, startWhisperRecording])

  // ── Mic amplitude → voice-reactive orb ───────────────────────────────────
  useEffect(() => {
    if (!onUserSpeaking) return
    let animId = null, audioCtx = null, cleanup = null
    let speaking = false

    getBuiltinMicStream()
      .then(stream => {
        if (!stream) return
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
          const rms       = Math.sqrt(sum / buf.length)
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

  // ── Push-to-talk: mouse/touch handlers ───────────────────────────────────
  const handlePttDown = useCallback((e) => {
    e.preventDefault()
    setPttHeld(true)
    if (voiceMode === 'whisper') startWhisperRecording()
  }, [voiceMode, startWhisperRecording])

  const handlePttUp = useCallback((e) => {
    e.preventDefault()
    setPttHeld(false)
  }, [])

  if (!supported) return null

  const shortLabel = micLabel
    ? micLabel.replace(/microphone/i, 'MIC').replace(/\(.*?\)/g, '').trim().toUpperCase()
    : 'DETECTING...'
  const isPhone = micLabel.toLowerCase().includes('iphone') || micLabel.toLowerCase().includes('continuity')

  const recColor = recState === 'recording'     ? '#f44'
                 : recState === 'transcribing'  ? '#fa0'
                 : voiceMode === 'whisper'       ? '#4fc3f7'
                 : '#4fc3f7'

  const modeLabel = voiceMode === 'whisper'
    ? (recState === 'recording' ? 'RECORDING...' : recState === 'transcribing' ? 'TRANSCRIBING...' : wakeActive ? 'WHISPER + HW WAKE' : 'WHISPER MODE')
    : 'BROWSER STT'

  return (
    <div style={{
      position: 'fixed', bottom: 90, right: 20, zIndex: 200,
      background: 'rgba(2,6,14,0.82)', backdropFilter: 'blur(8px)',
      border: `1px solid ${isPhone ? 'rgba(255,100,80,0.3)' : 'rgba(79,195,247,0.15)'}`,
      borderRadius: 6, padding: '8px 13px', pointerEvents: 'auto',
      userSelect: 'none',
    }}>
      {/* Header */}
      <div style={{ ...raj, fontSize: 8, letterSpacing: 4, color: 'rgba(79,195,247,0.35)', marginBottom: 6 }}>
        VOICE  CONTROL
      </div>

      <div style={{ display: 'flex', flexDirection: 'column', gap: 4 }}>
        <Row dot color={recColor} label={modeLabel} />
        <Row dot label='"JARVIS, [command]"' dim />
        <Row label={shortLabel} dim color={isPhone ? 'rgba(255,120,80,0.7)' : undefined} />
      </div>

      {/* Mode toggle */}
      <div style={{ display: 'flex', gap: 4, marginTop: 8 }}>
        <ModeBtn
          active={voiceMode === 'browser'}
          onClick={() => setVoiceMode('browser')}
          label='WEB STT'
        />
        <ModeBtn
          active={voiceMode === 'whisper'}
          onClick={() => setVoiceMode('whisper')}
          label='WHISPER'
        />
      </div>

      {/* Push-to-talk */}
      {voiceMode === 'whisper' && (
        <button
          onMouseDown={handlePttDown}
          onMouseUp={handlePttUp}
          onTouchStart={handlePttDown}
          onTouchEnd={handlePttUp}
          style={{
            marginTop: 8, width: '100%',
            background: pttHeld || recState === 'recording'
              ? 'rgba(244,68,68,0.25)'
              : 'rgba(79,195,247,0.08)',
            border: `1px solid ${pttHeld || recState === 'recording' ? 'rgba(244,68,68,0.6)' : 'rgba(79,195,247,0.2)'}`,
            borderRadius: 4, cursor: 'pointer', padding: '5px 0',
            color: pttHeld || recState === 'recording' ? '#f44' : 'rgba(79,195,247,0.7)',
            fontFamily: "'Share Tech Mono', monospace",
            fontSize: 9, letterSpacing: 2,
            transition: 'all 0.1s ease',
          }}
        >
          {recState === 'recording' ? '● REC' : recState === 'transcribing' ? '... PROCESSING' : 'HOLD TO TALK'}
        </button>
      )}
    </div>
  )
}

function Row({ dot, label, dim, color }) {
  return (
    <div style={{ display: 'flex', alignItems: 'center', gap: 6 }}>
      <div style={{
        width: 5, height: 5, borderRadius: '50%', flexShrink: 0,
        background: dot ? (color || (dim ? 'rgba(79,195,247,0.4)' : '#4fc3f7')) : 'rgba(79,195,247,0.15)',
      }} />
      <span style={{
        ...mono, fontSize: 9,
        color: color || (dim ? 'rgba(79,195,247,0.3)' : 'rgba(79,195,247,0.55)'),
        letterSpacing: 0.5,
      }}>{label}</span>
    </div>
  )
}

function ModeBtn({ active, onClick, label }) {
  return (
    <button
      onClick={onClick}
      style={{
        flex: 1,
        background: active ? 'rgba(79,195,247,0.18)' : 'rgba(79,195,247,0.04)',
        border: `1px solid ${active ? 'rgba(79,195,247,0.5)' : 'rgba(79,195,247,0.12)'}`,
        borderRadius: 3, cursor: 'pointer', padding: '3px 0',
        color: active ? '#4fc3f7' : 'rgba(79,195,247,0.3)',
        fontFamily: "'Share Tech Mono', monospace",
        fontSize: 8, letterSpacing: 1.5,
        transition: 'all 0.15s ease',
      }}
    >
      {label}
    </button>
  )
}
