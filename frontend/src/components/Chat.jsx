import { useState, useRef, useEffect } from 'react'

export default function Chat({ messages, onSend, thinking }) {
  const [input, setInput] = useState('')
  const bottomRef = useRef(null)
  const inputRef = useRef(null)

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: 'smooth' })
  }, [messages])

  useEffect(() => {
    inputRef.current?.focus()
  }, [])

  function handleSubmit(e) {
    e.preventDefault()
    const text = input.trim()
    if (!text || thinking) return
    setInput('')
    onSend(text)
  }

  return (
    <div style={{
      display: 'flex',
      flexDirection: 'column',
      height: '100%',
      padding: '24px 32px',
    }}>
      {/* Messages */}
      <div style={{
        flex: 1,
        overflowY: 'auto',
        display: 'flex',
        flexDirection: 'column',
        gap: 16,
        paddingRight: 8,
        scrollbarWidth: 'thin',
        scrollbarColor: 'rgba(80,160,255,0.2) transparent',
      }}>
        {messages.map((msg, i) => (
          <div key={i} style={{
            display: 'flex',
            flexDirection: 'column',
            alignItems: msg.role === 'user' ? 'flex-end' : 'flex-start',
          }}>
            <div style={{
              fontSize: 10,
              letterSpacing: 3,
              color: 'rgba(100,160,220,0.5)',
              marginBottom: 4,
              fontFamily: "'Rajdhani', sans-serif",
            }}>
              {msg.role === 'user' ? 'YOU' : 'JARVIS'}
            </div>
            <div style={{
              maxWidth: '72%',
              padding: '10px 16px',
              borderRadius: msg.role === 'user' ? '12px 12px 2px 12px' : '12px 12px 12px 2px',
              background: msg.role === 'user'
                ? 'rgba(0, 120, 200, 0.15)'
                : 'rgba(255, 255, 255, 0.04)',
              border: msg.role === 'user'
                ? '1px solid rgba(0, 140, 255, 0.25)'
                : '1px solid rgba(255, 255, 255, 0.07)',
              color: msg.role === 'user' ? 'rgba(200,230,255,0.9)' : 'rgba(230,240,255,0.85)',
              fontFamily: "'Rajdhani', sans-serif",
              fontSize: 16,
              lineHeight: 1.5,
              letterSpacing: 0.5,
              whiteSpace: 'pre-wrap',
            }}>
              {msg.content}
            </div>
          </div>
        ))}

        {thinking && (
          <div style={{ display: 'flex', flexDirection: 'column', alignItems: 'flex-start' }}>
            <div style={{
              fontSize: 10, letterSpacing: 3,
              color: 'rgba(100,160,220,0.5)', marginBottom: 4,
              fontFamily: "'Rajdhani', sans-serif",
            }}>JARVIS</div>
            <div style={{
              padding: '10px 16px',
              borderRadius: '12px 12px 12px 2px',
              background: 'rgba(255,255,255,0.04)',
              border: '1px solid rgba(255,255,255,0.07)',
              display: 'flex', gap: 6, alignItems: 'center',
            }}>
              {[0, 1, 2].map(i => (
                <span key={i} style={{
                  width: 6, height: 6, borderRadius: '50%',
                  background: 'rgba(80,180,255,0.7)',
                  animation: `dot-bounce 1.2s ease-in-out ${i * 0.2}s infinite`,
                }} />
              ))}
            </div>
          </div>
        )}
        <div ref={bottomRef} />
      </div>

      {/* Input */}
      <form onSubmit={handleSubmit} style={{ marginTop: 20, display: 'flex', gap: 10 }}>
        <input
          ref={inputRef}
          value={input}
          onChange={e => setInput(e.target.value)}
          placeholder="Speak to JARVIS..."
          disabled={thinking}
          style={{
            flex: 1,
            background: 'rgba(255,255,255,0.04)',
            border: '1px solid rgba(0,140,255,0.25)',
            borderRadius: 8,
            padding: '12px 16px',
            color: '#e8f4ff',
            fontFamily: "'Rajdhani', sans-serif",
            fontSize: 16,
            letterSpacing: 1,
            outline: 'none',
          }}
        />
        <button
          type="submit"
          disabled={thinking || !input.trim()}
          style={{
            background: thinking ? 'rgba(0,80,160,0.2)' : 'rgba(0,120,220,0.3)',
            border: '1px solid rgba(0,140,255,0.4)',
            borderRadius: 8,
            padding: '12px 20px',
            color: '#80c8ff',
            fontFamily: "'Rajdhani', sans-serif",
            fontSize: 14,
            letterSpacing: 3,
            cursor: thinking ? 'default' : 'pointer',
            transition: 'background 0.2s',
          }}
        >
          SEND
        </button>
      </form>

      <style>{`
        @keyframes dot-bounce {
          0%, 80%, 100% { transform: translateY(0); opacity: 0.5; }
          40% { transform: translateY(-6px); opacity: 1; }
        }
      `}</style>
    </div>
  )
}
