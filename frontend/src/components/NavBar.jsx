const TABS = [
  { id: 'chat',   label: 'CHAT',   icon: '◎' },
  { id: 'stocks', label: 'STOCKS', icon: '▲' },
]

export default function NavBar({ active, onChange }) {
  return (
    <div style={{
      position: 'fixed',
      bottom: 0,
      left: 0,
      right: 0,
      height: 52,
      display: 'flex',
      alignItems: 'center',
      justifyContent: 'center',
      gap: 4,
      background: 'rgba(7,11,20,0.85)',
      borderTop: '1px solid rgba(0,100,200,0.15)',
      backdropFilter: 'blur(10px)',
      zIndex: 100,
    }}>
      {TABS.map(tab => (
        <button
          key={tab.id}
          onClick={() => onChange(tab.id)}
          style={{
            background: active === tab.id ? 'rgba(0,120,220,0.2)' : 'transparent',
            border: active === tab.id ? '1px solid rgba(0,140,255,0.35)' : '1px solid transparent',
            borderRadius: 8,
            padding: '6px 20px',
            color: active === tab.id ? '#80c8ff' : 'rgba(100,160,220,0.4)',
            fontFamily: "'Rajdhani', sans-serif",
            fontSize: 11,
            letterSpacing: 4,
            cursor: 'pointer',
            transition: 'all 0.2s',
            display: 'flex',
            alignItems: 'center',
            gap: 8,
          }}
        >
          <span style={{ fontSize: 14 }}>{tab.icon}</span>
          {tab.label}
        </button>
      ))}
    </div>
  )
}
