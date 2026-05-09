import { useEffect, useState, useRef } from 'react'
import { MapContainer, TileLayer, Marker, Circle, Polyline, useMap } from 'react-leaflet'
import 'leaflet/dist/leaflet.css'
import L from 'leaflet'

// Custom HUD-style location marker
const locationIcon = L.divIcon({
  className: '',
  html: `
    <div style="position:relative;width:20px;height:20px">
      <div style="
        position:absolute;inset:0;border-radius:50%;
        border:2px solid rgba(80,200,255,0.9);
        box-shadow:0 0 12px rgba(0,180,255,0.7), inset 0 0 6px rgba(0,180,255,0.3);
        animation:loc-pulse 2s ease-in-out infinite;
      "></div>
      <div style="
        position:absolute;top:50%;left:50%;
        transform:translate(-50%,-50%);
        width:6px;height:6px;border-radius:50%;
        background:rgba(80,200,255,1);
        box-shadow:0 0 8px rgba(0,180,255,1);
      "></div>
    </div>
  `,
  iconSize: [20, 20],
  iconAnchor: [10, 10],
})

function SizeInvalidator({ visible }) {
  const map = useMap()
  useEffect(() => {
    if (visible) setTimeout(() => map.invalidateSize(), 50)
  }, [visible, map])
  return null
}

function LocationHandler({ onLocate }) {
  const map = useMap()
  useEffect(() => {
    if (!navigator.geolocation) return
    navigator.geolocation.getCurrentPosition(
      (pos) => {
        const { latitude: lat, longitude: lng, accuracy } = pos.coords
        onLocate({ lat, lng, accuracy })
        map.flyTo([lat, lng], 13, { duration: 1.5 })
      },
      () => {}
    )
  }, [map, onLocate])
  return null
}

function FlyToHandler({ showLocation }) {
  const map = useMap()
  useEffect(() => {
    if (!showLocation) return
    map.flyTo([showLocation.lat, showLocation.lon], 13, { duration: 1.5 })
  }, [showLocation, map])
  return null
}

function RouteHandler({ route }) {
  const map = useMap()
  useEffect(() => {
    if (!route) return
    // Fit the map to show the full route
    const latLngs = route.coordinates.map(([lon, lat]) => [lat, lon])
    map.fitBounds(latLngs, { padding: [60, 60], duration: 1.5 })
  }, [route, map])
  return null
}

const pinIcon = (color) => L.divIcon({
  className: '',
  html: `<div style="
    width:14px;height:14px;border-radius:50%;
    background:${color};
    border:2px solid rgba(255,255,255,0.8);
    box-shadow:0 0 10px ${color};
  "></div>`,
  iconSize: [14, 14],
  iconAnchor: [7, 7],
})

const HUD_CORNERS = ['top-left', 'top-right', 'bottom-left', 'bottom-right']

export default function MapPanel({ visible, route, showLocation }) {
  const [location, setLocation] = useState(null)

  return (
    <div style={{ height: '100%', width: '100%', position: 'relative', background: '#070b14' }}>

      {/* HUD top bar */}
      <div style={{
        position: 'absolute', top: 0, left: 0, right: 0,
        padding: '10px 20px',
        display: 'flex', justifyContent: 'space-between', alignItems: 'center',
        background: 'linear-gradient(to bottom, rgba(7,11,20,0.9) 0%, transparent 100%)',
        zIndex: 1000, pointerEvents: 'none',
      }}>
        <div style={{ fontFamily: "'Share Tech Mono', monospace", fontSize: 13, letterSpacing: 4, color: '#4fc3f7' }}>
          ◉ TACTICAL MAP
        </div>
        <div style={{ display: 'flex', gap: 20, alignItems: 'center' }}>
          {location && (
            <div style={{ fontFamily: "'Share Tech Mono', monospace", fontSize: 11, color: 'rgba(80,200,255,0.7)', letterSpacing: 1 }}>
              {location.lat.toFixed(4)}°N &nbsp; {location.lng.toFixed(4)}°E
            </div>
          )}
          <div style={{ fontFamily: "'Rajdhani', sans-serif", fontSize: 11, letterSpacing: 3, color: 'rgba(100,160,220,0.4)' }}>
            OPENSTREETMAP
          </div>
        </div>
      </div>

      {/* HUD corner brackets */}
      {HUD_CORNERS.map(pos => {
        const [v, h] = pos.split('-')
        return (
          <div key={pos} style={{
            position: 'absolute',
            [v]: 12, [h]: 12,
            width: 20, height: 20,
            borderTop:    v === 'top'    ? '2px solid rgba(80,180,255,0.5)' : 'none',
            borderBottom: v === 'bottom' ? '2px solid rgba(80,180,255,0.5)' : 'none',
            borderLeft:   h === 'left'   ? '2px solid rgba(80,180,255,0.5)' : 'none',
            borderRight:  h === 'right'  ? '2px solid rgba(80,180,255,0.5)' : 'none',
            zIndex: 1000, pointerEvents: 'none',
          }} />
        )
      })}

      <MapContainer
        center={[62.0, 15.0]}
        zoom={5}
        style={{ height: '100%', width: '100%' }}
        zoomControl={false}
      >
        <TileLayer
          url="https://{s}.basemaps.cartocdn.com/dark_all/{z}/{x}/{y}{r}.png"
          attribution='&copy; OpenStreetMap &copy; CARTO'
          subdomains="abcd"
          maxZoom={19}
        />
        <SizeInvalidator visible={visible} />
        <LocationHandler onLocate={setLocation} />
        <FlyToHandler showLocation={showLocation} />
        <RouteHandler route={route} />

        {location && (
          <>
            <Circle
              center={[location.lat, location.lng]}
              radius={location.accuracy}
              pathOptions={{ color: 'rgba(0,180,255,0.3)', fillColor: 'rgba(0,180,255,0.05)', fillOpacity: 1, weight: 1 }}
            />
            <Marker position={[location.lat, location.lng]} icon={locationIcon} />
          </>
        )}

        {route && (() => {
          const latLngs = route.coordinates.map(([lon, lat]) => [lat, lon])
          return (
            <>
              {/* Glow underlay */}
              <Polyline positions={latLngs} pathOptions={{ color: 'rgba(0,180,255,0.25)', weight: 12, lineCap: 'round', lineJoin: 'round' }} />
              {/* Main route line */}
              <Polyline positions={latLngs} pathOptions={{ color: '#4fc3f7', weight: 3, lineCap: 'round', lineJoin: 'round' }} />
              {/* Origin pin (green) */}
              <Marker position={[route.origin.lat, route.origin.lon]} icon={pinIcon('#4ade80')} />
              {/* Destination pin (red) */}
              <Marker position={[route.destination.lat, route.destination.lon]} icon={pinIcon('#f87171')} />
            </>
          )
        })()}
      </MapContainer>

      {/* Route info card */}
      {route && (
        <div style={{
          position: 'absolute', bottom: 20, left: '50%', transform: 'translateX(-50%)',
          background: 'rgba(7,11,20,0.9)', border: '1px solid rgba(0,140,255,0.3)',
          borderRadius: 10, padding: '10px 24px', zIndex: 1000, display: 'flex', gap: 24,
          backdropFilter: 'blur(8px)',
        }}>
          <div style={{ textAlign: 'center' }}>
            <div style={{ fontFamily: "'Rajdhani'", fontSize: 10, letterSpacing: 3, color: 'rgba(100,160,220,0.5)' }}>FROM</div>
            <div style={{ fontFamily: "'Share Tech Mono'", fontSize: 12, color: '#4ade80' }}>{route.origin.name}</div>
          </div>
          <div style={{ textAlign: 'center' }}>
            <div style={{ fontFamily: "'Rajdhani'", fontSize: 10, letterSpacing: 3, color: 'rgba(100,160,220,0.5)' }}>DISTANCE</div>
            <div style={{ fontFamily: "'Share Tech Mono'", fontSize: 14, color: '#e8f4ff' }}>{route.distance_km} km</div>
          </div>
          <div style={{ textAlign: 'center' }}>
            <div style={{ fontFamily: "'Rajdhani'", fontSize: 10, letterSpacing: 3, color: 'rgba(100,160,220,0.5)' }}>ETA</div>
            <div style={{ fontFamily: "'Share Tech Mono'", fontSize: 14, color: '#e8f4ff' }}>{route.duration_min} min</div>
          </div>
          <div style={{ textAlign: 'center' }}>
            <div style={{ fontFamily: "'Rajdhani'", fontSize: 10, letterSpacing: 3, color: 'rgba(100,160,220,0.5)' }}>TO</div>
            <div style={{ fontFamily: "'Share Tech Mono'", fontSize: 12, color: '#f87171' }}>{route.destination.name}</div>
          </div>
        </div>
      )}

      <style>{`
        .leaflet-container { background: #070b14 !important; }
        .leaflet-control-attribution { display: none; }
        .leaflet-tile { border: none !important; }
        @keyframes loc-pulse {
          0%, 100% { transform: scale(1); opacity: 1; }
          50%       { transform: scale(1.4); opacity: 0.6; }
        }
      `}</style>
    </div>
  )
}
