import { useRef, useEffect } from 'react'

const BARS    = 48
const BAR_W   = 3
const BAR_GAP = 2
const H       = 52
const W       = BARS * (BAR_W + BAR_GAP) - BAR_GAP

export default function Waveform({ userSpeaking, speaking }) {
  const canvasRef = useRef(null)
  const frameRef  = useRef(null)
  const phaseRef  = useRef(0)
  const barsRef   = useRef(new Array(BARS).fill(0.05))

  const mode = userSpeaking ? 'recording' : speaking ? 'speaking' : 'idle'

  useEffect(() => {
    const canvas = canvasRef.current
    if (!canvas) return
    const ctx = canvas.getContext('2d')

    function draw() {
      ctx.clearRect(0, 0, W, H)

      phaseRef.current += mode === 'recording' ? 0.14 : mode === 'speaking' ? 0.07 : 0.025
      const phase = phaseRef.current
      const bars  = barsRef.current

      for (let i = 0; i < BARS; i++) {
        let target
        if (mode === 'recording') {
          // Randomised jitter with envelope shape (louder in the middle)
          const env = 0.4 + 0.6 * Math.pow(Math.sin((i / BARS) * Math.PI), 0.5)
          target = env * (0.2 + Math.random() * 0.7 * Math.abs(Math.sin(phase + i * 0.35)))
        } else if (mode === 'speaking') {
          // Layered sine waves — looks like a real TTS waveform
          target = 0.15
            + 0.45 * Math.abs(Math.sin(phase       + i * 0.22))
            + 0.20 * Math.abs(Math.sin(phase * 1.7 + i * 0.45))
        } else {
          // Barely-there idle shimmer
          target = 0.03 + 0.04 * Math.abs(Math.sin(phase * 0.5 + i * 0.5))
        }

        const speed = mode === 'idle' ? 0.04 : 0.28
        bars[i] += (target - bars[i]) * speed
      }

      // Colour gradient: red for mic, blue for TTS, dim-blue for idle
      const grad = ctx.createLinearGradient(0, H, 0, 0)
      if (mode === 'recording') {
        grad.addColorStop(0, 'rgba(255,80,80,0.95)')
        grad.addColorStop(1, 'rgba(255,140,100,0.4)')
      } else if (mode === 'speaking') {
        grad.addColorStop(0, 'rgba(80,180,255,0.95)')
        grad.addColorStop(1, 'rgba(120,220,255,0.35)')
      } else {
        grad.addColorStop(0, 'rgba(80,180,255,0.18)')
        grad.addColorStop(1, 'rgba(120,200,255,0.06)')
      }
      ctx.fillStyle = grad

      for (let i = 0; i < BARS; i++) {
        const h = Math.max(2, bars[i] * H)
        const x = i * (BAR_W + BAR_GAP)
        const y = (H - h) / 2
        ctx.beginPath()
        ctx.roundRect(x, y, BAR_W, h, 1.5)
        ctx.fill()
      }

      frameRef.current = requestAnimationFrame(draw)
    }

    frameRef.current = requestAnimationFrame(draw)
    return () => cancelAnimationFrame(frameRef.current)
  }, [mode])

  return (
    <div style={{
      position:   'fixed',
      bottom:     88,
      left:       '50%',
      transform:  'translateX(-50%)',
      pointerEvents: 'none',
      zIndex:     600,
      opacity:    mode === 'idle' ? 0.35 : 1,
      transition: 'opacity 0.5s ease',
    }}>
      <canvas ref={canvasRef} width={W} height={H} style={{ display: 'block' }} />
    </div>
  )
}
