import { useState, useRef, useEffect } from 'react'

const raj  = { fontFamily: "'Rajdhani', sans-serif" }
const mono = { fontFamily: "'Share Tech Mono', monospace" }

const PROXY = (url) => `http://localhost:8000/api/browse?url=${encodeURIComponent(url)}`

function resolveUrl(raw) {
  if (!raw) return ''
  // YouTube video → embed player
  const yt = raw.match(/(?:youtube\.com\/watch\?v=|youtu\.be\/)([a-zA-Z0-9_-]{11})/)
  if (yt) return `https://www.youtube.com/embed/${yt[1]}?autoplay=0`
  // All other URLs → proxy
  return PROXY(raw)
}

export default function BrowserPanel({ url }) {
  const [currentUrl,  setCurrentUrl]  = useState(url || '')
  const [inputVal,    setInputVal]    = useState(url || '')
  const [iframeSrc,   setIframeSrc]   = useState(url ? resolveUrl(url) : '')
  const [loading,     setLoading]     = useState(false)
  const iframeRef = useRef(null)

  // External URL change (from voice command)
  useEffect(() => {
    if (url && url !== currentUrl) {
      loadUrl(url)
    }
  }, [url])  // eslint-disable-line react-hooks/exhaustive-deps

  function loadUrl(raw) {
    const trimmed = raw.trim()
    if (!trimmed) return
    setCurrentUrl(trimmed)
    setInputVal(trimmed)
    setLoading(true)
    setIframeSrc(resolveUrl(trimmed))
  }

  function handleKey(e) {
    if (e.key === 'Enter') loadUrl(inputVal)
  }

  function handleLoad() {
    setLoading(false)
  }

  const btnStyle = {
    background: 'none',
    border: '1px solid rgba(79,195,247,0.25)',
    borderRadius: 4,
    color: 'rgba(79,195,247,0.7)',
    cursor: 'pointer',
    padding: '3px 10px',
    ...mono, fontSize: 9, letterSpacing: 1,
    transition: 'border-color 0.2s, color 0.2s',
  }

  return (
    <div style={{ display: 'flex', flexDirection: 'column', height: '100%' }}>

      {/* ── URL bar ── */}
      <div style={{
        display: 'flex', alignItems: 'center', gap: 8,
        padding: '8px 16px',
        background: 'rgba(2,6,14,0.85)',
        borderBottom: '1px solid rgba(79,195,247,0.12)',
        flexShrink: 0,
      }}>
        <div style={{ ...raj, fontSize: 8, letterSpacing: 4, color: 'rgba(79,195,247,0.35)', whiteSpace: 'nowrap' }}>
          JARVIS  BROWSER
        </div>

        {loading && (
          <div style={{ width: 6, height: 6, borderRadius: '50%', background: '#4fc3f7', flexShrink: 0,
            animation: 'pulse 0.8s ease-in-out infinite' }} />
        )}

        <input
          value={inputVal}
          onChange={e => setInputVal(e.target.value)}
          onKeyDown={handleKey}
          placeholder="Enter URL or say 'Jarvis open youtube'"
          style={{
            flex: 1,
            background: 'rgba(255,255,255,0.04)',
            border: '1px solid rgba(79,195,247,0.18)',
            borderRadius: 4,
            padding: '5px 12px',
            color: '#a8d8f0',
            ...mono, fontSize: 11,
            outline: 'none',
          }}
        />

        <button style={btnStyle} onClick={() => loadUrl(inputVal)}>
          GO
        </button>
        <button style={btnStyle} onClick={() => iframeRef.current && (iframeRef.current.src = iframeRef.current.src)}>
          ↺
        </button>
        <button
          style={{ ...btnStyle, borderColor: 'rgba(79,195,247,0.18)' }}
          onClick={() => currentUrl && window.open(currentUrl, '_blank')}
        >
          ↗ EXTERNAL
        </button>
      </div>

      {/* ── Content ── */}
      {iframeSrc ? (
        <iframe
          ref={iframeRef}
          src={iframeSrc}
          onLoad={handleLoad}
          title="JARVIS Browser"
          style={{ flex: 1, border: 'none', background: '#fff', display: 'block' }}
          allow="autoplay; fullscreen"
        />
      ) : (
        <div style={{
          flex: 1, display: 'flex', flexDirection: 'column',
          alignItems: 'center', justifyContent: 'center', gap: 16,
        }}>
          <div style={{ ...raj, fontSize: 10, letterSpacing: 6, color: 'rgba(79,195,247,0.25)' }}>
            BROWSER  READY
          </div>
          <div style={{ ...mono, fontSize: 10, color: 'rgba(79,195,247,0.18)' }}>
            say  "jarvis  open  youtube"
          </div>
        </div>
      )}
    </div>
  )
}
