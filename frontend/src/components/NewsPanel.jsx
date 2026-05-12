import { useState, useEffect } from 'react'

const SOURCE_COLORS = {
  'SVT Nyheter':     '#4fc3f7',
  'Aftonbladet':     '#fbbf24',
  'Dagens industri': '#a78bfa',
}

function timeAgo(ts) {
  if (!ts) return ''
  const diff = Math.floor((Date.now() / 1000 - ts) / 60)
  if (diff < 1)  return 'just nu'
  if (diff < 60) return `${diff}m sedan`
  const h = Math.floor(diff / 60)
  if (h < 24)    return `${h}h sedan`
  return `${Math.floor(h / 24)}d sedan`
}

function HeadlineRow({ source, title, summary, link, published, image }) {
  const color = SOURCE_COLORS[source] || '#80c8ff'
  return (
    <a
      href={link}
      target="_blank"
      rel="noreferrer"
      style={{ textDecoration: 'none', display: 'block' }}
    >
      <div style={{
        display: 'flex',
        gap: 12,
        padding: '12px 0',
        borderBottom: '1px solid rgba(255,255,255,0.05)',
        cursor: 'pointer',
        transition: 'background 0.15s',
      }}
        onMouseEnter={e => e.currentTarget.style.background = 'rgba(255,255,255,0.03)'}
        onMouseLeave={e => e.currentTarget.style.background = 'transparent'}
      >
        {image && (
          <img
            src={image}
            alt=""
            style={{
              width: 72, height: 52, objectFit: 'cover',
              borderRadius: 6, flexShrink: 0,
              border: '1px solid rgba(255,255,255,0.08)',
            }}
          />
        )}
        <div style={{ flex: 1, minWidth: 0 }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: 8, marginBottom: 4 }}>
            <span style={{
              fontFamily: "'Rajdhani', sans-serif",
              fontSize: 10,
              letterSpacing: 2,
              color,
              textTransform: 'uppercase',
            }}>{source}</span>
            <span style={{
              fontFamily: "'Share Tech Mono', monospace",
              fontSize: 10,
              color: 'rgba(100,160,220,0.35)',
            }}>{timeAgo(published)}</span>
          </div>
          <div style={{
            fontFamily: "'Rajdhani', sans-serif",
            fontSize: 14,
            fontWeight: 500,
            color: 'rgba(230,240,255,0.9)',
            lineHeight: 1.35,
            letterSpacing: 0.3,
            overflow: 'hidden',
            display: '-webkit-box',
            WebkitLineClamp: 2,
            WebkitBoxOrient: 'vertical',
          }}>{title}</div>
        </div>
      </div>
    </a>
  )
}

export default function NewsPanel() {
  const [articles, setArticles] = useState([])
  const [loading, setLoading]   = useState(true)
  const [lastUpdated, setLastUpdated] = useState(null)

  async function fetchNews() {
    try {
      const res  = await fetch('http://localhost:8000/api/news')
      const data = await res.json()
      setArticles(data.articles)
      setLastUpdated(new Date())
    } catch (e) {
      console.error('Failed to fetch news', e)
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => {
    fetchNews()
    const id = setInterval(fetchNews, 5 * 60 * 1000) // refresh every 5 min
    return () => clearInterval(id)
  }, [])

  return (
    <div style={{ display: 'flex', height: '100%', overflow: 'hidden' }}>

      {/* Left: live stream */}
      <div style={{
        flex: '0 0 62%',
        display: 'flex',
        flexDirection: 'column',
        borderRight: '1px solid rgba(0,100,200,0.15)',
        overflow: 'hidden',
      }}>
        <div style={{
          padding: '12px 16px',
          display: 'flex',
          justifyContent: 'space-between',
          alignItems: 'center',
          borderBottom: '1px solid rgba(0,100,200,0.12)',
          flexShrink: 0,
        }}>
          <div style={{
            fontFamily: "'Share Tech Mono', monospace",
            fontSize: 12,
            letterSpacing: 3,
            color: '#4fc3f7',
          }}>◉ SVT NYHETER LIVE</div>
        </div>
        <div style={{ flex: 1, position: 'relative', background: '#000' }}>
          <iframe
            src="https://www.youtube.com/embed/live_stream?channel=UCN4TCCaX85NZMzJQ9b5UBXA&autoplay=1&mute=0"
            style={{
              width: '100%',
              height: '100%',
              border: 'none',
              display: 'block',
            }}
            allowFullScreen
            allow="autoplay; fullscreen; encrypted-media"
            title="SVT Nyheter Live"
          />
        </div>
      </div>

      {/* Right: headlines */}
      <div style={{
        flex: 1,
        display: 'flex',
        flexDirection: 'column',
        overflow: 'hidden',
      }}>
        <div style={{
          padding: '12px 16px',
          display: 'flex',
          justifyContent: 'space-between',
          alignItems: 'center',
          borderBottom: '1px solid rgba(0,100,200,0.12)',
          flexShrink: 0,
        }}>
          <div style={{
            fontFamily: "'Share Tech Mono', monospace",
            fontSize: 12,
            letterSpacing: 3,
            color: '#e8f4ff',
          }}>NYHETER</div>
          {lastUpdated && (
            <div style={{
              fontFamily: "'Rajdhani', sans-serif",
              fontSize: 10,
              letterSpacing: 2,
              color: 'rgba(100,160,220,0.35)',
            }}>{lastUpdated.toLocaleTimeString()}</div>
          )}
        </div>

        <div style={{
          flex: 1,
          overflowY: 'auto',
          padding: '0 16px',
          scrollbarWidth: 'thin',
          scrollbarColor: 'rgba(80,160,255,0.2) transparent',
        }}>
          {loading ? (
            <div style={{
              display: 'flex', alignItems: 'center', justifyContent: 'center',
              height: 120, fontFamily: "'Rajdhani', sans-serif",
              fontSize: 12, letterSpacing: 4, color: 'rgba(100,160,220,0.4)',
            }}>HÄMTAR NYHETER...</div>
          ) : (
            articles.map((a, i) => <HeadlineRow key={i} {...a} />)
          )}
        </div>
      </div>
    </div>
  )
}
