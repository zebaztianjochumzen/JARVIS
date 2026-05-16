import { useEffect, useRef, useState } from 'react'

export default function WidgetShell({
  title,
  width = 300,
  defaultX = 80,
  defaultY = 120,
  open,
  onClose,
  children,
}) {
  const [pos,     setPos]     = useState({ x: defaultX, y: defaultY })
  const [mounted, setMounted] = useState(false)
  const [visible, setVisible] = useState(false)

  const dragging = useRef(false)
  const offset   = useRef({ x: 0, y: 0 })

  // Mount before fade-in, unmount after fade-out
  useEffect(() => {
    if (open) {
      setMounted(true)
      const id = requestAnimationFrame(() => setVisible(true))
      return () => cancelAnimationFrame(id)
    } else {
      setVisible(false)
      const t = setTimeout(() => setMounted(false), 160)
      return () => clearTimeout(t)
    }
  }, [open])

  // Drag: track offset on header mousedown, update pos on window mousemove
  function onHeaderDown(e) {
    dragging.current = true
    offset.current   = { x: e.clientX - pos.x, y: e.clientY - pos.y }
    e.preventDefault()
  }

  useEffect(() => {
    function onMove(e) {
      if (!dragging.current) return
      setPos({ x: e.clientX - offset.current.x, y: e.clientY - offset.current.y })
    }
    function onUp() { dragging.current = false }
    window.addEventListener('mousemove', onMove)
    window.addEventListener('mouseup',   onUp)
    return () => {
      window.removeEventListener('mousemove', onMove)
      window.removeEventListener('mouseup',   onUp)
    }
  }, [])

  if (!mounted) return null

  return (
    <div style={{
      position: 'fixed',
      left: pos.x,
      top:  pos.y,
      width,
      zIndex: 600,
      opacity:   visible ? 1 : 0,
      transform: `scale(${visible ? 1 : 0.95})`,
      transformOrigin: 'top left',
      transition: 'opacity 0.15s ease-out, transform 0.15s ease-out',
      pointerEvents: visible ? 'all' : 'none',
      background:    'rgba(10, 22, 40, 0.88)',
      backdropFilter: 'blur(8px)',
      border:    '1px solid rgba(0, 212, 255, 0.35)',
      borderRadius: 6,
      display:   'flex',
      flexDirection: 'column',
      overflow:  'hidden',
      boxShadow: '0 12px 40px rgba(0, 0, 0, 0.65), 0 0 0 1px rgba(0, 212, 255, 0.07)',
    }}>

      {/* ── Header / drag handle ── */}
      <div
        onMouseDown={onHeaderDown}
        style={{
          height: 30,
          background: 'rgba(13, 31, 60, 0.98)',
          borderBottom: '1px solid rgba(0, 212, 255, 0.17)',
          display: 'flex', alignItems: 'center', justifyContent: 'space-between',
          padding: '0 8px 0 12px',
          cursor: 'grab',
          flexShrink: 0,
          userSelect: 'none',
        }}
      >
        <span style={{
          fontFamily: "'Share Tech Mono', monospace",
          fontSize: 9, letterSpacing: 2,
          color: '#00d4ff',
          textShadow: '0 0 8px rgba(0,212,255,0.5)',
        }}>
          {title}
        </span>
        <button
          onMouseDown={e => e.stopPropagation()}
          onClick={onClose}
          style={{
            background: 'none', border: 'none', cursor: 'pointer',
            color: 'rgba(0,212,255,0.55)',
            fontSize: 18, lineHeight: 1, padding: '0 3px',
          }}
          onMouseEnter={e => { e.currentTarget.style.color = '#f87171' }}
          onMouseLeave={e => { e.currentTarget.style.color = 'rgba(0,212,255,0.55)' }}
        >
          ×
        </button>
      </div>

      {/* ── Content ── */}
      <div style={{ display: 'flex', flexDirection: 'column', flex: 1, overflow: 'hidden' }}>
        {children}
      </div>
    </div>
  )
}
