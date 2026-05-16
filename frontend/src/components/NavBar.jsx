import { useState, useEffect } from 'react'

const TABS = [
  { id: 'home',     icon: '⌂', label: 'HOME'     },
  { id: 'stocks',   icon: '▲', label: 'STOCKS'   },
  { id: 'news',     icon: '◈', label: 'NEWS'      },
  { id: 'map',      icon: '⊕', label: 'MAP'       },
  { id: 'terminal', icon: '>', label: 'TERMINAL'  },
  { id: 'settings', icon: '⚙', label: 'SETTINGS' },
]

const WIDGET_BTNS = [
  { id: 'chat',    icon: '💬', label: 'CHAT'  },
  { id: 'spotify', icon: '♫',  label: 'MUSIC' },
  { id: 'camera',  icon: '◉',  label: 'CAM'   },
]

function StatusDot() {
  const [online, setOnline] = useState(navigator.onLine)
  useEffect(() => {
    const on  = () => setOnline(true)
    const off = () => setOnline(false)
    window.addEventListener('online',  on)
    window.addEventListener('offline', off)
    return () => {
      window.removeEventListener('online',  on)
      window.removeEventListener('offline', off)
    }
  }, [])
  return (
    <div style={{ display: 'flex', alignItems: 'center', gap: 5 }}>
      <div style={{
        width: 5, height: 5, borderRadius: '50%',
        background: online ? '#4ade80' : '#f87171',
        boxShadow:  online ? '0 0 5px #4ade80' : '0 0 5px #f87171',
      }} />
      <span style={{
        fontFamily: "'Rajdhani', sans-serif",
        fontSize: 9, letterSpacing: 2,
        color: 'rgba(100,160,220,0.4)',
      }}>
        {online ? 'ONLINE' : 'OFFLINE'}
      </span>
    </div>
  )
}

// Shared button style builder
const tabStyle = (active) => ({
  background:   active ? 'rgba(0,120,220,0.18)' : 'transparent',
  border:       'none',
  borderBottom: active ? '2px solid rgba(0,160,255,0.7)' : '2px solid transparent',
  borderRadius: 0,
  padding:      '5px 13px',
  color:        active ? '#80c8ff' : 'rgba(100,160,220,0.35)',
  fontFamily:   "'Rajdhani', sans-serif",
  fontSize:     10, letterSpacing: 3,
  cursor:       'pointer',
  transition:   'all 0.2s',
  display:      'flex', alignItems: 'center', gap: 5,
})

const widgetStyle = (active) => ({
  background:   active ? 'rgba(0,212,255,0.1)' : 'transparent',
  border:       'none',
  borderBottom: active ? '2px solid rgba(0,212,255,0.7)' : '2px solid transparent',
  borderRadius: 0,
  padding:      '5px 13px',
  color:        active ? '#00d4ff' : 'rgba(100,160,220,0.35)',
  fontFamily:   "'Rajdhani', sans-serif",
  fontSize:     10, letterSpacing: 3,
  cursor:       'pointer',
  transition:   'all 0.2s',
  display:      'flex', alignItems: 'center', gap: 5,
  position:     'relative',
})

export default function NavBar({ active, onChange, widgetOpen, onToggleWidget }) {
  return (
    <div style={{
      position: 'fixed', bottom: 0, left: 0, right: 0, height: 50,
      display: 'flex', alignItems: 'center',
      background: 'rgba(5, 10, 22, 0.95)',
      borderTop:  '1px solid rgba(0, 100, 200, 0.18)',
      backdropFilter: 'blur(14px)',
      zIndex: 100,
    }}>

      {/* ── Left: tab navigation ── */}
      <div style={{ flex: 1, display: 'flex', justifyContent: 'center' }}>
        <div style={{ display: 'flex', gap: 1 }}>
          {TABS.map(tab => (
            <button
              key={tab.id}
              onClick={() => onChange(tab.id)}
              style={tabStyle(active === tab.id)}
            >
              <span style={{ fontSize: 12 }}>{tab.icon}</span>
              {tab.label}
            </button>
          ))}
        </div>
      </div>

      {/* ── Divider ── */}
      <div style={{
        width: 1, height: 26, flexShrink: 0,
        background: 'rgba(0,212,255,0.14)',
        margin: '0 4px',
      }} />

      {/* ── Right: widget toggles ── */}
      <div style={{ display: 'flex', gap: 1, paddingRight: 10 }}>
        {WIDGET_BTNS.map(w => {
          const isOpen = widgetOpen?.[w.id]
          return (
            <button
              key={w.id}
              onClick={() => onToggleWidget(w.id)}
              style={widgetStyle(isOpen)}
            >
              <span style={{ fontSize: 12 }}>{w.icon}</span>
              {w.label}
              {/* Active dot indicator */}
              {isOpen && (
                <span style={{
                  position: 'absolute', bottom: 2, left: '50%',
                  transform: 'translateX(-50%)',
                  width: 3, height: 3, borderRadius: '50%',
                  background: '#00d4ff',
                  boxShadow: '0 0 5px #00d4ff',
                  display: 'block',
                }} />
              )}
            </button>
          )
        })}
      </div>

      {/* ── Far right: status ── */}
      <div style={{ paddingRight: 14 }}>
        <StatusDot />
      </div>
    </div>
  )
}
