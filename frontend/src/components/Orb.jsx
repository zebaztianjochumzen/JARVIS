import './Orb.css'

const TICK_COUNT = 24
const BAR_COUNT  = 20

function Ticks({ radius, size }) {
  return (
    <svg width={size} height={size} style={{ position: 'absolute', top: 0, left: 0, pointerEvents: 'none' }}>
      {Array.from({ length: TICK_COUNT }).map((_, i) => {
        const angle  = (i / TICK_COUNT) * 2 * Math.PI - Math.PI / 2
        const isMajor = i % 6 === 0
        const tickLen = isMajor ? 12 : 6
        const cx = size / 2, cy = size / 2
        const outerR = radius + 18, innerR = outerR - tickLen
        return (
          <line key={i}
            x1={cx + outerR * Math.cos(angle)} y1={cy + outerR * Math.sin(angle)}
            x2={cx + innerR * Math.cos(angle)} y2={cy + innerR * Math.sin(angle)}
            stroke={isMajor ? 'rgba(100,180,255,0.7)' : 'rgba(100,180,255,0.3)'}
            strokeWidth={isMajor ? 1.5 : 1}
          />
        )
      })}
    </svg>
  )
}

function Waveform({ radius, size }) {
  return (
    <svg width={size} height={size} style={{ position: 'absolute', top: 0, left: 0, pointerEvents: 'none' }}>
      {Array.from({ length: BAR_COUNT }).map((_, i) => {
        const angle   = (i / BAR_COUNT) * 2 * Math.PI - Math.PI / 2
        const barMaxH = 18
        const cx = size / 2, cy = size / 2
        const r1 = radius + 4
        const r2 = radius + 4 + barMaxH
        const delay = (i / BAR_COUNT) * 1.2
        return (
          <line key={i}
            x1={cx + r1 * Math.cos(angle)} y1={cy + r1 * Math.sin(angle)}
            x2={cx + r2 * Math.cos(angle)} y2={cy + r2 * Math.sin(angle)}
            stroke="rgba(80,200,255,0.7)" strokeWidth={2} strokeLinecap="round"
            style={{ animation: `wave-bar 0.6s ease-in-out ${delay}s infinite alternate` }}
          />
        )
      })}
    </svg>
  )
}

export default function Orb({ onClick, thinking, speaking, userSpeaking }) {
  const SIZE   = 260
  const RADIUS = 100

  return (
    <div
      className={`orb-wrapper${speaking ? ' orb-bounce' : ''}${thinking ? ' orb-user-glow' : ''}${userSpeaking && !speaking ? ' orb-voice-active' : ''}`}
      onClick={onClick}
      style={{ width: SIZE, height: SIZE, position: 'relative', cursor: onClick ? 'pointer' : 'default' }}
    >
      {/* Outer glow ring */}
      <div className={`orb-glow${thinking ? ' orb-thinking' : speaking ? ' orb-speaking' : ''}`} style={{
        position: 'absolute', top: '50%', left: '50%',
        transform: 'translate(-50%, -50%)',
        width: RADIUS * 2, height: RADIUS * 2, borderRadius: '50%',
        border: '2px solid rgba(80,180,255,0.9)',
        boxShadow: speaking
          ? '0 0 50px 20px rgba(0,200,255,0.6), 0 0 100px 40px rgba(0,100,255,0.35)'
          : thinking
          ? '0 0 40px 16px rgba(0,180,255,0.55), 0 0 80px 32px rgba(0,100,255,0.3)'
          : '0 0 30px 10px rgba(0,160,255,0.4), 0 0 60px 24px rgba(0,80,220,0.2)',
        transition: 'box-shadow 0.4s ease',
      }} />

      {/* Arc 1 */}
      <div className={`orb-arc orb-arc-1${thinking || speaking ? ' orb-fast' : ''}`} style={{
        position: 'absolute', top: '50%', left: '50%',
        transform: 'translate(-50%, -50%)',
        width: RADIUS * 2 + 8, height: RADIUS * 2 + 8, borderRadius: '50%',
        border: '2px solid transparent',
        borderTopColor: 'rgba(80,200,255,0.8)',
        borderRightColor: 'rgba(80,200,255,0.3)',
      }} />

      {/* Arc 2 */}
      <div className={`orb-arc orb-arc-2${thinking || speaking ? ' orb-fast' : ''}`} style={{
        position: 'absolute', top: '50%', left: '50%',
        transform: 'translate(-50%, -50%)',
        width: RADIUS * 2 + 20, height: RADIUS * 2 + 20, borderRadius: '50%',
        border: '1.5px solid transparent',
        borderBottomColor: 'rgba(80,200,255,0.5)',
        borderLeftColor: 'rgba(80,200,255,0.15)',
      }} />

      {/* Waveform (speaking only) */}
      {speaking && <Waveform radius={RADIUS} size={SIZE} />}

      {/* Tick marks (idle/thinking) */}
      {!speaking && <Ticks radius={RADIUS} size={SIZE} />}

      {/* Inner circle */}
      <div style={{
        position: 'absolute', top: '50%', left: '50%',
        transform: 'translate(-50%, -50%)',
        width: RADIUS * 2 - 6, height: RADIUS * 2 - 6, borderRadius: '50%',
        background: 'radial-gradient(circle at 40% 35%, #0d1828 0%, #070b14 70%)',
      }} />

      {/* Label */}
      <div style={{
        position: 'absolute', top: '50%', left: '50%',
        transform: 'translate(-50%, -50%)',
        fontFamily: "'Rajdhani', sans-serif", fontWeight: 500,
        fontSize: 22, letterSpacing: 8, color: '#e8f4ff',
        textTransform: 'uppercase', userSelect: 'none', paddingLeft: 8,
      }}>
        JARVIS
      </div>
    </div>
  )
}
