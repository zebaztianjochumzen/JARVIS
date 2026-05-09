import { useState, useRef } from 'react'
import GridBackground   from './components/GridBackground'
import Orb              from './components/Orb'
import Clock            from './components/Clock'
import Chat, { timestamp } from './components/Chat'
import BriefingPanel    from './components/BriefingPanel'
import StocksPanel      from './components/StocksPanel'
import NewsPanel        from './components/NewsPanel'
import MapPanel         from './components/MapPanel'
import TerminalPanel    from './components/TerminalPanel'
import MusicPanel       from './components/MusicPanel'
import SettingsPanel    from './components/SettingsPanel'
import CameraPanel     from './components/CameraPanel'
import NavBar           from './components/NavBar'
import TickerBar        from './components/TickerBar'
import './App.css'

const WS_URL = 'ws://localhost:8000/ws'

export default function App() {
  const [active,   setActive]   = useState(false)
  const [tab,      setTab]      = useState('home')
  const [messages, setMessages] = useState([])
  const [thinking, setThinking] = useState(false)
  const [speaking, setSpeaking] = useState(false)
  const [route,        setRoute]        = useState(null)
  const [showLocation, setShowLocation] = useState(null)
  const [toolLogs,     setToolLogs]     = useState([])
  const wsRef = useRef(null)

  function connectWS(onOpen) {
    if (wsRef.current?.readyState === WebSocket.OPEN) { onOpen?.(); return }
    const ws = new WebSocket(WS_URL)
    ws.onopen = () => onOpen?.()
    ws.onmessage = (e) => {
      const data = JSON.parse(e.data)
      if (data.type === 'token') {
        setThinking(false)
        setSpeaking(true)
        setMessages(prev => {
          const last = prev[prev.length - 1]
          if (last?.role === 'assistant' && last.streaming) {
            return [...prev.slice(0, -1), { ...last, content: last.content + data.text }]
          }
          return [...prev, { role: 'assistant', content: data.text, streaming: true, ts: timestamp() }]
        })
      } else if (data.type === 'done') {
        setMessages(prev => {
          const last = prev[prev.length - 1]
          if (last?.streaming) return [...prev.slice(0, -1), { role: 'assistant', content: last.content, ts: last.ts }]
          return prev
        })
        setSpeaking(false)
        setThinking(false)
      } else if (data.type === 'route') {
        setRoute(data)
        setTab('map')
      } else if (data.type === 'show_location') {
        setShowLocation(data)
        setTab('map')
      } else if (data.type === 'switch_tab') {
        setTab(data.tab)
      } else if (data.type === 'tool_log') {
        setToolLogs(prev => [...prev, data])
      } else if (data.type === 'error') {
        setMessages(prev => [...prev, { role: 'assistant', content: `[Error: ${data.message}]`, ts: timestamp() }])
        setSpeaking(false)
        setThinking(false)
      }
    }
    ws.onclose = () => { wsRef.current = null }
    wsRef.current = ws
  }

  function handleOrbClick() {
    if (!active) { setActive(true); connectWS() }
    else setTab('home')
  }

  function handleSend(text) {
    const send = () => {
      setMessages(prev => [...prev, { role: 'user', content: text, ts: timestamp() }])
      setThinking(true)
      setSpeaking(false)
      wsRef.current.send(JSON.stringify({ message: text }))
    }
    if (!wsRef.current || wsRef.current.readyState !== WebSocket.OPEN) connectWS(send)
    else send()
  }

  function handleTabChange(t) {
    if (!active) setActive(true)
    setTab(t)
    if (!wsRef.current || wsRef.current.readyState !== WebSocket.OPEN) connectWS()
  }

  const panels = {
    home:     (
      <div style={{ display: 'flex', height: '100%' }}>
        <div style={{ flex: '0 0 62%', minWidth: 0, borderRight: '1px solid rgba(0,100,200,0.12)' }}>
          <Chat messages={messages} onSend={handleSend} thinking={thinking} />
        </div>
        <div style={{ flex: 1, minWidth: 0 }}>
          <BriefingPanel />
        </div>
      </div>
    ),
    stocks:   <StocksPanel />,
    news:     <NewsPanel />,
    map:      <MapPanel visible={tab === 'map'} route={route} showLocation={showLocation} />,
    terminal: <TerminalPanel logs={toolLogs} />,
    music:    <MusicPanel />,
    camera:   <CameraPanel visible={tab === 'camera'} />,
    settings: <SettingsPanel />,
  }

  return (
    <div className="app">
      {/* HUD chrome */}
      <div className="scanline" />
      <div className="hud-corner tl" /><div className="hud-corner tr" />
      <div className="hud-corner bl" /><div className="hud-corner br" />

      <GridBackground />

      {/* Idle */}
      <div className={`idle-view${active ? ' idle-hidden' : ''}`}>
        <Orb onClick={handleOrbClick} thinking={false} speaking={false} />
        <Clock />
      </div>

      {/* Active */}
      <div className={`active-view${active ? ' active-visible' : ''}`}>
        <TickerBar />

        <div className="content-area">
          {Object.entries(panels).map(([id, panel]) => (
            <div key={id} className={`panel-fill${tab === id ? '' : ' hidden'}`}
              style={{ display: 'flex', flexDirection: 'column' }}>
              {panel}
            </div>
          ))}
        </div>

        {/* Orb fixed bottom-right — always visible, click to go home */}
        <div className="orb-fixed">
          <Orb onClick={handleOrbClick} thinking={thinking} speaking={speaking} />
        </div>
      </div>

      {active && <NavBar active={tab} onChange={handleTabChange} />}
    </div>
  )
}
