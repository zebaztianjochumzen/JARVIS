export default function GridBackground() {
  return (
    <>
      <style>{`
        @keyframes grid-pulse {
          0%, 100% { opacity: 1; }
          50%       { opacity: 0.55; }
        }
        .hud-grid {
          animation: grid-pulse 4s ease-in-out infinite;
        }
      `}</style>
      <div
        className="hud-grid"
        style={{
          position: 'fixed', inset: 0, zIndex: 0, pointerEvents: 'none',
          backgroundImage: [
            'linear-gradient(rgba(0, 212, 255, 0.06) 1px, transparent 1px)',
            'linear-gradient(90deg, rgba(0, 212, 255, 0.06) 1px, transparent 1px)',
          ].join(','),
          backgroundSize: '40px 40px',
        }}
      />
    </>
  )
}
