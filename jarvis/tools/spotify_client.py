"""Spotify Web API client — token refresh + playback control. Uses requests only."""

import time
import base64
import threading

import requests

_token_lock  = threading.Lock()
_access_token: str  = ""
_token_expiry: float = 0.0


def _get_access_token() -> str:
    global _access_token, _token_expiry
    with _token_lock:
        if _access_token and time.time() < _token_expiry - 60:
            return _access_token

        from jarvis.secrets import get_secret
        client_id     = get_secret("SPOTIFY_CLIENT_ID")
        client_secret = get_secret("SPOTIFY_CLIENT_SECRET")
        refresh_token = get_secret("SPOTIFY_REFRESH_TOKEN")

        creds = base64.b64encode(f"{client_id}:{client_secret}".encode()).decode()
        r = requests.post(
            "https://accounts.spotify.com/api/token",
            headers={"Authorization": f"Basic {creds}"},
            data={"grant_type": "refresh_token", "refresh_token": refresh_token},
            timeout=8,
        )
        r.raise_for_status()
        data = r.json()
        _access_token = data["access_token"]
        _token_expiry = time.time() + data.get("expires_in", 3600)
        return _access_token


def now_playing() -> dict | None:
    """Returns current track dict or None if nothing is playing."""
    token = _get_access_token()
    r = requests.get(
        "https://api.spotify.com/v1/me/player/currently-playing",
        headers={"Authorization": f"Bearer {token}"},
        timeout=5,
    )
    if r.status_code == 204 or not r.content:
        return None
    data = r.json()
    if not data or data.get("currently_playing_type") != "track":
        return None
    item = data["item"]
    return {
        "is_playing":   data["is_playing"],
        "track":        item["name"],
        "artist":       ", ".join(a["name"] for a in item["artists"]),
        "album":        item["album"]["name"],
        "art_url":      item["album"]["images"][0]["url"] if item["album"]["images"] else None,
        "progress_ms":  data["progress_ms"],
        "duration_ms":  item["duration_ms"],
        "track_uri":    item["uri"],
    }


def control(action: str) -> str:
    """Play / pause / next / previous."""
    token = _get_access_token()
    _endpoints = {
        "play":     ("PUT",  "https://api.spotify.com/v1/me/player/play"),
        "pause":    ("PUT",  "https://api.spotify.com/v1/me/player/pause"),
        "next":     ("POST", "https://api.spotify.com/v1/me/player/next"),
        "previous": ("POST", "https://api.spotify.com/v1/me/player/previous"),
    }
    if action not in _endpoints:
        return f"Unknown action '{action}'. Use: play, pause, next, previous, search."
    method, url = _endpoints[action]
    r = requests.request(method, url, headers={"Authorization": f"Bearer {token}"}, timeout=5)
    if r.status_code in (200, 204):
        return f"Spotify: {action}"
    return f"Spotify error {r.status_code}: {r.text[:120]}"


def search_and_play(query: str) -> str:
    """Search for a track by name/artist and start playback."""
    token = _get_access_token()
    r = requests.get(
        "https://api.spotify.com/v1/search",
        headers={"Authorization": f"Bearer {token}"},
        params={"q": query, "type": "track", "limit": 1},
        timeout=5,
    )
    r.raise_for_status()
    items = r.json()["tracks"]["items"]
    if not items:
        return f"No tracks found for: {query}"

    uri    = items[0]["uri"]
    name   = items[0]["name"]
    artist = items[0]["artists"][0]["name"]

    r2 = requests.put(
        "https://api.spotify.com/v1/me/player/play",
        headers={"Authorization": f"Bearer {token}", "Content-Type": "application/json"},
        json={"uris": [uri]},
        timeout=5,
    )
    if r2.status_code in (200, 204):
        return f"Now playing: {name} by {artist}"
    return f"Found '{name}' but playback failed (is Spotify open on a device?): {r2.status_code}"
