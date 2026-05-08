import { useEffect, useRef } from 'react'
import './Orb.css'

const TICK_COUNT = 24

function Ticks({ radius, size }) {
  return (
    <svg
      width={size}
      height={size}
      style={{ position: 'absolute', top: 0, left: 0, pointerEvents: 'none' }}
    >
      {Array.from({ length: TICK_COUNT }).map((_, i) => {
        const angle = (i / TICK_COUNT) * 2 * Math.PI - Math.PI / 2
        const isMajor = i % 6 === 0
        const tickLen = isMajor ? 12 : 6
        const cx = size / 2
        const cy = size / 2
        const outerR = radius + 18
        const innerR = outerR - tickLen
        const x1 = cx + outerR * Math.cos(angle)
        const y1 = cy + outerR * Math.sin(angle)
        const x2 = cx + innerR * Math.cos(angle)
        const y2 = cy + innerR * Math.sin(angle)
        return (
          <line
            key={i}
            x1={x1} y1={y1} x2={x2} y2={y2}
            stroke={isMajor ? 'rgba(100,180,255,0.7)' : 'rgba(100,180,255,0.3)'}
            strokeWidth={isMajor ? 1.5 : 1}
          />
        )
      })}
    </svg>
  )
}

export default function Orb({ active, onClick, thinking }) {
  const SIZE = 260
  const RADIUS = 100

  return (
    <div
      className={`orb-wrapper${active ? ' orb-active' : ''}`}
      onClick={onClick}
      style={{ width: SIZE, height: SIZE, position: 'relative', cursor: 'pointer' }}
    >
      {/* Outer glow ring */}
      <div className={`orb-glow${thinking ? ' orb-thinking' : ''}`} style={{
        position: 'absolute',
        top: '50%', left: '50%',
        transform: 'translate(-50%, -50%)',
        width: RADIUS * 2,
        height: RADIUS * 2,
        borderRadius: '50%',
        boxShadow: thinking
          ? '0 0 40px 16px rgba(0,180,255,0.55), 0 0 80px 32px rgba(0,100,255,0.3)'
          : '0 0 30px 10px rgba(0,160,255,0.4), 0 0 60px 24px rgba(0,80,220,0.2)',
        border: '2px solid rgba(80,180,255,0.9)',
        transition: 'box-shadow 0.4s ease',
      }} />

      {/* Rotating arc 1 */}
      <div className="orb-arc orb-arc-1" style={{
        position: 'absolute',
        top: '50%', left: '50%',
        transform: 'translate(-50%, -50%)',
        width: RADIUS * 2 + 8,
        height: RADIUS * 2 + 8,
        borderRadius: '50%',
        border: '2px solid transparent',
        borderTopColor: 'rgba(80,200,255,0.8)',
        borderRightColor: 'rgba(80,200,255,0.3)',
      }} />

      {/* Rotating arc 2 (counter) */}
      <div className="orb-arc orb-arc-2" style={{
        position: 'absolute',
        top: '50%', left: '50%',
        transform: 'translate(-50%, -50%)',
        width: RADIUS * 2 + 20,
        height: RADIUS * 2 + 20,
        borderRadius: '50%',
        border: '1.5px solid transparent',
        borderBottomColor: 'rgba(80,200,255,0.5)',
        borderLeftColor: 'rgba(80,200,255,0.15)',
      }} />

      {/* Tick marks */}
      <Ticks radius={RADIUS} size={SIZE} />

      {/* Inner dark circle */}
      <div style={{
        position: 'absolute',
        top: '50%', left: '50%',
        transform: 'translate(-50%, -50%)',
        width: RADIUS * 2 - 6,
        height: RADIUS * 2 - 6,
        borderRadius: '50%',
        background: 'radial-gradient(circle at 40% 35%, #0d1828 0%, #070b14 70%)',
      }} />

      {/* JARVIS label */}
      <div style={{
        position: 'absolute',
        top: '50%', left: '50%',
        transform: 'translate(-50%, -50%)',
        fontFamily: "'Rajdhani', sans-serif",
        fontWeight: 500,
        fontSize: 22,
        letterSpacing: 8,
        color: '#e8f4ff',
        textTransform: 'uppercase',
        userSelect: 'none',
        paddingLeft: 8,
      }}>
        JARVIS
      </div>
    </div>
  )
}
