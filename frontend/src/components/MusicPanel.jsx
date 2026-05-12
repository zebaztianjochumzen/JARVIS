import { useState, useEffect, useRef, useCallback } from 'react'

const API  = 'http://localhost:8000'
const mono = { fontFamily: "'Share Tech Mono', monospace" }
const raj  = { fontFamily: "'Rajdhani', sans-serif" }

function fmt(ms) {
  const s = Math.floor(ms / 1000)
  return `${Math.floor(s / 60)}:${String(s % 60).padStart(2, '0')}`
}

// Seeded bar heights so they don't re-randomise on re-render
const BAR_HEIGHTS = Array.from({ length: 32 }, (_, i) => 8 + ((i * 17 + 7) % 24))

function VisualizerBars({ playing }) {
  return (
    <div style={{ display: 'flex', gap: 3, alignItems: 'flex-end', height: 36 }}>
      {BAR_HEIGHTS.map((h, i) => (
        <div key={i} style={{
          width: 3,
          borderRadius: 2,
          background: playing ? `rgba(79,195,247,${0.35 + (i % 3) * 0.15})` : 'rgba(79,195,247,0.12)',
          height: playing ? undefined : 4,
          animation: playing
            ? `vbar ${(0.55 + (i % 7) * 0.11).toFixed(2)}s ease-in-out ${(i * 0.03).toFixed(2)}s infinite alternate`
            : 'none',
          '--bar-h': `${h}px`,
        }} />
      ))}
    </div>
  )
}

function CtrlBtn({ onClick, children, large = false }) {
  const [hover, setHover] = useState(false)
  return (
    <button
      onClick={onClick}
      onMouseEnter={() => setHover(true)}
      onMouseLeave={() => setHover(false)}
      style={{
        background: 'none', border: 'none', cursor: 'pointer', padding: '8px 16px',
        ...mono,
        fontSize: large ? 22 : 14,
        color: hover ? '#e8f4ff' : 'rgba(79,195,247,0.7)',
        transition: 'color 0.15s',
        lineHeight: 1,
      }}
    >
      {children}
    </button>
  )
}

export default function MusicPanel() {
  const [track,    setTrack]    = useState(null)
  const [progress, setProgress] = useState(0)
  const [error,    setError]    = useState(null)
  const trackUriRef = useRef(null)
  const progressRef = useRef(0)

  const fetchNow = useCallback(async () => {
    try {
      const r    = await fetch(`${API}/api/spotify/now-playing`)
      const data = await r.json()
      if (data.error && !data.track) {
        setError(data.error)
        return
      }
      setError(null)
      setTrack(data.track)
      if (data.track) {
        // Only snap progress when the track changed or we've drifted > 3s
        if (data.track.track_uri !== trackUriRef.current ||
            Math.abs(data.track.progress_ms - progressRef.current) > 3000) {
          setProgress(data.track.progress_ms)
          progressRef.current  = data.track.progress_ms
          trackUriRef.current  = data.track.track_uri
        }
      }
    } catch {
      setError('Backend offline')
    }
  }, [])

  // Poll every 3 s
  useEffect(() => {
    fetchNow()
    const id = setInterval(fetchNow, 3000)
    return () => clearInterval(id)
  }, [fetchNow])

  // Tick progress locally while playing
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

  const send = async (action, query = '') => {
    await fetch(`${API}/api/spotify/control`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ action, query }),
    }).catch(() => {})
    setTimeout(fetchNow, 600)
  }

  const pct = track ? Math.min((progress / track.duration_ms) * 100, 100) : 0

  return (
    <div style={{
      height: '100%', display: 'flex', flexDirection: 'column',
      alignItems: 'center', justifyContent: 'center',
      background: 'rgba(2,6,14,0.95)', position: 'relative', overflow: 'hidden',
    }}>

      {/* Blurred album-art background */}
      {track?.art_url && (
        <div style={{
          position: 'absolute', inset: 0,
          backgroundImage:    `url(${track.art_url})`,
          backgroundSize:     'cover',
          backgroundPosition: 'center',
          filter:     'blur(40px) brightness(0.18)',
          transform:  'scale(1.1)',
        }} />
      )}

      {/* HUD label */}
      <div style={{
        position: 'absolute', top: 14, left: 20,
        ...raj, fontSize: 9, letterSpacing: 4,
        color: 'rgba(79,195,247,0.45)',
        zIndex: 1,
      }}>
        ♫  AUDIO STREAM · SPOTIFY
      </div>

      {/* ── Main card ── */}
      <div style={{
        position: 'relative', zIndex: 1,
        display: 'flex', flexDirection: 'column', alignItems: 'center',
        gap: 0, width: '100%', maxWidth: 420, padding: '0 32px',
      }}>

        {/* Album art */}
        <div style={{
          width: 200, height: 200, borderRadius: 10, overflow: 'hidden',
          border: '1px solid rgba(79,195,247,0.2)',
          boxShadow: '0 0 60px rgba(0,130,220,0.25)',
          background: 'rgba(10,20,40,0.8)',
          display: 'flex', alignItems: 'center', justifyContent: 'center',
          marginBottom: 28,
          flexShrink: 0,
        }}>
          {track?.art_url
            ? <img src={track.art_url} alt="album art"
                style={{ width: '100%', height: '100%', objectFit: 'cover', display: 'block' }} />
            : <span style={{ fontSize: 48, opacity: 0.18 }}>♫</span>
          }
        </div>

        {/* Track info */}
        {track ? (
          <div style={{ textAlign: 'center', width: '100%', marginBottom: 22 }}>
            <div style={{
              ...mono, fontSize: 16, color: '#e8f4ff',
              letterSpacing: 1, marginBottom: 6,
              whiteSpace: 'nowrap', overflow: 'hidden', textOverflow: 'ellipsis',
            }}>
              {track.track}
            </div>
            <div style={{
              ...raj, fontSize: 13, letterSpacing: 2,
              color: 'rgba(100,170,230,0.65)',
            }}>
              {track.artist}
            </div>
            <div style={{
              ...raj, fontSize: 11, letterSpacing: 2,
              color: 'rgba(80,130,190,0.4)', marginTop: 3,
            }}>
              {track.album}
            </div>
          </div>
        ) : (
          <div style={{ textAlign: 'center', marginBottom: 22 }}>
            <div style={{ ...mono, fontSize: 12, color: 'rgba(79,195,247,0.25)', letterSpacing: 2 }}>
              {error ? 'CONFIGURATION REQUIRED' : 'NOTHING PLAYING'}
            </div>
            {error && (
              <div style={{ ...raj, fontSize: 11, color: 'rgba(79,195,247,0.3)', marginTop: 8, lineHeight: 1.7 }}>
                Run <span style={{ color: 'rgba(79,195,247,0.6)' }}>python scripts/spotify_auth.py</span>
                <br />then add the tokens to <span style={{ color: 'rgba(79,195,247,0.6)' }}>.env</span>
              </div>
            )}
          </div>
        )}

        {/* Progress bar */}
        <div style={{ width: '100%', marginBottom: 6 }}>
          <div style={{
            width: '100%', height: 3, borderRadius: 2,
            background: 'rgba(255,255,255,0.08)',
            position: 'relative', cursor: 'pointer',
          }}>
            <div style={{
              height: '100%', borderRadius: 2,
              width: `${pct}%`,
              background: 'linear-gradient(to right, rgba(0,140,255,0.8), rgba(79,195,247,0.9))',
              transition: 'width 0.9s linear',
            }} />
          </div>
          <div style={{
            display: 'flex', justifyContent: 'space-between', marginTop: 5,
            ...mono, fontSize: 9, color: 'rgba(79,195,247,0.35)',
          }}>
            <span>{fmt(progress)}</span>
            <span>{track ? fmt(track.duration_ms) : '0:00'}</span>
          </div>
        </div>

        {/* Controls */}
        <div style={{ display: 'flex', alignItems: 'center', marginBottom: 28 }}>
          <CtrlBtn onClick={() => send('previous')}>⏮</CtrlBtn>
          <CtrlBtn onClick={() => send(track?.is_playing ? 'pause' : 'play')} large>
            {track?.is_playing ? '⏸' : '▶'}
          </CtrlBtn>
          <CtrlBtn onClick={() => send('next')}>⏭</CtrlBtn>
        </div>

        {/* Visualizer */}
        <VisualizerBars playing={track?.is_playing ?? false} />
      </div>

      <style>{`
        @keyframes vbar {
          from { height: 4px }
          to   { height: var(--bar-h) }
        }
      `}</style>
    </div>
  )
}
