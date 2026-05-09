import { useState, useEffect } from 'react'

const DEFAULTS = {
  location:  'Stockholm',
  streamUrl: '',
  stocks:    'AAPL,NVDA,TSLA,MSFT,BTC-USD',
}

function Field({ label, value, onChange, placeholder, hint }) {
  return (
    <div style={{ marginBottom: 20 }}>
      <div style={{ fontFamily: "'Rajdhani'", fontSize: 10, letterSpacing: 4, color: 'rgba(100,160,220,0.5)', marginBottom: 6 }}>{label}</div>
      <input
        value={value}
        onChange={e => onChange(e.target.value)}
        placeholder={placeholder}
        style={{
          width: '100%', background: 'rgba(255,255,255,0.04)',
          border: '1px solid rgba(0,140,255,0.2)', borderRadius: 6,
          padding: '10px 14px', color: '#e8f4ff',
          fontFamily: "'Share Tech Mono', monospace", fontSize: 12, letterSpacing: 1, outline: 'none',
          boxSizing: 'border-box',
        }}
      />
      {hint && <div style={{ fontFamily: "'Rajdhani'", fontSize: 11, color: 'rgba(100,160,220,0.3)', marginTop: 4 }}>{hint}</div>}
    </div>
  )
}

export default function SettingsPanel() {
  const [cfg, setCfg] = useState(DEFAULTS)
  const [saved, setSaved] = useState(false)

  useEffect(() => {
    const stored = localStorage.getItem('jarvis_settings')
    if (stored) setCfg({ ...DEFAULTS, ...JSON.parse(stored) })
  }, [])

  function save() {
    localStorage.setItem('jarvis_settings', JSON.stringify(cfg))
    setSaved(true)
    setTimeout(() => setSaved(false), 2000)
  }

  function set(key) { return val => setCfg(c => ({ ...c, [key]: val })) }

  return (
    <div style={{ height: '100%', overflowY: 'auto', padding: '28px 40px', maxWidth: 600, scrollbarWidth: 'thin', scrollbarColor: 'rgba(80,160,255,0.15) transparent' }}>
      <div style={{ fontFamily: "'Share Tech Mono'", fontSize: 14, letterSpacing: 4, color: '#e8f4ff', marginBottom: 24 }}>⚙ SETTINGS</div>

      <Field
        label="LOCATION (for weather)"
        value={cfg.location}
        onChange={set('location')}
        placeholder="Stockholm"
      />
      <Field
        label="NEWS LIVE STREAM URL (YouTube embed)"
        value={cfg.streamUrl}
        onChange={set('streamUrl')}
        placeholder="https://www.youtube.com/embed/LIVE_VIDEO_ID?autoplay=1"
        hint="Go to YouTube → find the SVT/BBC/Al Jazeera live stream → Share → Embed → copy the src URL"
      />
      <Field
        label="WATCHLIST (comma-separated tickers)"
        value={cfg.stocks}
        onChange={set('stocks')}
        placeholder="AAPL,NVDA,TSLA,BTC-USD"
      />

      <button onClick={save} style={{
        background: saved ? 'rgba(74,222,128,0.2)' : 'rgba(0,120,220,0.3)',
        border: `1px solid ${saved ? 'rgba(74,222,128,0.4)' : 'rgba(0,140,255,0.4)'}`,
        borderRadius: 8, padding: '11px 28px',
        color: saved ? '#4ade80' : '#80c8ff',
        fontFamily: "'Rajdhani', sans-serif", fontSize: 12, letterSpacing: 4, cursor: 'pointer',
        transition: 'all 0.3s',
      }}>
        {saved ? 'SAVED ✓' : 'SAVE SETTINGS'}
      </button>
    </div>
  )
}
