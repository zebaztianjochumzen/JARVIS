import { useState, useEffect } from 'react'

function Card({ title, children }) {
  return (
    <div style={{
      background: 'rgba(255,255,255,0.03)', border: '1px solid rgba(0,100,200,0.15)',
      borderRadius: 10, padding: '14px 18px', marginBottom: 12,
    }}>
      <div style={{ fontFamily: "'Rajdhani'", fontSize: 10, letterSpacing: 4, color: 'rgba(100,160,220,0.5)', marginBottom: 10 }}>
        {title}
      </div>
      {children}
    </div>
  )
}

export default function BriefingPanel() {
  const [weather, setWeather] = useState(null)
  const [stocks,  setStocks]  = useState([])
  const [news,    setNews]    = useState([])

  useEffect(() => {
    Promise.all([
      fetch('http://localhost:8000/api/briefing').then(r => r.json()).catch(() => null),
      fetch('http://localhost:8000/api/stocks').then(r => r.json()).catch(() => ({ stocks: [] })),
      fetch('http://localhost:8000/api/news').then(r => r.json()).catch(() => ({ articles: [] })),
    ]).then(([briefing, stockData, newsData]) => {
      if (briefing?.weather) setWeather(briefing.weather)
      setStocks((stockData?.stocks || []).slice(0, 5))
      setNews((newsData?.articles || []).slice(0, 5))
    })
  }, [])

  const now = new Date()
  const DAYS = ['Sunday','Monday','Tuesday','Wednesday','Thursday','Friday','Saturday']

  return (
    <div style={{
      height: '100%', overflowY: 'auto', padding: '20px 20px 20px 12px',
      borderLeft: '1px solid rgba(0,100,200,0.12)',
      scrollbarWidth: 'thin', scrollbarColor: 'rgba(80,160,255,0.15) transparent',
    }}>
      {/* Date + greeting */}
      <div style={{ marginBottom: 16 }}>
        <div style={{ fontFamily: "'Share Tech Mono'", fontSize: 13, color: '#e8f4ff', letterSpacing: 2 }}>
          DAILY BRIEFING
        </div>
        <div style={{ fontFamily: "'Rajdhani'", fontSize: 11, letterSpacing: 3, color: 'rgba(100,160,220,0.4)', marginTop: 4 }}>
          {DAYS[now.getDay()].toUpperCase()} · {now.toLocaleDateString('sv-SE')}
        </div>
      </div>

      {/* Weather */}
      {weather && (
        <Card title="WEATHER">
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
            <div>
              <div style={{ fontFamily: "'Share Tech Mono'", fontSize: 28, color: '#e8f4ff' }}>
                {weather.temp_c}°C
              </div>
              <div style={{ fontFamily: "'Rajdhani'", fontSize: 12, color: 'rgba(100,160,220,0.6)', marginTop: 2 }}>
                {weather.description}
              </div>
            </div>
            <div style={{ textAlign: 'right' }}>
              <div style={{ fontFamily: "'Rajdhani'", fontSize: 11, color: 'rgba(100,160,220,0.4)', letterSpacing: 2 }}>{weather.city}</div>
              <div style={{ fontFamily: "'Share Tech Mono'", fontSize: 11, color: 'rgba(100,160,220,0.5)', marginTop: 4 }}>
                💧 {weather.humidity}% · 💨 {weather.wind_kmh} km/h
              </div>
            </div>
          </div>
        </Card>
      )}

      {/* Market summary */}
      {stocks.length > 0 && (
        <Card title="MARKET SUMMARY">
          {stocks.map(s => {
            const pos = s.change_pct >= 0
            const alert = Math.abs(s.change_pct) >= 2
            const color = alert ? '#fbbf24' : pos ? '#4ade80' : '#f87171'
            return (
              <div key={s.ticker} style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', padding: '5px 0', borderBottom: '1px solid rgba(255,255,255,0.04)' }}>
                <div>
                  <span style={{ fontFamily: "'Share Tech Mono'", fontSize: 12, color: '#e8f4ff' }}>{s.ticker}</span>
                  <span style={{ fontFamily: "'Rajdhani'", fontSize: 10, color: 'rgba(100,160,220,0.4)', marginLeft: 8, letterSpacing: 1 }}>{s.name}</span>
                </div>
                <div style={{ fontFamily: "'Share Tech Mono'", fontSize: 12, color }}>
                  {pos ? '▲' : '▼'} {Math.abs(s.change_pct).toFixed(2)}%
                </div>
              </div>
            )
          })}
        </Card>
      )}

      {/* Top news */}
      {news.length > 0 && (
        <Card title="TOP STORIES">
          {news.map((a, i) => (
            <a key={i} href={a.link} target="_blank" rel="noreferrer" style={{ textDecoration: 'none', display: 'block', padding: '6px 0', borderBottom: '1px solid rgba(255,255,255,0.04)' }}>
              <div style={{ fontFamily: "'Rajdhani'", fontSize: 11, color: 'rgba(100,160,220,0.5)', letterSpacing: 2, marginBottom: 2 }}>{a.source}</div>
              <div style={{ fontFamily: "'Rajdhani'", fontSize: 13, color: 'rgba(220,235,255,0.8)', lineHeight: 1.35 }}>{a.title}</div>
            </a>
          ))}
        </Card>
      )}
    </div>
  )
}
