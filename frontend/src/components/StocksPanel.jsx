import { useState, useEffect } from 'react'

function StockCard({ ticker, name, price, change, change_pct }) {
  const positive = change >= 0
  const color = positive ? '#4ade80' : '#f87171'
  const dimColor = positive ? 'rgba(74,222,128,0.15)' : 'rgba(248,113,113,0.15)'
  const borderColor = positive ? 'rgba(74,222,128,0.25)' : 'rgba(248,113,113,0.2)'

  return (
    <div style={{
      background: 'rgba(255,255,255,0.03)',
      border: `1px solid ${borderColor}`,
      borderRadius: 10,
      padding: '16px 20px',
      display: 'flex',
      justifyContent: 'space-between',
      alignItems: 'center',
      backdropFilter: 'blur(4px)',
    }}>
      <div>
        <div style={{
          fontFamily: "'Share Tech Mono', monospace",
          fontSize: 15,
          color: '#e8f4ff',
          letterSpacing: 2,
        }}>{ticker}</div>
        <div style={{
          fontFamily: "'Rajdhani', sans-serif",
          fontSize: 12,
          color: 'rgba(100,160,220,0.5)',
          letterSpacing: 1,
          marginTop: 2,
        }}>{name}</div>
      </div>

      <div style={{ textAlign: 'right' }}>
        <div style={{
          fontFamily: "'Share Tech Mono', monospace",
          fontSize: 18,
          color: '#e8f4ff',
          letterSpacing: 1,
        }}>
          ${price.toLocaleString('en-US', { minimumFractionDigits: 2, maximumFractionDigits: 2 })}
        </div>
        <div style={{
          fontFamily: "'Rajdhani', sans-serif",
          fontSize: 13,
          color,
          background: dimColor,
          borderRadius: 4,
          padding: '2px 8px',
          marginTop: 4,
          letterSpacing: 1,
        }}>
          {positive ? '+' : ''}{change.toFixed(2)} ({positive ? '+' : ''}{change_pct.toFixed(2)}%)
        </div>
      </div>
    </div>
  )
}

export default function StocksPanel() {
  const [stocks, setStocks] = useState([])
  const [loading, setLoading] = useState(true)
  const [lastUpdated, setLastUpdated] = useState(null)

  async function fetchStocks() {
    try {
      const res = await fetch('http://localhost:8000/api/stocks')
      const data = await res.json()
      setStocks(data.stocks)
      setLastUpdated(new Date())
    } catch (e) {
      console.error('Failed to fetch stocks', e)
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => {
    fetchStocks()
    const id = setInterval(fetchStocks, 60000) // refresh every minute
    return () => clearInterval(id)
  }, [])

  return (
    <div style={{
      height: '100%',
      overflowY: 'auto',
      padding: '32px 40px',
      scrollbarWidth: 'thin',
      scrollbarColor: 'rgba(80,160,255,0.2) transparent',
    }}>
      {/* Header */}
      <div style={{ marginBottom: 28, display: 'flex', justifyContent: 'space-between', alignItems: 'flex-end' }}>
        <div>
          <div style={{
            fontFamily: "'Rajdhani', sans-serif",
            fontSize: 11,
            letterSpacing: 5,
            color: 'rgba(100,160,220,0.5)',
            marginBottom: 4,
          }}>MARKET OVERVIEW</div>
          <div style={{
            fontFamily: "'Share Tech Mono', monospace",
            fontSize: 24,
            color: '#e8f4ff',
            letterSpacing: 3,
          }}>STOCKS</div>
        </div>
        {lastUpdated && (
          <div style={{
            fontFamily: "'Rajdhani', sans-serif",
            fontSize: 11,
            color: 'rgba(100,160,220,0.4)',
            letterSpacing: 2,
          }}>
            UPDATED {lastUpdated.toLocaleTimeString()}
          </div>
        )}
      </div>

      {/* Grid */}
      {loading ? (
        <div style={{
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'center',
          height: 200,
          fontFamily: "'Rajdhani', sans-serif",
          fontSize: 13,
          letterSpacing: 4,
          color: 'rgba(100,160,220,0.4)',
        }}>
          FETCHING MARKET DATA...
        </div>
      ) : (
        <div style={{
          display: 'grid',
          gridTemplateColumns: 'repeat(auto-fill, minmax(280px, 1fr))',
          gap: 12,
        }}>
          {stocks.map(s => <StockCard key={s.ticker} {...s} />)}
        </div>
      )}
    </div>
  )
}
