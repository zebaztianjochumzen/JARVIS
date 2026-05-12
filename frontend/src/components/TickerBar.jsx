import { useState, useEffect } from 'react'

function TickerItem({ ticker, price, change_pct }) {
  const positive  = change_pct >= 0
  const alert     = Math.abs(change_pct) >= 2
  const color     = alert ? '#fbbf24' : positive ? '#4ade80' : '#f87171'
  const arrow     = positive ? '▲' : '▼'
  return (
    <span style={{
      display: 'inline-flex', alignItems: 'center', gap: 6,
      padding: '0 22px',
      borderRight: '1px solid rgba(255,255,255,0.06)',
      background: alert ? 'rgba(251,191,36,0.06)' : 'transparent',
    }}>
      <span style={{ fontFamily: "'Share Tech Mono', monospace", fontSize: 11, color: '#e8f4ff', letterSpacing: 1 }}>
        {ticker}
      </span>
      <span style={{ fontFamily: "'Share Tech Mono', monospace", fontSize: 11, color: '#9ab8d8' }}>
        ${price.toLocaleString('en-US', { minimumFractionDigits: 2, maximumFractionDigits: 2 })}
      </span>
      <span style={{ fontFamily: "'Rajdhani', sans-serif", fontSize: 11, color, letterSpacing: 1 }}>
        {arrow} {Math.abs(change_pct).toFixed(2)}%{alert ? ' ⚠' : ''}
      </span>
    </span>
  )
}

export default function TickerBar() {
  const [stocks, setStocks] = useState([])
  const [now, setNow]       = useState(new Date())

  useEffect(() => {
    async function fetchStocks() {
      try {
        const res  = await fetch('http://localhost:8000/api/stocks')
        const data = await res.json()
        setStocks(data.stocks || [])
      } catch { /* silent */ }
    }
    fetchStocks()
    const stockId = setInterval(fetchStocks, 30000)
    const clockId = setInterval(() => setNow(new Date()), 1000)
    return () => { clearInterval(stockId); clearInterval(clockId) }
  }, [])

  const hh = String(now.getHours()).padStart(2, '0')
  const mm = String(now.getMinutes()).padStart(2, '0')
  const ss = String(now.getSeconds()).padStart(2, '0')
  const items = [...stocks, ...stocks]

  return (
    <div style={{
      height: 34, flexShrink: 0,
      background: 'rgba(5,9,18,0.95)',
      borderBottom: '1px solid rgba(0,100,200,0.2)',
      display: 'flex', alignItems: 'center', overflow: 'hidden',
      backdropFilter: 'blur(8px)', zIndex: 200,
    }}>
      <div style={{
        flexShrink: 0, padding: '0 16px',
        borderRight: '1px solid rgba(0,100,200,0.25)',
        fontFamily: "'Rajdhani', sans-serif", fontSize: 11,
        letterSpacing: 4, color: '#4fc3f7', whiteSpace: 'nowrap',
      }}>JARVIS</div>

      <div style={{ flex: 1, overflow: 'hidden' }}>
        {stocks.length > 0 && (
          <div style={{
            display: 'inline-flex', whiteSpace: 'nowrap',
            animation: `ticker-scroll ${stocks.length * 4}s linear infinite`,
          }}>
            {items.map((s, i) => <TickerItem key={i} {...s} />)}
          </div>
        )}
      </div>

      <div style={{
        flexShrink: 0, padding: '0 16px',
        borderLeft: '1px solid rgba(0,100,200,0.25)',
        fontFamily: "'Share Tech Mono', monospace",
        fontSize: 12, color: '#e8f4ff', letterSpacing: 2, whiteSpace: 'nowrap',
      }}>{hh}:{mm}:{ss}</div>

      <style>{`
        @keyframes ticker-scroll {
          0%   { transform: translateX(0); }
          100% { transform: translateX(-50%); }
        }
      `}</style>
    </div>
  )
}
