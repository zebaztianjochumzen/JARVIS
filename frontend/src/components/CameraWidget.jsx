import { useState, useEffect, useRef } from 'react'

const VISION_URL = 'http://localhost:8000/vision'
const mono       = { fontFamily: "'Share Tech Mono', monospace" }

export default function CameraWidget() {
  const [connected, setConnected] = useState(false)
  const [streamKey, setStreamKey] = useState(0)
  const pollRef = useRef(null)

  useEffect(() => {
    fetch(`${VISION_URL}/start`, { method: 'POST' }).catch(() => {})

    const poll = async () => {
      try {
        const r  = await fetch(`${VISION_URL}/health`, { signal: AbortSignal.timeout(2000) })
        const ok = r.ok
        setConnected(prev => {
          if (!prev && ok) setStreamKey(k => k + 1)
          return ok
        })
      } catch {
        setConnected(false)
      }
    }

    poll()
    pollRef.current = setInterval(poll, 3000)

    return () => {
      clearInterval(pollRef.current)
      fetch(`${VISION_URL}/stop`, { method: 'POST' }).catch(() => {})
    }
  }, [])

  return (
    <div style={{ position: 'relative', aspectRatio: '16/9', background: '#020b18', overflow: 'hidden' }}>
      {connected ? (
        <img
          key={streamKey}
          src={`${VISION_URL}/stream`}
          alt="camera"
          style={{ width: '100%', height: '100%', objectFit: 'cover', display: 'block' }}
        />
      ) : (
        <div style={{
          height: '100%', display: 'flex', flexDirection: 'column',
          alignItems: 'center', justifyContent: 'center', gap: 5,
          minHeight: 120,
        }}>
          <div style={{ ...mono, fontSize: 10, color: 'rgba(248,113,113,0.55)', letterSpacing: 2 }}>NO FEED</div>
          <div style={{ ...mono, fontSize: 9, color: 'rgba(0,212,255,0.25)', letterSpacing: 1 }}>CAMERA OFFLINE</div>
        </div>
      )}

      {/* HUD corner brackets */}
      {[
        { top: 4, left: 4,   borderTop: '1px solid rgba(0,212,255,0.28)', borderLeft: '1px solid rgba(0,212,255,0.28)'   },
        { top: 4, right: 4,  borderTop: '1px solid rgba(0,212,255,0.28)', borderRight: '1px solid rgba(0,212,255,0.28)'  },
        { bottom: 4, left: 4,  borderBottom: '1px solid rgba(0,212,255,0.28)', borderLeft:  '1px solid rgba(0,212,255,0.28)' },
        { bottom: 4, right: 4, borderBottom: '1px solid rgba(0,212,255,0.28)', borderRight: '1px solid rgba(0,212,255,0.28)' },
      ].map((s, i) => (
        <div key={i} style={{ position: 'absolute', width: 12, height: 12, pointerEvents: 'none', ...s }} />
      ))}

      {connected && (
        <div style={{
          position: 'absolute', top: 6, left: 8,
          ...mono, fontSize: 8, letterSpacing: 2,
          color: '#4ade80', textShadow: '0 0 6px #4ade80',
        }}>
          LIVE
        </div>
      )}
    </div>
  )
}
