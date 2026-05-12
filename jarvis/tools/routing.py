"""Route planning — Nominatim geocoding + OSRM street-level routing (both free, no API key)."""

import json
import requests

NOMINATIM = "https://nominatim.openstreetmap.org/search"
OSRM      = "https://router.project-osrm.org/route/v1/driving"
HEADERS   = {"User-Agent": "JARVIS/1.0 (personal assistant)"}


def _geocode(place: str) -> tuple[float, float]:
    """Return (lat, lon) for a place name."""
    r = requests.get(NOMINATIM, params={"q": place, "format": "json", "limit": 1},
                     headers=HEADERS, timeout=8)
    results = r.json()
    if not results:
        raise ValueError(f"Could not find location: {place!r}")
    return float(results[0]["lat"]), float(results[0]["lon"])


def plan_route(origin: str, destination: str, agent=None) -> str:
    """Geocode origin + destination, fetch an OSRM driving route, store it on the agent."""
    try:
        o_lat, o_lon = _geocode(origin)
        d_lat, d_lon = _geocode(destination)
    except ValueError as e:
        return str(e)

    url = f"{OSRM}/{o_lon},{o_lat};{d_lon},{d_lat}"
    r = requests.get(url, params={
        "overview": "full",
        "geometries": "geojson",
        "steps": "false",
    }, headers=HEADERS, timeout=15)

    data = r.json()
    if data.get("code") != "Ok":
        return f"Routing failed: {data.get('message', 'unknown error')}"

    route = data["routes"][0]
    coords     = route["geometry"]["coordinates"]   # [[lon, lat], ...]
    distance_m = route["legs"][0]["distance"]
    duration_s = route["legs"][0]["duration"]

    distance_km  = round(distance_m / 1000, 1)
    duration_min = round(duration_s / 60)

    # Push route to the frontend via agent's pending_actions side-channel
    if agent is not None:
        agent.pending_actions.append({
            "type": "route",
            "coordinates": coords,       # [[lon, lat], ...]
            "origin":      {"name": origin,      "lat": o_lat, "lon": o_lon},
            "destination": {"name": destination, "lat": d_lat, "lon": d_lon},
            "distance_km": distance_km,
            "duration_min": duration_min,
        })

    return (
        f"Route from {origin} to {destination}: "
        f"{distance_km} km, approximately {duration_min} minutes by car."
    )
