"""YouTube Data API v3 — search videos and open them in the JARVIS browser panel."""

import os
import requests

_SEARCH_URL = "https://www.googleapis.com/youtube/v3/search"
_VIDEO_URL  = "https://www.youtube.com/watch?v="


def _key() -> str:
    key = os.environ.get("GOOGLE_API_KEY", "").strip()
    if not key:
        raise RuntimeError("GOOGLE_API_KEY not configured.")
    return key


def youtube_search(query: str, max_results: int = 5, agent=None) -> str:
    """Search YouTube and return the top results. Opens the first video in the browser panel."""
    try:
        r = requests.get(_SEARCH_URL, params={
            "part":       "snippet",
            "q":          query,
            "type":       "video",
            "maxResults": min(max_results, 8),
            "key":        _key(),
        }, timeout=10)
        data = r.json()

        items = data.get("items", [])
        if not items:
            return f"No YouTube results for '{query}'."

        lines = [f"YouTube results for '{query}':"]
        first_url = None
        for i, item in enumerate(items, 1):
            vid_id  = item["id"]["videoId"]
            snippet = item["snippet"]
            title   = snippet["title"]
            channel = snippet["channelTitle"]
            url     = _VIDEO_URL + vid_id
            lines.append(f"  {i}. {title} — {channel}\n     {url}")
            if i == 1:
                first_url = url

        if first_url and agent is not None:
            agent.pending_actions.append({"type": "show_browser", "url": first_url})

        return "\n".join(lines)

    except RuntimeError as e:
        return str(e)
    except Exception as e:
        return f"YouTube search failed: {e}"
