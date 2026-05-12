import { useState, useEffect, useRef } from 'react'

const ICONS = {
  web_search:            '🔍',
  get_news:              '📰',
  get_weather:           '🌤',
  get_stock_price:       '📈',
  get_market_summary:    '📊',
  get_system_vitals:     '🖥',
  remember_this:         '🧠',
  recall_fact:           '💭',
  recall_semantic:       '🔎',
  forget_fact:           '🗑',
  save_note:             '📝',
  browser_navigate:      '🌐',
  browser_screenshot:    '📸',
  browser_execute_js:    '⚙',
  browser_click:         '🖱',
  browser_fill:          '✏',
  browser_extract_text:  '📋',
  send_telegram:         '📨',
  gmail_triage:          '📧',
  read_gmail_inbox:      '📥',
  search_gmail:          '📨',
  get_calendar_events:   '📅',
  create_calendar_event: '📆',
  delete_calendar_event: '🗓',
  show_calendar:         '📅',
  run_shell:             '💻',
  read_file:             '📂',
  write_file:            '💾',
  search_codebase:       '🔬',
  git_status:            '🌿',
  run_tests:             '🧪',
  set_timer:             '⏱',
  take_screenshot:       '📷',
  plan_route:            '🗺',
  show_location:         '📍',
  search_nearby:         '📌',
  look_at_desk:          '👁',
  play_music:            '🎵',
  set_volume:            '🔊',
  translate:             '🌐',
  draft_email:           '📮',
  create_document:       '📄',
  write_code:            '💡',
}

const CARD_TTL  = 4200   // ms visible
const FADE_MS   = 400    // exit animation

function ToolCard({ log, onDone }) {
  const [phase, setPhase] = useState('entering')  // entering | visible | leaving

  useEffect(() => {
    const t1 = setTimeout(() => setPhase('visible'), 20)
    const t2 = setTimeout(() => setPhase('leaving'), CARD_TTL)
    const t3 = setTimeout(() => onDone(), CARD_TTL + FADE_MS)
    return () => { clearTimeout(t1); clearTimeout(t2); clearTimeout(t3) }
  }, [])  // eslint-disable-line react-hooks/exhaustive-deps

  const icon   = ICONS[log.tool] || '⚡'
  const name   = (log.tool || '').replace(/_/g, ' ').toUpperCase()
  const result = typeof log.result === 'string' ? log.result : ''
  const snippet = result.length > 110 ? result.slice(0, 110) + '…' : result

  const isEntering = phase === 'entering'
  const isLeaving  = phase === 'leaving'

  return (
    <div style={{
      marginBottom:   8,
      transform:      isEntering || isLeaving ? 'translateX(110%)' : 'translateX(0)',
      opacity:        isEntering || isLeaving ? 0 : 1,
      transition:     isLeaving
        ? `transform ${FADE_MS}ms ease, opacity ${FADE_MS}ms ease`
        : 'transform 0.32s cubic-bezier(0.34,1.56,0.64,1), opacity 0.32s ease',
      background:     'rgba(7,11,20,0.9)',
      border:         '1px solid rgba(80,180,255,0.2)',
      borderLeft:     '3px solid rgba(80,180,255,0.65)',
      borderRadius:   7,
      padding:        '8px 12px',
      maxWidth:       260,
      backdropFilter: 'blur(10px)',
      boxShadow:      '0 4px 24px rgba(0,0,0,0.4)',
    }}>
      {/* header row */}
      <div style={{ display: 'flex', alignItems: 'center', gap: 6, marginBottom: snippet ? 5 : 0 }}>
        <span style={{ fontSize: 13, lineHeight: 1 }}>{icon}</span>
        <span style={{
          fontFamily:    "'Share Tech Mono',monospace",
          fontSize:      9.5,
          color:         'rgba(80,200,255,0.9)',
          letterSpacing: 1,
          flex:          1,
        }}>
          {name}
        </span>
        <span style={{
          fontFamily: "'Share Tech Mono',monospace",
          fontSize:    8,
          color:       'rgba(255,255,255,0.28)',
          whiteSpace:  'nowrap',
        }}>
          {log.ts}
        </span>
      </div>

      {/* result snippet */}
      {snippet && (
        <div style={{
          fontFamily:  "'Share Tech Mono',monospace",
          fontSize:    8.5,
          color:       'rgba(255,255,255,0.38)',
          lineHeight:  1.45,
          overflow:    'hidden',
          display:     '-webkit-box',
          WebkitLineClamp: 2,
          WebkitBoxOrient: 'vertical',
        }}>
          {snippet}
        </div>
      )}

      {/* progress bar that drains over CARD_TTL */}
      <div style={{
        marginTop:  6,
        height:     1.5,
        background: 'rgba(80,180,255,0.12)',
        borderRadius: 1,
        overflow:   'hidden',
      }}>
        <div style={{
          height:     '100%',
          background: 'rgba(80,180,255,0.45)',
          width:      phase === 'visible' ? '0%' : '100%',
          transition: phase === 'visible' ? `width ${CARD_TTL}ms linear` : 'none',
          transformOrigin: 'right',
        }} />
      </div>
    </div>
  )
}

export default function ToolTheater({ logs }) {
  const [cards, setCards] = useState([])
  const seenRef = useRef(0)

  useEffect(() => {
    if (logs.length <= seenRef.current) return
    const newLogs = logs.slice(seenRef.current)
    seenRef.current = logs.length
    newLogs.forEach(log => {
      const id = `${log.tool}-${log.ts}-${Math.random().toString(36).slice(2)}`
      setCards(prev => [...prev.slice(-4), { id, log }])
    })
  }, [logs])

  const remove = (id) => setCards(p => p.filter(c => c.id !== id))

  if (!cards.length) return null

  return (
    <div style={{
      position:       'fixed',
      right:          18,
      bottom:         130,
      display:        'flex',
      flexDirection:  'column-reverse',
      zIndex:         700,
      pointerEvents:  'none',
    }}>
      {cards.map(({ id, log }) => (
        <ToolCard key={id} log={log} onDone={() => remove(id)} />
      ))}
    </div>
  )
}
