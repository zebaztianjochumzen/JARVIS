"""Runtime settings — live, persisted key-value store for JARVIS configuration.

Priority: env vars (set at startup) < ~/.jarvis/settings.json < API PATCH calls.
Persists to ~/.jarvis/settings.json so changes survive restarts.
"""

import json
import os
from pathlib import Path

_SETTINGS_FILE = Path.home() / ".jarvis" / "settings.json"

# Default values (env vars used as seed where applicable)
_DEFAULTS: dict = {
    "location":           "Stockholm",
    "whisper_model":      os.environ.get("WHISPER_MODEL", "base"),
    "wakeword_enabled":   True,
    "wakeword_threshold": float(os.environ.get("WAKEWORD_THRESHOLD", "0.5")),
    "briefing_hour":      int(os.environ.get("BRIEFING_HOUR", "8")),
    "alert_tickers":      os.environ.get("ALERT_TICKERS", "AAPL,NVDA,BTC-USD"),
    "price_alert_pct":    float(os.environ.get("PRICE_ALERT_PCT", "2.5")),
    "tts_voice":          "en-US-GuyNeural",
    "browser_headless":   os.environ.get("BROWSER_HEADLESS", "1") not in ("0", "false", "no"),
    "obsidian_vault_path": os.environ.get("OBSIDIAN_VAULT_PATH", ""),
    "stocks_watchlist":   "AAPL,NVDA,TSLA,MSFT,GOOGL,BTC-USD",
    "stream_url":         "",
    "email_digest_enabled": os.environ.get("EMAIL_DIGEST_ENABLED", "0") == "1",
}

_current: dict = {}


def load() -> None:
    global _current
    _current = dict(_DEFAULTS)
    if _SETTINGS_FILE.exists():
        try:
            stored = json.loads(_SETTINGS_FILE.read_text(encoding="utf-8"))
            _current.update({k: v for k, v in stored.items() if k in _DEFAULTS})
        except Exception:
            pass


def get(key: str, default=None):
    return _current.get(key, default)


def get_all() -> dict:
    return dict(_current)


def update(updates: dict) -> dict:
    """Apply a partial update, persist to disk, and return the new full settings."""
    _current.update({k: v for k, v in updates.items() if k in _DEFAULTS})
    _persist()
    return get_all()


def _persist() -> None:
    try:
        _SETTINGS_FILE.parent.mkdir(parents=True, exist_ok=True)
        _SETTINGS_FILE.write_text(json.dumps(_current, indent=2), encoding="utf-8")
    except Exception:
        pass


# Load on import so every module that does `from jarvis import runtime_settings`
# gets the live values immediately.
load()
