import { useState, useEffect } from 'react'

const DAYS = ['Sunday','Monday','Tuesday','Wednesday','Thursday','Friday','Saturday']
const MONTHS = ['January','February','March','April','May','June','July','August','September','October','November','December']

export default function Clock() {
  const [now, setNow] = useState(new Date())

  useEffect(() => {
    const id = setInterval(() => setNow(new Date()), 1000)
    return () => clearInterval(id)
  }, [])

  const hh = String(now.getHours()).padStart(2, '0')
  const mm = String(now.getMinutes()).padStart(2, '0')
  const day = DAYS[now.getDay()].toUpperCase()
  const date = String(now.getDate()).padStart(2, '0')
  const month = MONTHS[now.getMonth()].toUpperCase()

  return (
    <div style={{ textAlign: 'center', marginTop: 28, userSelect: 'none' }}>
      <div style={{
        fontFamily: "'Share Tech Mono', monospace",
        fontSize: 48,
        letterSpacing: 8,
        color: '#e8f4ff',
        lineHeight: 1,
      }}>
        {hh}:{mm}
      </div>
      <div style={{
        fontFamily: "'Rajdhani', sans-serif",
        fontSize: 11,
        letterSpacing: 6,
        color: 'rgba(100,160,220,0.6)',
        marginTop: 8,
      }}>
        {day} {date} {month}
      </div>
    </div>
  )
}
