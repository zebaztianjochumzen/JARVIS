import { useState, useEffect } from 'react'

const LINES = [
  { text: 'J.A.R.V.I.S  —  ADVANCED AI SYSTEM  v4.0', delay: 0,    highlight: true },
  { text: '──────────────────────────────────────────────', delay: 300,  dim: true },
  { text: '▶  NEURAL INFERENCE CORE ........... ONLINE',  delay: 700,  ok: true },
  { text: '▶  PERSISTENT MEMORY LAYER ......... ONLINE',  delay: 1050, ok: true },
  { text: '▶  TOOL REGISTRY (47 TOOLS) ........ ONLINE',  delay: 1380, ok: true },
  { text: '▶  VOICE + WHISPER STT ............. ONLINE',  delay: 1690, ok: true },
  { text: '▶  PLAYWRIGHT BROWSER .............. ONLINE',  delay: 1970, ok: true },
  { text: '▶  MCP PROTOCOL BRIDGE ............. ONLINE',  delay: 2230, ok: true },
  { text: '▶  TELEGRAM REACH CHANNEL .......... ONLINE',  delay: 2470, ok: true },
  { text: '──────────────────────────────────────────────', delay: 2750, dim: true },
  { text: 'ALL SYSTEMS NOMINAL — GOOD MORNING, SIR.',     delay: 2950, final: true },
]

const TOTAL_MS = 2950 + 800   // last line delay + dwell
const FADE_MS  = TOTAL_MS + 200
const DONE_MS  = FADE_MS  + 700

export default function BootSequence({ onComplete }) {
  const [shown,  setShown]  = useState([])
  const [fading, setFading] = useState(false)
  const [gone,   setGone]   = useState(false)

  useEffect(() => {
    if (sessionStorage.getItem('jarvis_booted')) {
      setGone(true)
      onComplete?.()
      return
    }
    sessionStorage.setItem('jarvis_booted', '1')

    const timers = []
    LINES.forEach((_, i) => {
      timers.push(setTimeout(() => setShown(p => [...p, i]), LINES[i].delay))
    })
    timers.push(setTimeout(() => setFading(true), FADE_MS))
    timers.push(setTimeout(() => { setGone(true); onComplete?.() }, DONE_MS))
    return () => timers.forEach(clearTimeout)
  }, [])  // eslint-disable-line react-hooks/exhaustive-deps

  if (gone) return null

  return (
    <div style={{
      position:   'fixed', inset: 0,
      background: '#070b14',
      display:    'flex', alignItems: 'center', justifyContent: 'center',
      zIndex:     99999,
      opacity:    fading ? 0 : 1,
      transition: 'opacity 0.65s ease',
    }}>
      {/* corner brackets */}
      {['tl','tr','bl','br'].map(c => (
        <div key={c} style={{
          position: 'absolute',
          width: 32, height: 32,
          top:    c[0]==='t' ? 20  : undefined,
          bottom: c[0]==='b' ? 20  : undefined,
          left:   c[1]==='l' ? 20  : undefined,
          right:  c[1]==='r' ? 20  : undefined,
          borderTop:    c[0]==='t' ? '2px solid rgba(80,180,255,0.5)' : undefined,
          borderBottom: c[0]==='b' ? '2px solid rgba(80,180,255,0.5)' : undefined,
          borderLeft:   c[1]==='l' ? '2px solid rgba(80,180,255,0.5)' : undefined,
          borderRight:  c[1]==='r' ? '2px solid rgba(80,180,255,0.5)' : undefined,
        }} />
      ))}

      <div style={{ fontFamily: "'Share Tech Mono', monospace", minWidth: 460 }}>
        {LINES.map((line, i) => (
          <div key={i} style={{
            marginBottom:   line.dim ? 4 : 7,
            opacity:        shown.includes(i) ? 1 : 0,
            transform:      shown.includes(i) ? 'translateX(0)' : 'translateX(-8px)',
            transition:     'opacity 0.35s ease, transform 0.35s ease',
            fontSize:       line.final ? 15 : line.highlight ? 14 : 12,
            letterSpacing:  line.final ? 5 : line.highlight ? 4 : 1,
            color: line.final
              ? '#7ef7ff'
              : line.highlight
                ? 'rgba(100,210,255,0.95)'
                : line.dim
                  ? 'rgba(80,180,255,0.28)'
                  : 'rgba(80,200,255,0.75)',
            textShadow: (line.final || line.highlight)
              ? '0 0 20px rgba(80,180,255,0.6)'
              : 'none',
          }}>
            {line.text}
            {line.ok && (
              <span style={{ color: '#4ade80', textShadow: '0 0 8px #4ade80', marginLeft: 0 }}>
                {/* already embedded in the text */}
              </span>
            )}
          </div>
        ))}
      </div>
    </div>
  )
}
