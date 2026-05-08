import { useState, useRef } from 'react'
import GridBackground from './components/GridBackground'
import Orb from './components/Orb'
import Clock from './components/Clock'
import Chat from './components/Chat'
import StocksPanel from './components/StocksPanel'
import NavBar from './components/NavBar'
import './App.css'

const WS_URL = 'ws://localhost:8000/ws'

export default function App() {
  const [active, setActive] = useState(false)   // has orb been clicked
  const [tab, setTab] = useState('chat')         // active panel
  const [messages, setMessages] = useState([])
  const [thinking, setThinking] = useState(false)
  const wsRef = useRef(null)

  function connectWS(onOpen) {
    if (wsRef.current?.readyState === WebSocket.OPEN) { onOpen?.(); return }
    const ws = new WebSocket(WS_URL)
    ws.onopen = () => onOpen?.()
    ws.onmessage = (e) => {
      const data = JSON.parse(e.data)
      if (data.type === 'token') {
        setMessages(prev => {
          const last = prev[prev.length - 1]
          if (last?.role === 'assistant' && last.streaming) {
            return [...prev.slice(0, -1), { ...last, content: last.content + data.text }]
          }
          return [...prev, { role: 'assistant', content: data.text, streaming: true }]
        })
      } else if (data.type === 'done') {
        setMessages(prev => {
          const last = prev[prev.length - 1]
          if (last?.streaming) return [...prev.slice(0, -1), { role: 'assistant', content: last.content }]
          return prev
        })
        setThinking(false)
      } else if (data.type === 'error') {
        setMessages(prev => [...prev, { role: 'assistant', content: `[Error: ${data.message}]` }])
        setThinking(false)
      }
    }
    ws.onclose = () => { wsRef.current = null }
    wsRef.current = ws
  }

  function handleOrbClick() {
    if (!active) {
      setActive(true)
      connectWS()
    }
  }

  function handleSend(text) {
    const send = () => {
      setMessages(prev => [...prev, { role: 'user', content: text }])
      setThinking(true)
      wsRef.current.send(JSON.stringify({ message: text }))
    }
    if (!wsRef.current || wsRef.current.readyState !== WebSocket.OPEN) {
      connectWS(send)
    } else {
      send()
    }
  }

  function handleTabChange(newTab) {
    if (!active) setActive(true)
    setTab(newTab)
  }

  return (
    <div className="app">
      <GridBackground />

      {/* Idle: orb + clock centred, no nav yet */}
      <div className={`idle-view${active ? ' idle-hidden' : ''}`}>
        <Orb onClick={handleOrbClick} thinking={false} />
        <Clock />
      </div>

      {/* Active: mini orb + panels + nav */}
      <div className={`active-view${active ? ' active-visible' : ''}`} style={{ paddingBottom: 52 }}>
        <div className="active-orb">
          <Orb onClick={() => {}} thinking={thinking} />
        </div>

        <div className="panel-area">
          <div style={{ display: tab === 'chat' ? 'flex' : 'none', flexDirection: 'column', height: '100%' }}>
            <Chat messages={messages} onSend={handleSend} thinking={thinking} />
          </div>
          <div style={{ display: tab === 'stocks' ? 'block' : 'none', height: '100%' }}>
            <StocksPanel />
          </div>
        </div>
      </div>

      {active && <NavBar active={tab} onChange={handleTabChange} />}
    </div>
  )
}
