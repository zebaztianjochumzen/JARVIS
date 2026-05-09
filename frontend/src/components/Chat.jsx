import { useState, useRef, useEffect } from 'react'

function timestamp() {
  const d = new Date()
  return `${String(d.getHours()).padStart(2,'0')}:${String(d.getMinutes()).padStart(2,'0')}:${String(d.getSeconds()).padStart(2,'0')}`
}

export default function Chat({ messages, onSend, thinking }) {
  const [input, setInput]   = useState('')
  const bottomRef           = useRef(null)
  const inputRef            = useRef(null)

  useEffect(() => { bottomRef.current?.scrollIntoView({ behavior: 'smooth' }) }, [messages])
  useEffect(() => { inputRef.current?.focus() }, [])

  function handleSubmit(e) {
    e.preventDefault()
    const text = input.trim()
    if (!text || thinking) return
    setInput('')
    onSend(text)
  }

  return (
    <div style={{ display: 'flex', flexDirection: 'column', height: '100%', padding: '20px 28px' }}>
      <div style={{
        flex: 1, overflowY: 'auto', display: 'flex', flexDirection: 'column', gap: 14,
        paddingRight: 6, scrollbarWidth: 'thin', scrollbarColor: 'rgba(80,160,255,0.2) transparent',
      }}>
        {messages.map((msg, i) => (
          <div key={i} style={{ display: 'flex', flexDirection: 'column', alignItems: msg.role === 'user' ? 'flex-end' : 'flex-start' }}>
            <div style={{ display: 'flex', alignItems: 'center', gap: 8, marginBottom: 3 }}>
              <span style={{ fontSize: 9, letterSpacing: 3, color: 'rgba(100,160,220,0.5)', fontFamily: "'Rajdhani', sans-serif" }}>
                {msg.role === 'user' ? 'YOU' : 'JARVIS'}
              </span>
              <span style={{ fontFamily: "'Share Tech Mono', monospace", fontSize: 9, color: 'rgba(100,160,220,0.3)' }}>
                {msg.ts || ''}
              </span>
            </div>
            <div style={{
              maxWidth: '75%', padding: '10px 15px',
              borderRadius: msg.role === 'user' ? '12px 12px 2px 12px' : '12px 12px 12px 2px',
              background: msg.role === 'user' ? 'rgba(0,120,200,0.15)' : 'rgba(255,255,255,0.04)',
              border: msg.role === 'user' ? '1px solid rgba(0,140,255,0.25)' : '1px solid rgba(255,255,255,0.07)',
              color: msg.role === 'user' ? 'rgba(200,230,255,0.9)' : 'rgba(230,240,255,0.85)',
              fontFamily: "'Rajdhani', sans-serif", fontSize: 15, lineHeight: 1.5,
              letterSpacing: 0.4, whiteSpace: 'pre-wrap',
            }}>
              {msg.content}
            </div>
          </div>
        ))}

        {thinking && (
          <div style={{ display: 'flex', flexDirection: 'column', alignItems: 'flex-start' }}>
            <div style={{ fontSize: 9, letterSpacing: 3, color: 'rgba(100,160,220,0.5)', marginBottom: 3, fontFamily: "'Rajdhani'" }}>JARVIS</div>
            <div style={{ padding: '10px 16px', borderRadius: '12px 12px 12px 2px', background: 'rgba(255,255,255,0.04)', border: '1px solid rgba(255,255,255,0.07)', display: 'flex', gap: 6, alignItems: 'center' }}>
              {[0,1,2].map(i => (
                <span key={i} style={{ width: 6, height: 6, borderRadius: '50%', background: 'rgba(80,180,255,0.7)', animation: `dot-bounce 1.2s ease-in-out ${i*0.2}s infinite` }} />
              ))}
            </div>
          </div>
        )}
        <div ref={bottomRef} />
      </div>

      <form onSubmit={handleSubmit} style={{ marginTop: 16, display: 'flex', gap: 10 }}>
        <input
          ref={inputRef}
          value={input}
          onChange={e => setInput(e.target.value)}
          placeholder="Speak to JARVIS..."
          disabled={thinking}
          style={{
            flex: 1, background: 'rgba(255,255,255,0.04)',
            border: '1px solid rgba(0,140,255,0.25)', borderRadius: 8,
            padding: '11px 16px', color: '#e8f4ff',
            fontFamily: "'Rajdhani', sans-serif", fontSize: 15, letterSpacing: 1, outline: 'none',
          }}
        />
        <button type="submit" disabled={thinking || !input.trim()} style={{
          background: 'rgba(0,120,220,0.3)', border: '1px solid rgba(0,140,255,0.4)',
          borderRadius: 8, padding: '11px 20px', color: '#80c8ff',
          fontFamily: "'Rajdhani', sans-serif", fontSize: 13, letterSpacing: 3, cursor: 'pointer',
        }}>SEND</button>
      </form>

      <style>{`
        @keyframes dot-bounce {
          0%,80%,100% { transform:translateY(0); opacity:0.5; }
          40% { transform:translateY(-6px); opacity:1; }
        }
      `}</style>
    </div>
  )
}

export { timestamp }
