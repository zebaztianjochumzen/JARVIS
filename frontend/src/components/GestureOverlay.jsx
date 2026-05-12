import { useState, useEffect, useRef } from 'react'

const VISION_WS  = 'ws://localhost:8000/vision/ws/gestures'
const VISION_URL = 'http://localhost:8000/vision'

const mono = { fontFamily: "'Share Tech Mono', monospace" }
const raj  = { fontFamily: "'Rajdhani', sans-serif" }

const GESTURE_LABELS = {
  swipe_right: '→  SWIPE RIGHT',
  swipe_left:  '←  SWIPE LEFT',
  swipe_up:    '↑  SWIPE UP',
  swipe_down:  '↓  SWIPE DOWN',
}

export default function GestureOverlay({ onGesture }) {
  const [handVisible,  setHandVisible]  = useState(false)
  const [lastGesture,  setLastGesture]  = useState(null)
  const [flash,        setFlash]        = useState(false)
  const [connected,    setConnected]    = useState(false)
  const wsRef    = useRef(null)
  const flashRef = useRef(null)

  // Start vision server camera on mount so gesture detection is always live
  useEffect(() => {
    fetch(`${VISION_URL}/start`, { method: 'POST' }).catch(() => {})
  }, [])

  useEffect(() => {
    let reconnectTimer = null

    function connect() {
      const ws = new WebSocket(VISION_WS)

      ws.onopen = () => setConnected(true)

      ws.onmessage = (e) => {
        const data = JSON.parse(e.data)

        if (data.type === 'hand_status') {
          setHandVisible(data.visible)
        }

        if (data.type === 'gesture') {
          setLastGesture(data.gesture)
          // Flash animation
          setFlash(true)
          clearTimeout(flashRef.current)
          flashRef.current = setTimeout(() => setFlash(false), 900)
          // Bubble up to App
          onGesture?.(data.gesture)
        }
      }

      ws.onclose = () => {
        setConnected(false)
        setHandVisible(false)
        reconnectTimer = setTimeout(connect, 3000)
      }

      ws.onerror = () => ws.close()

      wsRef.current = ws
    }

    connect()
    return () => {
      clearTimeout(reconnectTimer)
      clearTimeout(flashRef.current)
      wsRef.current?.close()
    }
  }, [onGesture])

  if (!connected) return null  // hide widget entirely when vision server is offline

  const dotColor   = handVisible ? '#4fc3f7' : 'rgba(79,195,247,0.22)'
  const dotGlow    = handVisible ? '0 0 6px #4fc3f7' : 'none'
  const borderClr  = flash ? 'rgba(79,195,247,0.55)' : 'rgba(79,195,247,0.12)'

  return (
    <div style={{
      position: 'fixed',
      bottom: 90,
      left: 20,
      zIndex: 200,
      background: 'rgba(2,6,14,0.72)',
      backdropFilter: 'blur(8px)',
      border: `1px solid ${borderClr}`,
      borderRadius: 6,
      padding: '9px 14px',
      minWidth: 158,
      transition: 'border-color 0.2s',
      pointerEvents: 'none',
    }}>

      {/* Header */}
      <div style={{ ...raj, fontSize: 8, letterSpacing: 4, color: 'rgba(79,195,247,0.4)', marginBottom: 8 }}>
        HAND  CONTROL
      </div>

      {/* Status row */}
      <div style={{ display: 'flex', alignItems: 'center', gap: 7 }}>
        <div style={{
          width: 7, height: 7, borderRadius: '50%',
          background: dotColor,
          boxShadow: dotGlow,
          transition: 'background 0.3s, box-shadow 0.3s',
          flexShrink: 0,
        }} />
        <span style={{ ...mono, fontSize: 9, color: handVisible ? '#4fc3f7' : 'rgba(79,195,247,0.3)' }}>
          {handVisible ? 'HAND DETECTED' : 'NO HAND'}
        </span>
      </div>

      {/* Last gesture */}
      {lastGesture && (
        <div style={{
          marginTop: 8,
          ...mono,
          fontSize: 10,
          color: flash ? '#4fc3f7' : 'rgba(79,195,247,0.35)',
          letterSpacing: 1,
          transition: 'color 0.15s',
        }}>
          {GESTURE_LABELS[lastGesture] ?? lastGesture.toUpperCase()}
        </div>
      )}

      <style>{`
        @keyframes gesture-flash {
          0%   { opacity: 1; }
          100% { opacity: 0.3; }
        }
      `}</style>
    </div>
  )
}
