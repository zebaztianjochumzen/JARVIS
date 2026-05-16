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
import NavBar           from './components/NavBar'
import WidgetShell      from './components/WidgetShell'
import ChatWidget       from './components/ChatWidget'
import SpotifyWidget    from './components/SpotifyWidget'
import CameraWidget     from './components/CameraWidget'
import { timestamp }    from './components/Chat'
import './App.css'

const GESTURE_COMMANDS = {
  swipe_right: 'Skip to the next Spotify track',
  swipe_left:  'Go back to the previous Spotify track',
  swipe_up:    'Turn the volume up',
  swipe_down:  'Turn the volume down',
}

const WS_URL = 'ws://localhost:8000/ws'

// Stable session ID — looks like a system process ID
const SESSION_ID = Math.floor(Math.random() * 9e7 + 1e7)

const INITIAL_MESSAGES = [
  { role: 'jarvis', content: 'All systems online. Standing by, Sir.', ts: '00:00:00' },
]

export default function App() {
  const [tab,         setTab]         = useState('home')
  const [thinking,    setThinking]    = useState(false)
  const [speaking,    setSpeaking]    = useState(false)
  const [route,        setRoute]        = useState(null)
  const [showLocation, setShowLocation] = useState(null)
  const [toolLogs,     setToolLogs]     = useState([])
  const [activeTimer,  setActiveTimer]  = useState(null)
  const [userSpeaking, setUserSpeaking] = useState(false)
  const [browserUrl,   setBrowserUrl]   = useState('')

  // ── Widget system ────────────────────────────────────────────────────────────
  const [widgetOpen, setWidgetOpen] = useState({ chat: false, spotify: false, camera: false })
  const [messages,   setMessages]   = useState(INITIAL_MESSAGES)

  function toggleWidget(name) {
    setWidgetOpen(prev => ({ ...prev, [name]: !prev[name] }))
  }

  function addSystemMessage(content) {
    setMessages(prev => [...prev, { role: 'system', content, ts: timestamp() }])
  }

  // ── WebSocket ─────────────────────────────────────────────────────────────
  const wsRef              = useRef(null)
  const gestureActiveRef   = useRef(false)
  const pendingResponseRef = useRef('')
  const audioRef           = useRef(null)
  const msgHandlerRef      = useRef(null)
  const streamingRef       = useRef(false)

  // Re-assigned every render so the live WS always calls the latest closure
  msgHandlerRef.current = (e) => {
    const data = JSON.parse(e.data)

    if (data.type === 'token') {
      pendingResponseRef.current += data.text
      if (!streamingRef.current) {
        // Start a new streaming JARVIS message
        streamingRef.current = true
        const ts = timestamp()
        setMessages(prev => [...prev, { role: 'jarvis', content: data.text, ts }])
      } else {
        // Update the last JARVIS message in-place as more tokens arrive
        setMessages(prev => {
          const copy = [...prev]
          const last = copy[copy.length - 1]
          if (last?.role === 'jarvis') {
            copy[copy.length - 1] = { ...last, content: pendingResponseRef.current }
          }
          return copy
        })
      }
      setThinking(false)
      setSpeaking(true)

    } else if (data.type === 'done') {
      streamingRef.current = false
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

    // ── Widget control via backend ──────────────────────────────────────────
    } else if (data.type === 'open_widget') {
      setWidgetOpen(prev => ({ ...prev, [data.widget]: true }))
      addSystemMessage(`Opening the ${data.widget} widget.`)
    } else if (data.type === 'close_widget') {
      setWidgetOpen(prev => ({ ...prev, [data.widget]: false }))
      addSystemMessage(`Closing the ${data.widget}.`)

    } else if (data.type === 'error') {
      setSpeaking(false)
      setThinking(false)
    }
  }

  useEffect(() => { connectWS() }, [])  // eslint-disable-line react-hooks/exhaustive-deps

  function speakViaApi(text) {
    if (!text) return
    if (audioRef.current) { audioRef.current.pause(); audioRef.current = null }
    fetch('http://localhost:8000/api/tts', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ text }),
    }).then(res => {
      if (!res.ok) return
      return res.blob()
    }).then(blob => {
      if (!blob) return
      const url   = URL.createObjectURL(blob)
      const audio = new Audio(url)
      audioRef.current   = audio
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
    ws.onopen    = () => onOpen?.()
    ws.onmessage = (e) => msgHandlerRef.current?.(e)
    ws.onclose   = () => { wsRef.current = null; setTimeout(() => connectWS(), 3000) }
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

  // ── Chat widget send ──────────────────────────────────────────────────────
  function handleChatSend(text) {
    if (!text) return
    if (audioRef.current) { audioRef.current.pause(); audioRef.current = null }
    setSpeaking(false)
    setThinking(false)
    gestureActiveRef.current   = false
    pendingResponseRef.current = ''
    setMessages(prev => [...prev, { role: 'user', content: text, ts: timestamp() }])
    handleSend(text)
  }

  const handleNotUnderstood = useCallback(() => {
    speakViaApi("I didn't get that, sir.")
  }, [])  // eslint-disable-line react-hooks/exhaustive-deps

  const handleInterrupt = useCallback(() => {
    if (audioRef.current) { audioRef.current.pause(); audioRef.current = null }
    setSpeaking(false)
    setThinking(false)
    gestureActiveRef.current   = false
    pendingResponseRef.current = ''
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

  // ── Panels (full-screen tabs) ─────────────────────────────────────────────
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
      <BootSequence />
      <div className="scanline" />
      <div className="hud-corner tl" /><div className="hud-corner tr" />
      <div className="hud-corner bl" /><div className="hud-corner br" />

      <GridBackground />
      <TickerBar />

      {/* ── Tab panels ── */}
      <div className="content-area" style={{ paddingBottom: 50 }}>
        {Object.entries(panels).map(([id, panel]) => (
          <div key={id} className={`panel-fill${tab === id ? '' : ' hidden'}`}
            style={{ display: 'flex', flexDirection: 'column' }}>
            {panel}
          </div>
        ))}
      </div>

      {/* ── Mini orb when not on home tab ── */}
      {tab !== 'home' && (
        <div className="orb-fixed">
          <Orb onClick={() => setTab('home')} thinking={thinking} speaking={speaking} />
        </div>
      )}

      {/* ── Floating widgets ──────────────────────────────────────────────── */}
      <WidgetShell
        title={`JARVIS_GID_${SESSION_ID}`}
        width={310}
        defaultX={80}
        defaultY={110}
        open={widgetOpen.chat}
        onClose={() => toggleWidget('chat')}
      >
        <ChatWidget
          messages={messages}
          thinking={thinking}
          onSend={handleChatSend}
        />
      </WidgetShell>

      <WidgetShell
        title="SPOTIFY_HUB"
        width={300}
        defaultX={420}
        defaultY={200}
        open={widgetOpen.spotify}
        onClose={() => toggleWidget('spotify')}
      >
        <SpotifyWidget />
      </WidgetShell>

      <WidgetShell
        title="CAM_FEED_01"
        width={280}
        defaultX={80}
        defaultY={60}
        open={widgetOpen.camera}
        onClose={() => toggleWidget('camera')}
      >
        <CameraWidget />
      </WidgetShell>

      {/* ── Bottom nav bar ── */}
      <NavBar
        active={tab}
        onChange={setTab}
        widgetOpen={widgetOpen}
        onToggleWidget={toggleWidget}
      />

      {/* ── Phase D overlays ── */}
      <SystemVitals />
      <Waveform userSpeaking={userSpeaking} speaking={speaking} />
      <ToolTheater logs={toolLogs} />
      <GestureOverlay onGesture={handleGesture} />
      <VoiceControl
        onCommand={handleVoiceCommand}
        onInterrupt={handleInterrupt}
        onNotUnderstood={handleNotUnderstood}
        onUserSpeaking={setUserSpeaking}
      />
    </div>
  )
}
