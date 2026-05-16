import { useEffect, useRef, useState } from 'react'

const mono = { fontFamily: "'Share Tech Mono', monospace" }

export default function ChatWidget({ messages, thinking, onSend }) {
  const [input,   setInput]   = useState('')
  const bottomRef             = useRef(null)

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: 'smooth' })
  }, [messages, thinking])

  function submit(e) {
    e?.preventDefault()
    const text = input.trim()
    if (!text || thinking) return
    setInput('')
    onSend(text)
  }

  return (
    <div style={{ display: 'flex', flexDirection: 'column', height: 320 }}>

      {/* ── Message log ── */}
      <div style={{
        flex: 1, overflowY: 'auto',
        padding: '10px 12px 6px',
        display: 'flex', flexDirection: 'column', gap: 2,
        scrollbarWidth: 'thin',
        scrollbarColor: 'rgba(0,212,255,0.12) transparent',
      }}>
        {messages.map((msg, i) => {
          const isUser   = msg.role === 'user'
          const isSystem = msg.role === 'system'
          const isLast   = i === messages.length - 1

          return (
            <div key={i} style={{
              ...mono,
              fontSize: 11,
              lineHeight: 1.65,
              color: isUser
                ? 'rgba(210, 228, 255, 0.88)'
                : isSystem
                ? 'rgba(0, 180, 255, 0.42)'
                : 'rgba(0, 212, 255, 0.92)',
              fontStyle: isSystem ? 'italic' : 'normal',
              wordBreak: 'break-word',
            }}>
              <span style={{
                color: isUser ? 'rgba(120,150,190,0.5)' : 'rgba(0,212,255,0.38)',
                marginRight: 6,
              }}>
                {isUser ? '$' : '>'}
              </span>
              {msg.content}
              {/* Blinking cursor on last JARVIS line while idle */}
              {isLast && !isUser && !isSystem && !thinking && (
                <span style={{ animation: 'cur-blink 1.1s step-end infinite', marginLeft: 1 }}>▌</span>
              )}
            </div>
          )
        })}

        {/* Thinking indicator */}
        {thinking && (
          <div style={{ ...mono, fontSize: 11, color: 'rgba(0,212,255,0.38)' }}>
            <span style={{ marginRight: 6 }}>{'>'}</span>
            <span style={{ animation: 'cur-blink 0.65s step-end infinite' }}>_</span>
          </div>
        )}

        <div ref={bottomRef} />
      </div>

      {/* ── Input area ── */}
      <div style={{
        borderTop: '1px solid rgba(0,212,255,0.11)',
        padding: '7px 10px 5px',
        flexShrink: 0,
      }}>
        <form onSubmit={submit}>
          <input
            value={input}
            onChange={e => setInput(e.target.value)}
            placeholder="> enter message..."
            disabled={thinking}
            style={{
              width: '100%', boxSizing: 'border-box',
              background: 'rgba(0, 8, 24, 0.6)',
              border: '1px solid rgba(0,212,255,0.14)',
              borderRadius: 3,
              padding: '5px 9px',
              color: 'rgba(210,228,255,0.88)',
              ...mono, fontSize: 11,
              outline: 'none',
              caretColor: '#00d4ff',
            }}
          />
        </form>
        <div style={{ display: 'flex', justifyContent: 'space-between', marginTop: 5 }}>
          <button
            type="button"
            style={{
              background: 'none', border: 'none', cursor: 'pointer',
              ...mono, fontSize: 9,
              color: 'rgba(0,212,255,0.35)',
              padding: '1px 0',
            }}
          >
            [+ img]
          </button>
          <button
            type="button"
            onClick={submit}
            disabled={!input.trim() || thinking}
            style={{
              background: 'none', border: 'none', cursor: 'pointer',
              ...mono, fontSize: 9,
              color: input.trim() && !thinking
                ? 'rgba(0,212,255,0.72)'
                : 'rgba(0,212,255,0.22)',
              padding: '1px 0',
              transition: 'color 0.1s',
            }}
          >
            [send ↵]
          </button>
        </div>
      </div>

      <style>{`
        @keyframes cur-blink {
          0%, 100% { opacity: 1; }
          50%       { opacity: 0; }
        }
      `}</style>
    </div>
  )
}
