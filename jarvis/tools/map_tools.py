"""Map tools — fly to a location, search nearby places."""

import requests as _req

_HEADERS = {"User-Agent": "JARVIS/1.0 (jarvis-bot)"}


def _geocode(place: str) -> tuple[float, float]:
    r = _req.get(
        "https://nominatim.openstreetmap.org/search",
        params={"q": place, "format": "json", "limit": 1},
        headers=_HEADERS, timeout=8,
    )
    results = r.json()
    if not results:
        raise ValueError(f"Could not geocode: {place}")
    return float(results[0]["lat"]), float(results[0]["lon"])


def show_location(place: str, agent=None) -> str:
    """Geocode a place name and fly the map to it."""
    try:
        lat, lon = _geocode(place)
        if agent is not None:
            agent.pending_actions.append({
                "type": "show_location",
                "lat": lat, "lon": lon,
                "name": place,
            })
        return f"Showing {place} on map ({lat:.4f}°N, {lon:.4f}°E)."
    except Exception as e:
        return f"show_location failed: {e}"


def search_nearby(query: str, location: str = "Stockholm", agent=None) -> str:
    """Find places matching a query near a given location via Nominatim."""
    try:
        lat, lon = _geocode(location)
        delta = 0.03
        r = _req.get(
            "https://nominatim.openstreetmap.org/search",
            params={
                "q": query, "format": "json", "limit": 8,
                "viewbox": f"{lon-delta},{lat+delta},{lon+delta},{lat-delta}",
                "bounded": 1,
            },
            headers=_HEADERS, timeout=8,
        )
        places = r.json()
        if not places:
            return f"No '{query}' found near {location}."
        lines = [f"'{query}' near {location}:"]
        for p in places[:6]:
            name    = p["display_name"].split(",")[0]
            address = ", ".join(p["display_name"].split(",")[:3])
            lines.append(f"  • {name} — {address}")
        return "\n".join(lines)
    except Exception as e:
        return f"search_nearby failed: {e}"
