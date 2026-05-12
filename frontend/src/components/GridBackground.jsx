export default function GridBackground() {
  return (
    <div style={{
      position: 'fixed',
      inset: 0,
      zIndex: 0,
      backgroundImage: `
        linear-gradient(rgba(30, 60, 100, 0.15) 1px, transparent 1px),
        linear-gradient(90deg, rgba(30, 60, 100, 0.15) 1px, transparent 1px)
      `,
      backgroundSize: '40px 40px',
      pointerEvents: 'none',
    }} />
  )
}
