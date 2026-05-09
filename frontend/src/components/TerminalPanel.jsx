import { useEffect, useRef } from 'react'

export default function TerminalPanel({ logs }) {
  const bottomRef = useRef(null)
  useEffect(() => { bottomRef.current?.scrollIntoView({ behavior: 'smooth' }) }, [logs])

  return (
    <div style={{ height: '100%', display: 'flex', flexDirection: 'column', background: '#050810' }}>
      <div style={{
        padding: '10px 20px', borderBottom: '1px solid rgba(0,180,80,0.2)',
        fontFamily: "'Share Tech Mono', monospace", fontSize: 12, letterSpacing: 3, color: '#4ade80',
        display: 'flex', justifyContent: 'space-between',
      }}>
        <span>◉ TERMINAL</span>
        <span style={{ color: 'rgba(100,160,220,0.4)', fontSize: 10 }}>{logs.length} EVENTS</span>
      </div>

      <div style={{
        flex: 1, overflowY: 'auto', padding: '16px 20px',
        fontFamily: "'Share Tech Mono', monospace", fontSize: 12,
        scrollbarWidth: 'thin', scrollbarColor: 'rgba(0,180,80,0.2) transparent',
      }}>
        {logs.length === 0 ? (
          <div style={{ color: 'rgba(0,180,80,0.3)', letterSpacing: 2 }}>
            JARVIS@system:~$ <span style={{ animation: 'blink 1s step-end infinite' }}>_</span>
            <br /><br />
            <span style={{ color: 'rgba(0,180,80,0.2)' }}>Waiting for tool activity...</span>
          </div>
        ) : (
          logs.map((log, i) => (
            <div key={i} style={{ marginBottom: 16 }}>
              <div style={{ color: 'rgba(0,180,80,0.5)', fontSize: 10, marginBottom: 4 }}>
                [{log.ts}] TOOL CALL — {log.tool.toUpperCase()}
              </div>
              <div style={{ color: '#4ade80' }}>
                $ {log.tool}({Object.entries(log.input || {}).map(([k,v]) => `${k}="${v}"`).join(', ')})
              </div>
              <div style={{ color: 'rgba(200,240,200,0.7)', marginTop: 4, paddingLeft: 12, borderLeft: '2px solid rgba(0,180,80,0.3)', whiteSpace: 'pre-wrap', wordBreak: 'break-word' }}>
                {log.result}
              </div>
            </div>
          ))
        )}
        <div ref={bottomRef} />
      </div>

      <style>{`
        @keyframes blink { 0%,100% { opacity:1; } 50% { opacity:0; } }
      `}</style>
    </div>
  )
}
