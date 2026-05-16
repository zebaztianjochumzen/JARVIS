"""Map tools — fly to a location, search nearby places.

Uses Google Maps APIs when GOOGLE_MAPS_API_KEY is set (much more accurate).
Falls back to Nominatim (OpenStreetMap) when not configured.
"""

import requests as _req

_NOMINATIM_HEADERS = {"User-Agent": "JARVIS/1.0 (jarvis-bot)"}


def _geocode(place: str) -> tuple[float, float, str]:
    """Return (lat, lon, display_name). Tries Google first, falls back to Nominatim."""
    try:
        from jarvis.tools.google_maps import geocode
        return geocode(place)
    except RuntimeError:
        pass

    # Nominatim fallback
    r = _req.get(
        "https://nominatim.openstreetmap.org/search",
        params={"q": place, "format": "json", "limit": 1},
        headers=_NOMINATIM_HEADERS, timeout=8,
    )
    results = r.json()
    if not results:
        raise ValueError(f"Could not geocode: {place}")
    return float(results[0]["lat"]), float(results[0]["lon"]), results[0]["display_name"].split(",")[0]


def show_location(place: str, agent=None) -> str:
    """Geocode a place name and fly the Mapbox map to it."""
    try:
        lat, lon, display = _geocode(place)
        if agent is not None:
            agent.pending_actions.append({
                "type": "show_location",
                "lat": lat, "lon": lon,
                "name": display,
            })
        return f"Showing {display} on the map."
    except Exception as e:
        return f"show_location failed: {e}"


def compare_travel_times(destinations: list, origin: str, agent=None) -> str:
    """Compare driving times from one origin to multiple destinations using Google Distance Matrix."""
    try:
        from jarvis.tools.google_maps import distance_matrix
        results = distance_matrix(origin, destinations)
        results.sort(key=lambda x: x.get("duration_traffic_min", 9999))

        lines = [f"Travel times from {origin} with current traffic:"]
        for r in results:
            if "error" in r:
                lines.append(f"  • {r['destination']}: unavailable")
            else:
                lines.append(
                    f"  • {r['destination']}: {r['duration_traffic_min']} min "
                    f"({r['distance_km']} km)"
                )
        return "\n".join(lines)
    except RuntimeError:
        return "Distance Matrix requires GOOGLE_MAPS_API_KEY to be configured."
    except Exception as e:
        return f"compare_travel_times failed: {e}"


def get_pollen(location: str = "Stockholm", agent=None) -> str:
    """Return today's pollen forecast (grass, tree, weed) for a location."""
    try:
        from jarvis.tools.google_maps import geocode, pollen_forecast
        lat, lon, loc_name = geocode(location)
        data = pollen_forecast(lat, lon)

        if not data:
            return f"No pollen data available for {loc_name}."

        label_map = {"GRASS": "Grass", "TREE": "Tree", "WEED": "Weed"}
        lines = [f"Pollen forecast for {loc_name}:"]
        for code, label in label_map.items():
            if code in data:
                d = data[code]
                lines.append(f"  • {label}: {d['category']} ({d['value']}/5)")
        return "\n".join(lines)
    except RuntimeError:
        return "Pollen forecast requires GOOGLE_MAPS_API_KEY to be configured."
    except Exception as e:
        return f"get_pollen failed: {e}"


def search_nearby(query: str, location: str = "Stockholm", agent=None) -> str:
    """Find places matching a query near a given location."""

    # ── Google Places path ────────────────────────────────────────────────────
    try:
        from jarvis.tools.google_maps import geocode, places_nearby

        lat, lon, loc_name = geocode(location)
        places = places_nearby(query, lat, lon)

        if not places:
            return f"No '{query}' found near {loc_name}."

        lines = [f"'{query}' near {loc_name}:"]
        for p in places[:6]:
            rating   = f" ★{p['rating']}" if p.get("rating") else ""
            open_str = " (open now)" if p.get("open") else ""
            lines.append(f"  • {p['name']} — {p['address']}{rating}{open_str}")
        return "\n".join(lines)

    except RuntimeError:
        pass   # key not configured — fall through to Nominatim

    except Exception as e:
        return f"Places search failed: {e}"

    # ── Nominatim fallback ────────────────────────────────────────────────────
    try:
        lat, lon, _ = _geocode(location)
        delta = 0.03
        r = _req.get(
            "https://nominatim.openstreetmap.org/search",
            params={
                "q": query, "format": "json", "limit": 8,
                "viewbox": f"{lon-delta},{lat+delta},{lon+delta},{lat-delta}",
                "bounded": 1,
            },
            headers=_NOMINATIM_HEADERS, timeout=8,
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
