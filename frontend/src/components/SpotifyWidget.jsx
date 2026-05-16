import { useState, useEffect, useRef, useCallback } from 'react'

const API  = 'http://localhost:8000'
const mono = { fontFamily: "'Share Tech Mono', monospace" }

function fmt(ms) {
  const s = Math.floor(ms / 1000)
  return `${Math.floor(s / 60)}:${String(s % 60).padStart(2, '0')}`
}

function Ctrl({ onClick, children, large }) {
  return (
    <button
      onClick={onClick}
      style={{
        background: 'none', border: 'none', cursor: 'pointer',
        color: 'rgba(0,212,255,0.65)',
        fontSize: large ? 15 : 11,
        padding: '2px 6px', lineHeight: 1,
        transition: 'color 0.1s',
      }}
      onMouseEnter={e => { e.currentTarget.style.color = '#e8f4ff' }}
      onMouseLeave={e => { e.currentTarget.style.color = 'rgba(0,212,255,0.65)' }}
    >
      {children}
    </button>
  )
}

export default function SpotifyWidget() {
  const [track,    setTrack]    = useState(null)
  const [progress, setProgress] = useState(0)
  const [error,    setError]    = useState(false)
  const trackUriRef = useRef(null)
  const progressRef = useRef(0)

  const fetchNow = useCallback(async () => {
    try {
      const r    = await fetch(`${API}/api/spotify/now-playing`)
      const data = await r.json()
      if (data.error && !data.track) { setError(true); return }
      setError(false)
      setTrack(data.track)
      if (data.track) {
        if (data.track.track_uri !== trackUriRef.current ||
            Math.abs(data.track.progress_ms - progressRef.current) > 3000) {
          setProgress(data.track.progress_ms)
          progressRef.current = data.track.progress_ms
          trackUriRef.current = data.track.track_uri
        }
      }
    } catch { setError(true) }
  }, [])

  useEffect(() => {
    fetchNow()
    const id = setInterval(fetchNow, 3000)
    return () => clearInterval(id)
  }, [fetchNow])

  // Local progress tick while playing
  useEffect(() => {
    if (!track?.is_playing) return
    const id = setInterval(() => {
      setProgress(p => {
        const next = Math.min(p + 1000, track.duration_ms)
        progressRef.current = next
        return next
      })
    }, 1000)
    return () => clearInterval(id)
  }, [track?.is_playing, track?.duration_ms])

  const send = async (action) => {
    await fetch(`${API}/api/spotify/control`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ action }),
    }).catch(() => {})
    setTimeout(fetchNow, 600)
  }

  const pct = track ? Math.min((progress / track.duration_ms) * 100, 100) : 0

  return (
    <div style={{ display: 'flex', padding: '10px 12px', gap: 12, alignItems: 'flex-start' }}>

      {/* Album art */}
      <div style={{
        width: 70, height: 70, borderRadius: 4,
        flexShrink: 0, overflow: 'hidden',
        background: 'rgba(0, 18, 45, 0.85)',
        border: '1px solid rgba(0,212,255,0.14)',
        position: 'relative',
        display: 'flex', alignItems: 'center', justifyContent: 'center',
      }}>
        {track?.art_url
          ? <img src={track.art_url} alt="" style={{ width: '100%', height: '100%', objectFit: 'cover' }} />
          : <span style={{ fontSize: 22, opacity: 0.18 }}>♫</span>
        }
        <div style={{
          position: 'absolute', bottom: 3, left: 3,
          ...mono, fontSize: 7, letterSpacing: 1,
          background: 'rgba(2,8,22,0.85)',
          color: track?.is_playing ? '#4ade80' : 'rgba(0,212,255,0.45)',
          padding: '1px 4px', borderRadius: 2,
        }}>
          {track?.is_playing ? 'LIVE' : 'IDLE'}
        </div>
      </div>

      {/* Info + controls */}
      <div style={{ flex: 1, minWidth: 0 }}>
        {error ? (
          <div style={{ ...mono, fontSize: 9, color: 'rgba(0,212,255,0.3)', lineHeight: 2 }}>
            SPOTIFY NOT CONFIGURED<br />
            <span style={{ color: 'rgba(0,212,255,0.5)' }}>python scripts/spotify_auth.py</span>
          </div>
        ) : track ? (
          <>
            <div style={{ ...mono, fontSize: 11, color: '#e8f4ff', overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap' }}>
              {track.track}
            </div>
            <div style={{ ...mono, fontSize: 10, color: 'rgba(0,212,255,0.75)', overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap' }}>
              {track.artist}
            </div>
            <div style={{ ...mono, fontSize: 9, color: 'rgba(100,135,175,0.4)', overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap', marginBottom: 7 }}>
              {track.album}
            </div>
          </>
        ) : (
          <div style={{ ...mono, fontSize: 9, color: 'rgba(0,212,255,0.3)', marginBottom: 7 }}>
            NOTHING PLAYING
          </div>
        )}

        {/* Progress bar */}
        <div style={{ marginBottom: 6 }}>
          <div style={{
            width: '100%', height: 2, borderRadius: 1,
            background: 'rgba(255,255,255,0.07)',
          }}>
            <div style={{
              height: '100%', borderRadius: 1,
              width: `${pct}%`,
              background: 'linear-gradient(to right, rgba(0,140,255,0.8), #00d4ff)',
              transition: 'width 0.9s linear',
            }} />
          </div>
          <div style={{
            display: 'flex', justifyContent: 'space-between', marginTop: 3,
            ...mono, fontSize: 8, color: 'rgba(0,212,255,0.3)',
          }}>
            <span>{fmt(progress)}</span>
            <span>{track ? fmt(track.duration_ms) : '0:00'}</span>
          </div>
        </div>

        {/* Controls */}
        <div style={{ display: 'flex', alignItems: 'center', marginLeft: -6 }}>
          <Ctrl onClick={() => send('previous')}>⏮</Ctrl>
          <Ctrl onClick={() => send(track?.is_playing ? 'pause' : 'play')} large>
            {track?.is_playing ? '⏸' : '▶'}
          </Ctrl>
          <Ctrl onClick={() => send('next')}>⏭</Ctrl>
          <Ctrl onClick={() => send('repeat')}>🔁</Ctrl>
        </div>
      </div>
    </div>
  )
}
