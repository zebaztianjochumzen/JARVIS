"""Route planning — Google Maps Directions (traffic-aware) with OSRM fallback."""

import requests

_NOMINATIM = "https://nominatim.openstreetmap.org/search"
_OSRM      = "https://router.project-osrm.org/route/v1/driving"
_HEADERS   = {"User-Agent": "JARVIS/1.0 (personal assistant)"}


def _nominatim_geocode(place: str) -> tuple[float, float]:
    r = requests.get(_NOMINATIM, params={"q": place, "format": "json", "limit": 1},
                     headers=_HEADERS, timeout=8)
    results = r.json()
    if not results:
        raise ValueError(f"Could not find location: {place!r}")
    return float(results[0]["lat"]), float(results[0]["lon"])


def _osrm_route(o_lat, o_lon, d_lat, d_lon):
    url = f"{_OSRM}/{o_lon},{o_lat};{d_lon},{d_lat}"
    r   = requests.get(url, params={"overview": "full", "geometries": "geojson",
                                    "steps": "false"}, headers=_HEADERS, timeout=15)
    data = r.json()
    if data.get("code") != "Ok":
        raise ValueError(f"OSRM routing failed: {data.get('message', 'unknown error')}")
    route = data["routes"][0]
    coords       = route["geometry"]["coordinates"]   # already [[lon, lat]]
    distance_km  = round(route["legs"][0]["distance"] / 1000, 1)
    duration_min = round(route["legs"][0]["duration"] / 60)
    return coords, distance_km, duration_min


def plan_route(origin: str, destination: str, agent=None) -> str:
    """Geocode origin + destination and fetch a driving route with ETA."""

    # ── Google Maps path (traffic-aware) ──────────────────────────────────────
    try:
        from jarvis.tools.google_maps import geocode, directions as gm_directions

        o_lat, o_lon, o_name = geocode(origin)
        d_lat, d_lon, d_name = geocode(destination)
        coords, distance_km, duration_min = gm_directions(o_lat, o_lon, d_lat, d_lon)
        traffic_note = " with current traffic"

    except RuntimeError:
        # Google Maps API key not configured — use free Nominatim + OSRM
        try:
            o_lat, o_lon = _nominatim_geocode(origin)
            d_lat, d_lon = _nominatim_geocode(destination)
            coords, distance_km, duration_min = _osrm_route(o_lat, o_lon, d_lat, d_lon)
            o_name, d_name = origin, destination
            traffic_note = ""
        except Exception as e:
            return f"Routing failed: {e}"

    except Exception as e:
        return f"Routing failed: {e}"

    if agent is not None:
        agent.pending_actions.append({
            "type":         "route",
            "coordinates":  coords,
            "origin":       {"name": o_name, "lat": o_lat, "lon": o_lon},
            "destination":  {"name": d_name, "lat": d_lat, "lon": d_lon},
            "distance_km":  distance_km,
            "duration_min": duration_min,
        })

    return (
        f"Route from {origin} to {destination}: "
        f"{distance_km} km, approximately {duration_min} minutes{traffic_note}."
    )
