import { useState, useEffect, useRef } from 'react'

const VISION_URL = 'http://localhost:8000/vision'

const mono  = { fontFamily: "'Share Tech Mono', monospace" }
const raj   = { fontFamily: "'Rajdhani', sans-serif" }

export default function CameraPanel({ visible }) {
  const [detections, setDetections] = useState([])
  const [connected,  setConnected]  = useState(false)
  const [streamKey,  setStreamKey]  = useState(0)
  const pollRef = useRef(null)

  useEffect(() => {
    if (!visible) {
      fetch(`${VISION_URL}/stop`, { method: 'POST' }).catch(() => {})
      setDetections([])
      setConnected(false)
      return
    }

    fetch(`${VISION_URL}/start`, { method: 'POST' }).catch(() => {})

    const poll = async () => {
      try {
        const r = await fetch(`${VISION_URL}/health`, {
          signal: AbortSignal.timeout(2000),
        })
        const ok = r.ok
        setConnected(prev => {
          if (!prev && ok) setStreamKey(k => k + 1)
          return ok
        })
        if (ok) {
          const d    = await fetch(`${VISION_URL}/detections`)
          const json = await d.json()
          setDetections(json.detections || [])
        }
      } catch {
        setConnected(false)
      }
    }

    poll()
    pollRef.current = setInterval(poll, 2000)
    return () => clearInterval(pollRef.current)
  }, [visible])

  return (
    <div style={{ height: '100%', position: 'relative', overflow: 'hidden', background: 'rgba(2,6,14,0.95)' }}>

      {connected ? (
        <>
          {/* ── Full-bleed camera feed ── */}
          <img
            key={streamKey}
            src={`${VISION_URL}/stream`}
            alt="camera feed"
            style={{ width: '100%', height: '100%', objectFit: 'cover', display: 'block' }}
          />

          {/* ── Top-left label ── */}
          <div style={{
            position: 'absolute', top: 12, left: 14,
            ...raj, fontSize: 9, letterSpacing: 4,
            color: 'rgba(79,195,247,0.55)',
            pointerEvents: 'none',
          }}>
            VISUAL FEED  ·  ACTIVE
          </div>

          {/* ── Bottom-left model tag ── */}
          <div style={{
            position: 'absolute', bottom: 14, left: 14,
            ...mono, fontSize: 9, color: 'rgba(79,195,247,0.3)',
            pointerEvents: 'none',
          }}>
            YOLOv8-nano
          </div>

          {/* ── HUD corner brackets ── */}
          {[
            { top: 8,    left: 8,   borderTop: '1px solid rgba(79,195,247,0.35)', borderLeft:  '1px solid rgba(79,195,247,0.35)' },
            { top: 8,    right: 8,  borderTop: '1px solid rgba(79,195,247,0.35)', borderRight: '1px solid rgba(79,195,247,0.35)' },
            { bottom: 8, left: 8,   borderBottom: '1px solid rgba(79,195,247,0.35)', borderLeft:  '1px solid rgba(79,195,247,0.35)' },
            { bottom: 8, right: 8,  borderBottom: '1px solid rgba(79,195,247,0.35)', borderRight: '1px solid rgba(79,195,247,0.35)' },
          ].map((s, i) => (
            <div key={i} style={{ position: 'absolute', width: 20, height: 20, pointerEvents: 'none', ...s }} />
          ))}

          {/* ── Detection overlay (top-right, transparent) ── */}
          {detections.length > 0 && (
            <div style={{
              position: 'absolute', top: 12, right: 14,
              background: 'rgba(2,6,14,0.52)',
              backdropFilter: 'blur(6px)',
              border: '1px solid rgba(79,195,247,0.15)',
              borderRadius: 6,
              padding: '10px 14px',
              minWidth: 150,
              pointerEvents: 'none',
            }}>
              <div style={{
                ...raj, fontSize: 8, letterSpacing: 4,
                color: 'rgba(79,195,247,0.45)',
                marginBottom: 10,
              }}>
                DETECTIONS
              </div>

              {detections.map((d, i) => (
                <div key={i} style={{
                  marginBottom: i < detections.length - 1 ? 8 : 0,
                  paddingLeft: 8,
                  borderLeft: '1px solid rgba(79,195,247,0.2)',
                }}>
                  <div style={{ ...mono, fontSize: 10, color: '#80c8ff' }}>
                    [{d.label.toUpperCase()}]
                  </div>
                  <div style={{ ...mono, fontSize: 9, color: 'rgba(100,160,220,0.45)', marginTop: 1 }}>
                    {Math.round(d.confidence * 100)}%
                  </div>
                </div>
              ))}

              <div style={{
                marginTop: 10,
                ...raj, fontSize: 8, letterSpacing: 3,
                color: 'rgba(79,195,247,0.25)',
              }}>
                {detections.length} OBJECT{detections.length !== 1 ? 'S' : ''}
              </div>
            </div>
          )}
        </>
      ) : (
        /* ── Offline state ── */
        <div style={{
          height: '100%', display: 'flex', flexDirection: 'column',
          alignItems: 'center', justifyContent: 'center', gap: 16,
        }}>
          <div style={{ ...mono, fontSize: 12, letterSpacing: 2, color: 'rgba(79,195,247,0.3)' }}>
            ◉  VISION SERVER OFFLINE
          </div>
          <div style={{ ...mono, fontSize: 10, color: 'rgba(100,140,180,0.35)', lineHeight: 2.2, textAlign: 'center' }}>
            Restart the backend — vision loads automatically.<br />
            <span style={{ color: 'rgba(79,195,247,0.55)' }}>
              uvicorn api.main:app --reload --port 8000
            </span>
          </div>
        </div>
      )}
    </div>
  )
}
