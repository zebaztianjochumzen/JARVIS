import { useState, useEffect } from 'react'

const SIZE   = 260
const CX     = SIZE / 2
const R      = 118   // just outside the orb arcs

export default function TimerRing({ duration, endsAt, label, onComplete }) {
  const [remaining, setRemaining] = useState(() => Math.max(0, Math.ceil((endsAt - Date.now()) / 1000)))

  useEffect(() => {
    const tick = () => {
      const r = Math.max(0, Math.ceil((endsAt - Date.now()) / 1000))
      setRemaining(r)
      if (r <= 0) onComplete?.()
    }
    const id = setInterval(tick, 250)
    return () => clearInterval(id)
  }, [endsAt, onComplete])

  const progress     = duration > 0 ? Math.max(0, remaining / duration) : 0
  const circumference = 2 * Math.PI * R
  const dashOffset   = circumference * (1 - progress)

  const mins = Math.floor(remaining / 60)
  const secs = remaining % 60
  const timeStr = `${mins}:${String(secs).padStart(2, '0')}`
  const done = remaining <= 0

  return (
    <div style={{ position: 'absolute', top: '50%', left: '50%', transform: 'translate(-50%, -50%)', pointerEvents: 'none' }}>
      <svg width={SIZE} height={SIZE} style={{ overflow: 'visible' }}>
        {/* Background track */}
        <circle cx={CX} cy={CX} r={R}
          fill="none" stroke="rgba(79,195,247,0.1)" strokeWidth={2.5} />

        {/* Countdown arc */}
        <circle cx={CX} cy={CX} r={R}
          fill="none"
          stroke={done ? 'rgba(79,247,150,0.9)' : '#4fc3f7'}
          strokeWidth={2.5}
          strokeLinecap="round"
          strokeDasharray={circumference}
          strokeDashoffset={dashOffset}
          transform={`rotate(-90 ${CX} ${CX})`}
          style={{
            transition: 'stroke-dashoffset 0.25s linear, stroke 0.4s ease',
            filter: `drop-shadow(0 0 6px ${done ? '#4ff796' : '#4fc3f7'})`,
          }}
        />
      </svg>

      {/* Time display below JARVIS label */}
      <div style={{
        position: 'absolute',
        top: '50%', left: '50%',
        transform: 'translate(-50%, 28px)',
        fontFamily: "'Share Tech Mono', monospace",
        fontSize: done ? 13 : 18,
        letterSpacing: done ? 3 : 4,
        color: done ? 'rgba(79,247,150,0.9)' : '#4fc3f7',
        textAlign: 'center',
        whiteSpace: 'nowrap',
        transition: 'color 0.4s ease',
      }}>
        {done ? 'DONE' : timeStr}
      </div>

      {/* Label above JARVIS label */}
      {label && (
        <div style={{
          position: 'absolute',
          top: '50%', left: '50%',
          transform: 'translate(-50%, -44px)',
          fontFamily: "'Rajdhani', sans-serif",
          fontSize: 9, letterSpacing: 4,
          color: 'rgba(79,195,247,0.45)',
          textAlign: 'center',
          whiteSpace: 'nowrap',
          textTransform: 'uppercase',
        }}>
          {label}
        </div>
      )}
    </div>
  )
}
