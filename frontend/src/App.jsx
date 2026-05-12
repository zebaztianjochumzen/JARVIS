import { useState, useRef, useCallback, useEffect } from 'react'
import GridBackground   from './components/GridBackground'
import Orb              from './components/Orb'
import Clock            from './components/Clock'
import BriefingPanel    from './components/BriefingPanel'
import StocksPanel      from './components/StocksPanel'
import NewsPanel        from './components/NewsPanel'
import MapPanel         from './components/MapPanel'
import TerminalPanel    from './components/TerminalPanel'
import MusicPanel       from './components/MusicPanel'
import SettingsPanel    from './components/SettingsPanel'
import CameraPanel      from './components/CameraPanel'
import GestureOverlay   from './components/GestureOverlay'
import VoiceControl     from './components/VoiceControl'
import TickerBar        from './components/TickerBar'
import TimerRing        from './components/TimerRing'
import BrowserPanel     from './components/BrowserPanel'
import CalendarPanel    from './components/CalendarPanel'
import BootSequence     from './components/BootSequence'
import SystemVitals     from './components/SystemVitals'
import Waveform         from './components/Waveform'
import ToolTheater      from './components/ToolTheater'
import './App.css'

const GESTURE_COMMANDS = {
  swipe_right: 'Skip to the next Spotify track',
  swipe_left:  'Go back to the previous Spotify track',
  swipe_up:    'Turn the volume up',
  swipe_down:  'Turn the volume down',
}

const WS_URL = 'ws://localhost:8000/ws'

export default function App() {
  const [tab,      setTab]      = useState('home')
  const [thinking, setThinking] = useState(false)
  const [speaking, setSpeaking] = useState(false)
  const [route,        setRoute]        = useState(null)
  const [showLocation, setShowLocation] = useState(null)
  const [toolLogs,     setToolLogs]     = useState([])
  const [activeTimer,   setActiveTimer]  = useState(null)
  const [userSpeaking,  setUserSpeaking] = useState(false)
  const [browserUrl,    setBrowserUrl]   = useState('')
  const wsRef              = useRef(null)
  const gestureActiveRef   = useRef(false)
  const pendingResponseRef = useRef('')
  const audioRef           = useRef(null)
  const msgHandlerRef      = useRef(null)

  // Re-assigned every render so the live WS always calls the latest closure
  msgHandlerRef.current = (e) => {
    const data = JSON.parse(e.data)
    if (data.type === 'token') {
      pendingResponseRef.current += data.text
      setThinking(false)
      setSpeaking(true)
    } else if (data.type === 'done') {
      if (gestureActiveRef.current && pendingResponseRef.current) {
        const text = pendingResponseRef.current.replace(/[*_`#>]/g, '').trim()
        speakViaApi(text)
      }
      gestureActiveRef.current   = false
      pendingResponseRef.current = ''
      setSpeaking(false)
      setThinking(false)
    } else if (data.type === 'route') {
      setRoute(data)
      setTab('map')
    } else if (data.type === 'show_location') {
      setShowLocation(data)
      setTab('map')
    } else if (data.type === 'timer_set') {
      setActiveTimer({
        duration: data.duration_seconds,
        label:    data.label || 'Timer',
        endsAt:   Date.now() + data.duration_seconds * 1000,
      })
      setTab('home')
    } else if (data.type === 'show_browser') {
      setBrowserUrl(data.url)
      setTab('browser')
    } else if (data.type === 'switch_tab') {
      setTab(data.tab)
    } else if (data.type === 'tool_log') {
      setToolLogs(prev => [...prev, data])
    } else if (data.type === 'error') {
      setSpeaking(false)
      setThinking(false)
    }
  }

  useEffect(() => { connectWS() }, [])  // eslint-disable-line react-hooks/exhaustive-deps

  function speakViaApi(text) {
    if (!text) return
    if (audioRef.current) {
      audioRef.current.pause()
      audioRef.current = null
    }
    fetch('http://localhost:8000/api/tts', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ text }),
    }).then(res => {
      if (!res.ok) return
      return res.blob()
    }).then(blob => {
      if (!blob) return
      const url = URL.createObjectURL(blob)
      const audio = new Audio(url)
      audioRef.current = audio
      audio.onended = () => { URL.revokeObjectURL(url); audioRef.current = null }
      audio.play()
    }).catch(() => {})
  }

  function connectWS(onOpen) {
    if (wsRef.current?.readyState === WebSocket.OPEN) { onOpen?.(); return }
    if (wsRef.current?.readyState === WebSocket.CONNECTING) {
      if (onOpen) wsRef.current.addEventListener('open', onOpen, { once: true })
      return
    }
    const ws = new WebSocket(WS_URL)
    ws.onopen = () => onOpen?.()
    ws.onmessage = (e) => msgHandlerRef.current?.(e)
    ws.onclose = () => {
      wsRef.current = null
      setTimeout(() => connectWS(), 3000)  // auto-reconnect
    }
    wsRef.current = ws
  }

  function handleSend(text) {
    const send = () => {
      setThinking(true)
      setSpeaking(false)
      wsRef.current.send(JSON.stringify({ message: text }))
    }
    if (!wsRef.current || wsRef.current.readyState !== WebSocket.OPEN) connectWS(send)
    else send()
  }

  const handleNotUnderstood = useCallback(() => {
    speakViaApi("I didn't get that, sir.")
  }, [])  // eslint-disable-line react-hooks/exhaustive-deps

  const handleInterrupt = useCallback(() => {
    if (audioRef.current) {
      audioRef.current.pause()
      audioRef.current = null
    }
    setSpeaking(false)
    setThinking(false)
    gestureActiveRef.current   = false
    pendingResponseRef.current = ''
    // Tell the backend to stop streaming immediately
    if (wsRef.current?.readyState === WebSocket.OPEN) {
      wsRef.current.send(JSON.stringify({ type: 'interrupt' }))
    }
  }, [])

  const handleVoiceCommand = useCallback((text) => {
    if (!text) return
    if (audioRef.current) { audioRef.current.pause(); audioRef.current = null }
    setSpeaking(false)
    setThinking(false)
    gestureActiveRef.current   = true
    pendingResponseRef.current = ''
    handleSend(text)
  }, [])  // eslint-disable-line react-hooks/exhaustive-deps

  const handleGesture = useCallback((gesture) => {
    const cmd = GESTURE_COMMANDS[gesture]
    if (!cmd) return
    gestureActiveRef.current   = true
    pendingResponseRef.current = ''
    handleSend(cmd)
  }, [])  // eslint-disable-line react-hooks/exhaustive-deps

  const panels = {
    home: (
      <div style={{ display: 'flex', flexDirection: 'column', alignItems: 'center', justifyContent: 'center', height: '100%', gap: 32 }}>
        <div style={{ position: 'relative' }}>
          <Orb thinking={thinking} speaking={speaking} userSpeaking={userSpeaking} />
          {activeTimer && (
            <TimerRing
              duration={activeTimer.duration}
              endsAt={activeTimer.endsAt}
              label={activeTimer.label}
              onComplete={() => { speakViaApi('Timer complete, sir.'); setActiveTimer(null) }}
            />
          )}
        </div>
        <Clock />
      </div>
    ),
    briefing: <BriefingPanel />,
    stocks:   <StocksPanel />,
    news:     <NewsPanel />,
    map:      <MapPanel visible={tab === 'map'} route={route} showLocation={showLocation} />,
    terminal: <TerminalPanel logs={toolLogs} />,
    calendar: <CalendarPanel />,
    browser:  <BrowserPanel url={browserUrl} />,
    music:    <MusicPanel />,
    camera:   <CameraPanel visible={tab === 'camera'} />,
    settings: <SettingsPanel />,
  }

  return (
    <div className="app">
      {/* ── Cinematic boot sequence (Phase D) ── */}
      <BootSequence />

      <div className="scanline" />
      <div className="hud-corner tl" /><div className="hud-corner tr" />
      <div className="hud-corner bl" /><div className="hud-corner br" />

      <GridBackground />
      <TickerBar />

      <div className="content-area">
        {Object.entries(panels).map(([id, panel]) => (
          <div key={id} className={`panel-fill${tab === id ? '' : ' hidden'}`}
            style={{ display: 'flex', flexDirection: 'column' }}>
            {panel}
          </div>
        ))}
      </div>

      {tab !== 'home' && (
        <div className="orb-fixed">
          <Orb onClick={() => setTab('home')} thinking={thinking} speaking={speaking} />
        </div>
      )}

      {/* ── Phase D overlays ── */}
      <SystemVitals />
      <Waveform userSpeaking={userSpeaking} speaking={speaking} />
      <ToolTheater logs={toolLogs} />

      <GestureOverlay onGesture={handleGesture} />
      <VoiceControl   onCommand={handleVoiceCommand} onInterrupt={handleInterrupt} onNotUnderstood={handleNotUnderstood} onUserSpeaking={setUserSpeaking} />
    </div>
  )
}
