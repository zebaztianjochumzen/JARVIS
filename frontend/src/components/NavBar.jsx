import { useState, useEffect } from 'react'

const TABS = [
  { id: 'home',     label: 'HOME',     icon: '⌂' },
  { id: 'stocks',   label: 'STOCKS',   icon: '▲' },
  { id: 'news',     label: 'NEWS',     icon: '◈' },
  { id: 'map',      label: 'MAP',      icon: '⊕' },
  { id: 'terminal', label: 'TERMINAL', icon: '>' },
  { id: 'music',    label: 'MUSIC',    icon: '♫' },
  { id: 'camera',   label: 'CAMERA',   icon: '◉' },
  { id: 'settings', label: 'SETTINGS', icon: '⚙' },
]

function StatusDot() {
  const [online, setOnline] = useState(navigator.onLine)
  useEffect(() => {
    const on  = () => setOnline(true)
    const off = () => setOnline(false)
    window.addEventListener('online',  on)
    window.addEventListener('offline', off)
    return () => { window.removeEventListener('online', on); window.removeEventListener('offline', off) }
  }, [])
  return (
    <div style={{ display: 'flex', alignItems: 'center', gap: 6, paddingRight: 16 }}>
      <div style={{
        width: 6, height: 6, borderRadius: '50%',
        background: online ? '#4ade80' : '#f87171',
        boxShadow: online ? '0 0 6px #4ade80' : '0 0 6px #f87171',
      }} />
      <span style={{ fontFamily: "'Rajdhani'", fontSize: 10, letterSpacing: 2, color: 'rgba(100,160,220,0.4)' }}>
        {online ? 'ONLINE' : 'OFFLINE'}
      </span>
    </div>
  )
}

export default function NavBar({ active, onChange }) {
  return (
    <div style={{
      position: 'fixed', bottom: 0, left: 0, right: 0, height: 52,
      display: 'flex', alignItems: 'center',
      background: 'rgba(7,11,20,0.92)',
      borderTop: '1px solid rgba(0,100,200,0.15)',
      backdropFilter: 'blur(12px)',
      zIndex: 100,
    }}>
      {/* left spacer */}
      <div style={{ flex: 1 }} />

      {/* centered tabs */}
      <div style={{ display: 'flex', gap: 2 }}>
        {TABS.map(tab => (
          <button
            key={tab.id}
            onClick={() => onChange(tab.id)}
            style={{
              background: active === tab.id ? 'rgba(0,120,220,0.2)' : 'transparent',
              border: 'none',
              borderBottom: active === tab.id ? '2px solid rgba(0,160,255,0.7)' : '2px solid transparent',
              borderRadius: 0,
              padding: '6px 14px',
              color: active === tab.id ? '#80c8ff' : 'rgba(100,160,220,0.35)',
              fontFamily: "'Rajdhani', sans-serif",
              fontSize: 10,
              letterSpacing: 3,
              cursor: 'pointer',
              transition: 'all 0.2s',
              display: 'flex', alignItems: 'center', gap: 6,
            }}
          >
            <span style={{ fontSize: 13 }}>{tab.icon}</span>
            {tab.label}
          </button>
        ))}
      </div>

      {/* right: status dot */}
      <div style={{ flex: 1, display: 'flex', justifyContent: 'flex-end', paddingRight: 16 }}>
        <StatusDot />
      </div>
    </div>
  )
}
