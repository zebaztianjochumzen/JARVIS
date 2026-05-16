"""Google Maps client — Geocoding, Directions (traffic-aware), and Places.

Used as the intelligence layer under Mapbox's visual rendering.
Falls back gracefully when GOOGLE_MAPS_API_KEY is not configured.
"""

import os
import requests

_GEOCODE_URL    = "https://maps.googleapis.com/maps/api/geocode/json"
_DIRECTIONS_URL = "https://maps.googleapis.com/maps/api/directions/json"
_PLACES_URL     = "https://maps.googleapis.com/maps/api/place/nearbysearch/json"
_MATRIX_URL     = "https://maps.googleapis.com/maps/api/distancematrix/json"
_POLLEN_URL     = "https://pollen.googleapis.com/v1/forecast:lookup"


def _key() -> str:
    key = os.environ.get("GOOGLE_API_KEY", "").strip()
    if not key:
        raise RuntimeError("GOOGLE_API_KEY not configured.")
    return key


def geocode(place: str) -> tuple[float, float, str]:
    """Return (lat, lon, formatted_address) for a place name or address."""
    r = requests.get(_GEOCODE_URL, params={"address": place, "key": _key()}, timeout=8)
    data = r.json()
    if data["status"] != "OK":
        raise ValueError(f"Geocoding failed for '{place}': {data['status']}")
    result = data["results"][0]
    loc    = result["geometry"]["location"]
    return loc["lat"], loc["lng"], result["formatted_address"]


def _decode_polyline(encoded: str) -> list[list[float]]:
    """Decode a Google encoded polyline to [[lon, lat], ...] pairs for Mapbox."""
    coords = []
    index  = 0
    lat = lng = 0
    n   = len(encoded)
    while index < n:
        for is_lat in (True, False):
            result = shift = 0
            while True:
                b = ord(encoded[index]) - 63
                index += 1
                result |= (b & 0x1F) << shift
                shift  += 5
                if b < 0x20:
                    break
            delta = ~(result >> 1) if (result & 1) else (result >> 1)
            if is_lat:
                lat += delta
            else:
                lng += delta
        coords.append([lng / 1e5, lat / 1e5])   # [lon, lat] — Mapbox convention
    return coords


def directions(
    o_lat: float, o_lon: float,
    d_lat: float, d_lon: float,
) -> tuple[list[list[float]], float, int]:
    """Return (coords, distance_km, duration_min) with live traffic ETA.

    coords is a list of [lon, lat] pairs compatible with Mapbox LineString.
    """
    r = requests.get(_DIRECTIONS_URL, params={
        "origin":         f"{o_lat},{o_lon}",
        "destination":    f"{d_lat},{d_lon}",
        "departure_time": "now",   # enables traffic-aware duration_in_traffic
        "key":            _key(),
    }, timeout=15)
    data = r.json()
    if data["status"] != "OK":
        raise ValueError(f"Directions failed: {data['status']}")

    route = data["routes"][0]
    leg   = route["legs"][0]

    coords       = _decode_polyline(route["overview_polyline"]["points"])
    distance_km  = round(leg["distance"]["value"] / 1000, 1)
    dur          = leg.get("duration_in_traffic", leg["duration"])
    duration_min = round(dur["value"] / 60)

    return coords, distance_km, duration_min


def distance_matrix(origin: str, destinations: list[str]) -> list[dict]:
    """Return travel time + distance from one origin to multiple destinations.

    Each result dict: {destination, distance_km, duration_min, duration_traffic_min}
    """
    dest_str = "|".join(destinations)
    r = requests.get(_MATRIX_URL, params={
        "origins":         origin,
        "destinations":    dest_str,
        "departure_time":  "now",
        "key":             _key(),
    }, timeout=12)
    data = r.json()
    if data["status"] != "OK":
        raise ValueError(f"Distance Matrix failed: {data['status']}")

    row     = data["rows"][0]["elements"]
    results = []
    for dest, elem in zip(destinations, row):
        if elem["status"] != "OK":
            results.append({"destination": dest, "error": elem["status"]})
            continue
        dur_traffic = elem.get("duration_in_traffic", elem["duration"])
        results.append({
            "destination":        dest,
            "distance_km":        round(elem["distance"]["value"] / 1000, 1),
            "duration_min":       round(elem["duration"]["value"] / 60),
            "duration_traffic_min": round(dur_traffic["value"] / 60),
        })
    return results


def pollen_forecast(lat: float, lon: float) -> dict:
    """Return today's pollen forecast for grass, tree, and weed."""
    r = requests.get(_POLLEN_URL, params={
        "location.latitude":  lat,
        "location.longitude": lon,
        "days":               1,
        "key":                _key(),
    }, timeout=10)
    data = r.json()

    result = {}
    daily = data.get("dailyInfo", [{}])[0]
    for pollen in daily.get("pollenTypeInfo", []):
        code  = pollen.get("code", "").upper()
        index = pollen.get("indexInfo", {})
        result[code] = {
            "value":    index.get("value", 0),
            "category": index.get("category", "None"),
        }
    return result


def embed_streetview_url(lat: float, lon: float) -> str:
    """Return a Maps Embed API Street View URL — iframe-safe, no proxy needed."""
    return (
        f"https://www.google.com/maps/embed/v1/streetview"
        f"?key={_key()}&location={lat},{lon}&heading=210&pitch=10&fov=90"
    )


def embed_place_url(place_id: str) -> str:
    """Return a Maps Embed API place view URL — iframe-safe, no proxy needed."""
    return (
        f"https://www.google.com/maps/embed/v1/place"
        f"?key={_key()}&q=place_id:{place_id}&zoom=16"
    )


def places_nearby(query: str, lat: float, lon: float, radius_m: int = 3000) -> list[dict]:
    """Search Google Places near a location. Returns up to 8 results."""
    r = requests.get(_PLACES_URL, params={
        "location": f"{lat},{lon}",
        "radius":   radius_m,
        "keyword":  query,
        "key":      _key(),
    }, timeout=10)
    data = r.json()
    if data["status"] not in ("OK", "ZERO_RESULTS"):
        raise ValueError(f"Places search failed: {data['status']}")

    results = []
    for p in data.get("results", [])[:8]:
        results.append({
            "name":    p["name"],
            "address": p.get("vicinity", ""),
            "rating":  p.get("rating"),
            "open":    p.get("opening_hours", {}).get("open_now"),
            "lat":     p["geometry"]["location"]["lat"],
            "lon":     p["geometry"]["location"]["lng"],
        })
    return results
