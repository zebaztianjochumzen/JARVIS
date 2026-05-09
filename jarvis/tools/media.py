"""Media tools — Spotify control (Web API preferred, AppleScript fallback), volume, news."""

import subprocess


def play_music(action: str = "play", query: str = "", agent=None) -> str:
    """Control Spotify. Tries Web API first, falls back to AppleScript."""

    # ── Web API path ──────────────────────────────────────────────────────────
    try:
        from jarvis.tools.spotify_client import control, search_and_play
        if action == "search" and query:
            return search_and_play(query)
        if action in ("play", "pause", "next", "previous"):
            return control(action)
    except RuntimeError:
        pass  # secrets not configured — fall through to AppleScript
    except Exception:
        pass  # network / token error — fall through

    # ── AppleScript fallback ──────────────────────────────────────────────────
    scripts = {
        "play":     'tell application "Spotify" to play',
        "pause":    'tell application "Spotify" to pause',
        "next":     'tell application "Spotify" to next track',
        "previous": 'tell application "Spotify" to previous track',
    }
    if action in scripts:
        try:
            r = subprocess.run(["osascript", "-e", scripts[action]], capture_output=True, text=True)
            if r.returncode == 0:
                return f"Spotify: {action}"
            return f"Spotify not running or error: {r.stderr.strip()}"
        except Exception as e:
            return f"Spotify control failed: {e}"

    if action == "search" and query:
        try:
            url = f"spotify:search:{query.replace(' ', '%20')}"
            subprocess.run(["open", url], check=True)
            return f"Opened Spotify search: {query}"
        except Exception as e:
            return f"Spotify search failed: {e}"

    return f"Unknown action '{action}'. Use: play, pause, next, previous, search"


def set_volume(level: int, agent=None) -> str:
    """Set macOS system output volume (0–100)."""
    level = max(0, min(100, int(level)))
    try:
        subprocess.run(
            ["osascript", "-e", f"set volume output volume {level}"],
            check=True,
        )
        return f"Volume set to {level}%."
    except Exception as e:
        return f"Volume change failed: {e}"


def show_news_stream(channel: str = "", agent=None) -> str:
    """Switch the HUD to the news panel."""
    if agent is not None:
        agent.pending_actions.append({
            "type":    "switch_tab",
            "tab":     "news",
            "channel": channel,
        })
    return f"Switching to news stream{': ' + channel if channel else ''}."
