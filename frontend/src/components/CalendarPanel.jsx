import { useState, useEffect } from 'react'

const raj  = { fontFamily: "'Rajdhani', sans-serif" }
const mono = { fontFamily: "'Share Tech Mono', monospace" }

const DAY_LABELS = ['Today', 'Tomorrow', '3 Days', 'This Week']
const DAY_VALUES = [1, 2, 3, 7]

function parseTime(iso) {
  if (!iso) return null
  try { return new Date(iso) } catch { return null }
}

function fmtTime(dt) {
  if (!dt) return ''
  return dt.toLocaleTimeString('sv-SE', { hour: '2-digit', minute: '2-digit' })
}

function fmtDate(dt) {
  if (!dt) return ''
  return dt.toLocaleDateString('sv-SE', { weekday: 'short', month: 'short', day: 'numeric' })
}

function isToday(dt) {
  if (!dt) return false
  const now = new Date()
  return dt.getDate() === now.getDate() &&
         dt.getMonth() === now.getMonth() &&
         dt.getFullYear() === now.getFullYear()
}

function EventCard({ ev, index }) {
  const start = parseTime(ev.start)
  const end   = parseTime(ev.end)
  const now   = new Date()
  const isNow = start && end && start <= now && now <= end
  const isPast = end && end < now

  return (
    <div style={{
      display: 'flex', gap: 14, alignItems: 'flex-start',
      padding: '12px 0',
      borderBottom: '1px solid rgba(79,195,247,0.07)',
      opacity: isPast ? 0.4 : 1,
      transition: 'opacity 0.3s',
    }}>
      {/* Time column */}
      <div style={{ width: 52, flexShrink: 0, paddingTop: 2 }}>
        {ev.all_day ? (
          <div style={{ ...raj, fontSize: 8, letterSpacing: 3, color: 'rgba(79,195,247,0.4)' }}>ALL DAY</div>
        ) : (
          <>
            <div style={{ ...mono, fontSize: 13, color: isNow ? '#4fc3f7' : 'rgba(168,216,240,0.8)', lineHeight: 1.2 }}>
              {fmtTime(start)}
            </div>
            {end && (
              <div style={{ ...mono, fontSize: 9, color: 'rgba(100,160,200,0.35)', marginTop: 2 }}>
                {fmtTime(end)}
              </div>
            )}
          </>
        )}
      </div>

      {/* Active indicator */}
      <div style={{
        width: 2, alignSelf: 'stretch', flexShrink: 0, borderRadius: 1,
        background: isNow
          ? '#4fc3f7'
          : isPast
          ? 'rgba(79,195,247,0.1)'
          : 'rgba(79,195,247,0.25)',
        boxShadow: isNow ? '0 0 8px rgba(79,195,247,0.6)' : 'none',
        transition: 'all 0.3s',
      }} />

      {/* Event details */}
      <div style={{ flex: 1, minWidth: 0 }}>
        <div style={{
          ...raj, fontSize: 14, fontWeight: 600, letterSpacing: 1,
          color: isNow ? '#e8f4ff' : 'rgba(220,235,250,0.85)',
          whiteSpace: 'nowrap', overflow: 'hidden', textOverflow: 'ellipsis',
        }}>
          {ev.title}
        </div>
        {!isToday(start) && (
          <div style={{ ...mono, fontSize: 9, color: 'rgba(79,195,247,0.4)', marginTop: 2 }}>
            {fmtDate(start)}
          </div>
        )}
        {ev.location && (
          <div style={{ ...mono, fontSize: 9, color: 'rgba(100,160,200,0.4)', marginTop: 2,
            whiteSpace: 'nowrap', overflow: 'hidden', textOverflow: 'ellipsis' }}>
            ◎ {ev.location}
          </div>
        )}
        {ev.meet_url && (
          <div style={{ ...mono, fontSize: 9, color: 'rgba(79,195,247,0.5)', marginTop: 3 }}>
            ⬡ MEET
          </div>
        )}
        {isNow && (
          <div style={{
            display: 'inline-block', marginTop: 4,
            ...raj, fontSize: 7, letterSpacing: 3,
            color: '#4fc3f7', border: '1px solid rgba(79,195,247,0.4)',
            borderRadius: 2, padding: '1px 6px',
          }}>
            IN PROGRESS
          </div>
        )}
      </div>
    </div>
  )
}

export default function CalendarPanel() {
  const [events,  setEvents]  = useState([])
  const [loading, setLoading] = useState(true)
  const [error,   setError]   = useState(null)
  const [days,    setDays]    = useState(1)

  useEffect(() => {
    setLoading(true)
    fetch(`http://localhost:8000/api/calendar?days=${days}`)
      .then(r => r.json())
      .then(d => {
        setEvents(d.events || [])
        setError(d.error || null)
        setLoading(false)
      })
      .catch(() => { setError('offline'); setLoading(false) })
  }, [days])

  // Auto-refresh every 60s
  useEffect(() => {
    const id = setInterval(() => {
      fetch(`http://localhost:8000/api/calendar?days=${days}`)
        .then(r => r.json())
        .then(d => { setEvents(d.events || []); setError(d.error || null) })
        .catch(() => {})
    }, 60_000)
    return () => clearInterval(id)
  }, [days])

  const now = new Date()
  const dateLabel = now.toLocaleDateString('sv-SE', { weekday: 'long', month: 'long', day: 'numeric' })

  return (
    <div style={{ height: '100%', display: 'flex', flexDirection: 'column', overflow: 'hidden' }}>

      {/* ── Header ── */}
      <div style={{
        padding: '18px 24px 12px',
        borderBottom: '1px solid rgba(79,195,247,0.1)',
        flexShrink: 0,
      }}>
        <div style={{ ...raj, fontSize: 8, letterSpacing: 5, color: 'rgba(79,195,247,0.35)', marginBottom: 6 }}>
          CALENDAR
        </div>
        <div style={{ ...mono, fontSize: 20, color: '#c8e8ff', letterSpacing: 1 }}>
          {dateLabel.toUpperCase()}
        </div>

        {/* Day range tabs */}
        <div style={{ display: 'flex', gap: 8, marginTop: 14 }}>
          {DAY_LABELS.map((label, i) => (
            <button key={i}
              onClick={() => setDays(DAY_VALUES[i])}
              style={{
                background: days === DAY_VALUES[i] ? 'rgba(79,195,247,0.12)' : 'none',
                border: `1px solid ${days === DAY_VALUES[i] ? 'rgba(79,195,247,0.4)' : 'rgba(79,195,247,0.12)'}`,
                borderRadius: 4, padding: '4px 12px',
                ...raj, fontSize: 9, letterSpacing: 3,
                color: days === DAY_VALUES[i] ? '#4fc3f7' : 'rgba(79,195,247,0.35)',
                cursor: 'pointer', transition: 'all 0.2s',
              }}>
              {label}
            </button>
          ))}
        </div>
      </div>

      {/* ── Events list ── */}
      <div style={{ flex: 1, overflowY: 'auto', padding: '0 24px' }}>
        {loading ? (
          <div style={{ padding: 40, textAlign: 'center', ...mono, fontSize: 10, color: 'rgba(79,195,247,0.25)', letterSpacing: 3 }}>
            LOADING...
          </div>
        ) : error === 'credentials_missing' ? (
          <div style={{ padding: 40, display: 'flex', flexDirection: 'column', gap: 12, alignItems: 'center' }}>
            <div style={{ ...raj, fontSize: 11, letterSpacing: 4, color: 'rgba(79,195,247,0.4)' }}>
              CALENDAR NOT CONFIGURED
            </div>
            <div style={{ ...mono, fontSize: 10, color: 'rgba(79,195,247,0.25)', textAlign: 'center', lineHeight: 2 }}>
              Add credentials.json to the JARVIS root<br />
              from Google Cloud Console
            </div>
          </div>
        ) : events.length === 0 ? (
          <div style={{ padding: 40, textAlign: 'center' }}>
            <div style={{ ...raj, fontSize: 11, letterSpacing: 4, color: 'rgba(79,195,247,0.25)' }}>
              NOTHING SCHEDULED
            </div>
            <div style={{ ...mono, fontSize: 9, color: 'rgba(79,195,247,0.15)', marginTop: 8 }}>
              say "jarvis schedule a meeting..."
            </div>
          </div>
        ) : (
          <div style={{ paddingTop: 8 }}>
            {events.map((ev, i) => <EventCard key={ev.id || i} ev={ev} index={i} />)}
          </div>
        )}
      </div>

      {/* ── Footer hint ── */}
      <div style={{
        padding: '10px 24px',
        borderTop: '1px solid rgba(79,195,247,0.06)',
        ...mono, fontSize: 8, letterSpacing: 2,
        color: 'rgba(79,195,247,0.18)',
        flexShrink: 0,
      }}>
        "JARVIS SCHEDULE A MEETING..."  ·  "JARVIS WHAT'S ON TODAY?"
      </div>
    </div>
  )
}
