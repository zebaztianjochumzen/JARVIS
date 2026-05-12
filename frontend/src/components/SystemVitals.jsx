import { useState, useEffect, useRef } from 'react'

// ── Arc gauge (SVG stroke-dasharray trick) ────────────────────────────────────
function ArcGauge({ label, value, max = 100, color = '#4fc3f7', size = 78 }) {
  const r    = size / 2 - 7
  const cx   = size / 2
  const cy   = size / 2
  const circ = 2 * Math.PI * r
  const arc  = circ * 0.75                              // 270°
  const fill = arc * Math.min(value / max, 1)
  const displayVal = max === 100
    ? `${Math.round(value)}%`
    : value >= 1000
      ? `${(value / 1024).toFixed(1)}M`
      : `${Math.round(value)}K`

  return (
    <div style={{ textAlign: 'center', width: size }}>
      <svg width={size} height={size} viewBox={`0 0 ${size} ${size}`}>
        {/* track */}
        <circle cx={cx} cy={cy} r={r} fill="none"
          stroke="rgba(80,180,255,0.1)" strokeWidth={4.5}
          strokeDasharray={`${arc} ${circ}`} strokeLinecap="round"
          transform={`rotate(135,${cx},${cy})`}
        />
        {/* fill */}
        <circle cx={cx} cy={cy} r={r} fill="none"
          stroke={color} strokeWidth={4.5}
          strokeDasharray={`${fill} ${circ}`} strokeLinecap="round"
          transform={`rotate(135,${cx},${cy})`}
          style={{
            transition: 'stroke-dasharray 0.55s ease',
            filter: `drop-shadow(0 0 4px ${color})`,
          }}
        />
        <text x={cx} y={cy + 1} textAnchor="middle" dominantBaseline="middle"
          fill={color}
          style={{ fontFamily: "'Share Tech Mono',monospace", fontSize: 11, fontWeight: 700 }}>
          {displayVal}
        </text>
        <text x={cx} y={cy + 14} textAnchor="middle"
          fill="rgba(255,255,255,0.3)"
          style={{ fontFamily: "'Share Tech Mono',monospace", fontSize: 8 }}>
          {label}
        </text>
      </svg>
    </div>
  )
}

// ── Main component ────────────────────────────────────────────────────────────
export default function SystemVitals() {
  const [vitals,  setVitals]  = useState(null)
  const [visible, setVisible] = useState(false)
  const prevNetRef = useRef(null)

  useEffect(() => {
    let es
    try {
      es = new EventSource('http://localhost:8000/api/vitals')
      es.onmessage = (e) => {
        const d = JSON.parse(e.data)

        // Compute KB/s from cumulative byte counters
        let sentKBs = 0, recvKBs = 0
        const now = Date.now()
        if (prevNetRef.current) {
          const dt = (now - prevNetRef.current.ts) / 1000
          if (dt > 0) {
            sentKBs = (d.net_sent_bytes - prevNetRef.current.sent) / dt / 1024
            recvKBs = (d.net_recv_bytes - prevNetRef.current.recv) / dt / 1024
          }
        }
        prevNetRef.current = { ts: now, sent: d.net_sent_bytes, recv: d.net_recv_bytes }

        setVitals({ cpu: d.cpu, ram: d.ram, sentKBs: Math.max(0, sentKBs), recvKBs: Math.max(0, recvKBs) })
        if (!visible) setVisible(true)
      }
      es.onerror = () => setVisible(false)
    } catch {
      setVisible(false)
    }
    return () => es?.close()
  }, [])  // eslint-disable-line react-hooks/exhaustive-deps

  if (!visible || !vitals) return null

  // Colour the CPU gauge based on load
  const cpuColor = vitals.cpu > 80 ? '#ff6b6b' : vitals.cpu > 60 ? '#ffd93d' : '#4fc3f7'
  const ramColor = vitals.ram > 85 ? '#ff6b6b' : vitals.ram > 70 ? '#ffd93d' : '#7eb8f7'
  const netMax   = 2048  // 2 MB/s display ceiling

  return (
    <div style={{
      position:       'fixed',
      top:            28,
      right:          36,
      display:        'flex',
      gap:            2,
      alignItems:     'center',
      zIndex:         900,
      pointerEvents:  'none',
      background:     'rgba(7,11,20,0.75)',
      border:         '1px solid rgba(80,180,255,0.14)',
      borderRadius:   10,
      padding:        '4px 8px',
      backdropFilter: 'blur(8px)',
    }}>
      <ArcGauge label="CPU"  value={vitals.cpu}     color={cpuColor} />
      <ArcGauge label="RAM"  value={vitals.ram}     color={ramColor} />
      <ArcGauge label="↑NET" value={vitals.sentKBs} max={netMax} color="#a3e4d7" size={70} />
      <ArcGauge label="↓NET" value={vitals.recvKBs} max={netMax} color="#a3e4d7" size={70} />
    </div>
  )
}
