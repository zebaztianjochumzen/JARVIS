import { useEffect, useRef, useState } from 'react'
import mapboxgl from 'mapbox-gl'
import 'mapbox-gl/dist/mapbox-gl.css'

const TOKEN = import.meta.env.VITE_MAPBOX_TOKEN || ''
if (TOKEN) mapboxgl.accessToken = TOKEN

const ROAD_KEYWORDS = ['motorway', 'trunk', 'primary', 'secondary', 'tertiary', 'street', 'road', 'bridge', 'tunnel', 'path', 'pedestrian', 'link']
const isRoadLayer = id => ROAD_KEYWORDS.some(k => id.includes(k))

const sleep = ms => new Promise(r => setTimeout(r, ms))

const HUD_CORNERS = [
  { v: 'top',    h: 'left',  top: 12,    left: 12  },
  { v: 'top',    h: 'right', top: 12,    right: 12 },
  { v: 'bottom', h: 'left',  bottom: 12, left: 12  },
  { v: 'bottom', h: 'right', bottom: 12, right: 12 },
]

const CORNER_BORDER = 'rgba(0, 180, 255, 0.55)'

export default function MapPanel({ visible, route, showLocation }) {
  const containerRef = useRef(null)
  const ctrlRef      = useRef({})
  const [coords,    setCoords]    = useState(null)
  const [statusMsg, setStatusMsg] = useState('STANDBY')

  // ── Map init ────────────────────────────────────────────────────────────────
  useEffect(() => {
    if (!TOKEN || !containerRef.current) return

    const map = new mapboxgl.Map({
      container: containerRef.current,
      style: 'mapbox://styles/mapbox/navigation-night-v1',
      center: [20, 30],
      zoom: 2.5,
      projection: { name: 'globe' },
      antialias: true,
      attributionControl: false,
    })

    // ── Animation state (closure-scoped to this map instance) ────────────────
    const state = { mode: 'idle', animId: null, userDragging: false }

    function stopAnim() {
      cancelAnimationFrame(state.animId)
      state.animId = null
      state.mode   = 'idle'
    }

    function startRotation() {
      stopAnim()
      state.mode = 'rotating'
      let last = 0
      function tick(t) {
        if (state.mode !== 'rotating') return
        if (!state.userDragging && last) {
          const c = map.getCenter()
          map.setCenter([c.lng - 0.008 * (t - last) / 16, c.lat])
        }
        last = t
        state.animId = requestAnimationFrame(tick)
      }
      state.animId = requestAnimationFrame(tick)
    }

    function startOrbit() {
      stopAnim()
      state.mode = 'orbiting'
      let bearing = map.getBearing()
      function tick() {
        if (state.mode !== 'orbiting') return
        if (!state.userDragging) {
          bearing = (bearing + 0.025) % 360
          map.setBearing(bearing)
        }
        state.animId = requestAnimationFrame(tick)
      }
      state.animId = requestAnimationFrame(tick)
    }

    async function cinematicFlyTo([lng, lat]) {
      stopAnim()
      // Phase 1 — pull back to full globe
      map.flyTo({ zoom: 2.5, bearing: 0, pitch: 0, duration: 1500, essential: true })
      await sleep(1800)
      // Phase 2 — dramatic cross-globe flight
      map.flyTo({
        center: [lng, lat],
        zoom: 12,
        duration: 4000,
        curve: 1.5,
        speed: 0.8,
        easing: t => t * (2 - t),
        essential: true,
      })
      await sleep(4400)
      // Phase 3 — slow orbit
      startOrbit()
    }

    function addRoute(routeData) {
      ;['route-glow', 'route-line'].forEach(id => { if (map.getLayer(id)) map.removeLayer(id) })
      if (map.getSource('route')) map.removeSource('route')

      const coords = routeData.coordinates.map(([lon, lat]) => [lon, lat])
      map.addSource('route', {
        type: 'geojson',
        data: { type: 'Feature', geometry: { type: 'LineString', coordinates: coords } },
      })
      map.addLayer({
        id: 'route-glow', type: 'line', source: 'route',
        paint: { 'line-color': 'rgba(0,180,255,0.22)', 'line-width': 14, 'line-blur': 10 },
      })
      map.addLayer({
        id: 'route-line', type: 'line', source: 'route',
        paint: { 'line-color': '#00d4ff', 'line-width': 2.5, 'line-glow-width': 5 },
      })
      const bounds = coords.reduce(
        (b, c) => b.extend(c),
        new mapboxgl.LngLatBounds(coords[0], coords[0])
      )
      stopAnim()
      map.fitBounds(bounds, { padding: 80, duration: 2500 })
    }

    // ── Map load ─────────────────────────────────────────────────────────────
    map.on('load', () => {
      // Stars + atmosphere around the globe
      map.setFog({
        color:            'rgb(2, 11, 24)',
        'high-color':     'rgb(0, 35, 80)',
        'horizon-blend':  0.025,
        'space-color':    'rgb(1, 4, 12)',
        'star-intensity': 0.92,
      })

      // Apply glow to every road-type line layer
      map.getStyle().layers.forEach(layer => {
        if (layer.type === 'line' && isRoadLayer(layer.id)) {
          try {
            map.setPaintProperty(layer.id, 'line-blur', 0.8)
            map.setPaintProperty(layer.id, 'line-glow-width', 5)
          } catch {}
        }
      })

      startRotation()
    })

    // Pause rotation while user drags; resume when they let go
    map.on('mousedown',  () => { state.userDragging = true;  stopAnim() })
    map.on('mouseup',    () => { state.userDragging = false; if (state.mode === 'idle') startRotation() })
    map.on('touchstart', () => { state.userDragging = true;  stopAnim() })
    map.on('touchend',   () => { state.userDragging = false; if (state.mode === 'idle') startRotation() })

    ctrlRef.current = { map, cinematicFlyTo, addRoute }

    return () => {
      stopAnim()
      map.remove()
      ctrlRef.current = {}
    }
  }, [])

  // ── Resize on visibility change ───────────────────────────────────────────
  useEffect(() => {
    if (visible && ctrlRef.current.map) setTimeout(() => ctrlRef.current.map.resize(), 50)
  }, [visible])

  // ── React to showLocation ─────────────────────────────────────────────────
  useEffect(() => {
    if (!showLocation || !ctrlRef.current.cinematicFlyTo) return
    setCoords({ lat: showLocation.lat, lon: showLocation.lon })
    setStatusMsg('ACQUIRING TARGET...')
    ctrlRef.current.cinematicFlyTo([showLocation.lon, showLocation.lat])
      .then(() => setStatusMsg('TARGET LOCKED'))
  }, [showLocation])

  // ── React to route ────────────────────────────────────────────────────────
  useEffect(() => {
    if (!route || !ctrlRef.current.addRoute) return
    ctrlRef.current.addRoute(route)
    setStatusMsg('ROUTE CALCULATED')
  }, [route])

  return (
    <div style={{ height: '100%', width: '100%', position: 'relative', background: '#020b18', overflow: 'hidden' }}>

      {/* Mapbox canvas */}
      <div ref={containerRef} style={{ height: '100%', width: '100%' }} />

      {/* Sci-fi grid overlay */}
      <div style={{
        position: 'absolute', inset: 0, pointerEvents: 'none', zIndex: 5,
        backgroundImage: [
          'linear-gradient(rgba(255,255,255,0.032) 1px, transparent 1px)',
          'linear-gradient(90deg, rgba(255,255,255,0.032) 1px, transparent 1px)',
        ].join(','),
        backgroundSize: '60px 60px',
      }} />

      {/* Radial vignette to push focus toward center */}
      <div style={{
        position: 'absolute', inset: 0, pointerEvents: 'none', zIndex: 6,
        background: 'radial-gradient(ellipse at center, transparent 45%, rgba(2,11,24,0.65) 100%)',
      }} />

      {/* HUD top bar */}
      <div style={{
        position: 'absolute', top: 0, left: 0, right: 0,
        padding: '10px 20px', display: 'flex', justifyContent: 'space-between', alignItems: 'center',
        background: 'linear-gradient(to bottom, rgba(2,11,24,0.92) 0%, transparent 100%)',
        zIndex: 10, pointerEvents: 'none',
      }}>
        <div style={{
          fontFamily: "'Share Tech Mono', monospace", fontSize: 13, letterSpacing: 4,
          color: '#00d4ff', textShadow: '0 0 14px rgba(0,212,255,0.85)',
        }}>
          ◉ TACTICAL MAP
        </div>
        <div style={{ display: 'flex', gap: 24, alignItems: 'center' }}>
          {coords && (
            <span style={{
              fontFamily: "'Share Tech Mono', monospace", fontSize: 11,
              color: 'rgba(0,212,255,0.72)', letterSpacing: 1,
            }}>
              {coords.lat.toFixed(4)}°N &nbsp;{coords.lon.toFixed(4)}°E
            </span>
          )}
          <span style={{
            fontFamily: "'Share Tech Mono', monospace", fontSize: 11, letterSpacing: 3,
            color: 'rgba(0,212,255,0.42)', textShadow: '0 0 8px rgba(0,212,255,0.5)',
          }}>
            {statusMsg}
          </span>
        </div>
      </div>

      {/* HUD corner brackets */}
      {HUD_CORNERS.map(({ v, h, ...pos }) => (
        <div key={`${v}-${h}`} style={{
          position: 'absolute', ...pos,
          width: 22, height: 22,
          borderTop:    v === 'top'    ? `2px solid ${CORNER_BORDER}` : 'none',
          borderBottom: v === 'bottom' ? `2px solid ${CORNER_BORDER}` : 'none',
          borderLeft:   h === 'left'   ? `2px solid ${CORNER_BORDER}` : 'none',
          borderRight:  h === 'right'  ? `2px solid ${CORNER_BORDER}` : 'none',
          filter: 'drop-shadow(0 0 5px rgba(0,180,255,0.7))',
          zIndex: 10, pointerEvents: 'none',
        }} />
      ))}

      {/* Route info card */}
      {route && (
        <div style={{
          position: 'absolute', bottom: 20, left: '50%', transform: 'translateX(-50%)',
          background: 'rgba(2,11,24,0.92)', border: '1px solid rgba(0,180,255,0.3)',
          borderRadius: 10, padding: '10px 24px', zIndex: 10,
          display: 'flex', gap: 24, backdropFilter: 'blur(10px)',
          boxShadow: '0 0 24px rgba(0,100,200,0.22)',
        }}>
          {[
            { label: 'FROM',     value: route.origin.name,      color: '#4ade80' },
            { label: 'DISTANCE', value: `${route.distance_km} km`, color: '#e8f4ff' },
            { label: 'ETA',      value: `${route.duration_min} min`, color: '#e8f4ff' },
            { label: 'TO',       value: route.destination.name, color: '#f87171' },
          ].map(({ label, value, color }) => (
            <div key={label} style={{ textAlign: 'center' }}>
              <div style={{
                fontFamily: "'Rajdhani', sans-serif", fontSize: 10,
                letterSpacing: 3, color: 'rgba(0,180,255,0.5)', marginBottom: 2,
              }}>{label}</div>
              <div style={{
                fontFamily: "'Share Tech Mono', monospace", fontSize: 13, color,
              }}>{value}</div>
            </div>
          ))}
        </div>
      )}

      {/* No-token fallback */}
      {!TOKEN && (
        <div style={{
          position: 'absolute', inset: 0, zIndex: 20,
          display: 'flex', flexDirection: 'column', alignItems: 'center', justifyContent: 'center',
          background: 'rgba(2,11,24,0.97)', gap: 12,
          fontFamily: "'Share Tech Mono', monospace",
        }}>
          <div style={{ fontSize: 14, letterSpacing: 4, color: '#f87171', textShadow: '0 0 12px rgba(248,113,113,0.7)' }}>
            ⚠ MAPBOX TOKEN REQUIRED
          </div>
          <div style={{ fontSize: 11, color: 'rgba(0,180,255,0.5)', letterSpacing: 2 }}>
            Set VITE_MAPBOX_TOKEN in .env
          </div>
        </div>
      )}

      <style>{`
        .mapboxgl-ctrl-logo,
        .mapboxgl-ctrl-attrib,
        .mapboxgl-ctrl-bottom-right,
        .mapboxgl-ctrl-bottom-left { display: none !important; }
      `}</style>
    </div>
  )
}
