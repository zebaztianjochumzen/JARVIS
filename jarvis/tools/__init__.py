"""Tool registry — exposes TOOLS list and execute_tool() to the agent."""

from jarvis.tools.basic    import get_current_time, save_note, remember_this, recall_fact, forget_fact
from jarvis.tools.routing  import plan_route
from jarvis.tools.vision   import look_at_desk
from jarvis.tools.info     import web_search, get_news, get_weather, get_stock_price, get_market_summary
from jarvis.tools.system   import set_timer, open_app, run_shell, take_screenshot, read_clipboard, write_clipboard
from jarvis.tools.dev      import read_file, write_file, git_status, run_tests, search_codebase
from jarvis.tools.map_tools import show_location, search_nearby
from jarvis.tools.media    import play_music, set_volume, show_news_stream

# ── JSON schemas for Claude's tool use API ────────────────────────────────────
TOOLS: list[dict] = [

    # ── Basic ──────────────────────────────────────────────────────────────────
    {
        "name": "get_current_time",
        "description": "Returns the current local date and time.",
        "input_schema": {"type": "object", "properties": {}, "required": []},
    },
    {
        "name": "save_note",
        "description": "Appends a note to the user's local notes file.",
        "input_schema": {
            "type": "object",
            "properties": {"content": {"type": "string", "description": "Note text."}},
            "required": ["content"],
        },
    },
    {
        "name": "remember_this",
        "description": "Stores a fact about the user in persistent memory for future conversations.",
        "input_schema": {
            "type": "object",
            "properties": {
                "key":   {"type": "string", "description": "Short label, e.g. 'user_name'."},
                "value": {"type": "string", "description": "The value to store."},
            },
            "required": ["key", "value"],
        },
    },
    {
        "name": "recall_fact",
        "description": "Retrieves a stored fact from memory by key.",
        "input_schema": {
            "type": "object",
            "properties": {"key": {"type": "string"}},
            "required": ["key"],
        },
    },
    {
        "name": "forget_fact",
        "description": "Deletes a stored fact from memory.",
        "input_schema": {
            "type": "object",
            "properties": {"key": {"type": "string"}},
            "required": ["key"],
        },
    },

    # ── Information ────────────────────────────────────────────────────────────
    {
        "name": "web_search",
        "description": "Searches the web using DuckDuckGo and returns the top results. Use for current events, facts, or anything not in training data.",
        "input_schema": {
            "type": "object",
            "properties": {
                "query":       {"type": "string",  "description": "Search query."},
                "num_results": {"type": "integer", "description": "Number of results (default 5)."},
            },
            "required": ["query"],
        },
    },
    {
        "name": "get_news",
        "description": "Fetches the latest news headlines from Swedish news sources (SVT, Aftonbladet, DI). Optionally filter by topic.",
        "input_schema": {
            "type": "object",
            "properties": {
                "topic":        {"type": "string",  "description": "Filter topic, e.g. 'economy'. Leave empty for all news."},
                "num_articles": {"type": "integer", "description": "Number of articles (default 6)."},
            },
            "required": [],
        },
    },
    {
        "name": "get_weather",
        "description": "Returns current weather and 5-day forecast for a city.",
        "input_schema": {
            "type": "object",
            "properties": {"city": {"type": "string", "description": "City name (default: Stockholm)."}},
            "required": [],
        },
    },
    {
        "name": "get_stock_price",
        "description": "Returns the latest price and daily change for a stock or crypto ticker.",
        "input_schema": {
            "type": "object",
            "properties": {"ticker": {"type": "string", "description": "Ticker symbol, e.g. AAPL, BTC-USD."}},
            "required": ["ticker"],
        },
    },
    {
        "name": "get_market_summary",
        "description": "Returns a snapshot of major market indices: S&P 500, NASDAQ, Dow Jones, VIX.",
        "input_schema": {"type": "object", "properties": {}, "required": []},
    },

    # ── System ─────────────────────────────────────────────────────────────────
    {
        "name": "set_timer",
        "description": "Sets a countdown timer that fires a macOS notification when it expires.",
        "input_schema": {
            "type": "object",
            "properties": {
                "duration_seconds": {"type": "integer", "description": "Timer duration in seconds."},
                "label":            {"type": "string",  "description": "Timer label shown in the notification."},
            },
            "required": ["duration_seconds"],
        },
    },
    {
        "name": "open_app",
        "description": "Opens a macOS application by name (e.g. 'Safari', 'Spotify', 'Terminal').",
        "input_schema": {
            "type": "object",
            "properties": {"app_name": {"type": "string", "description": "Exact macOS app name."}},
            "required": ["app_name"],
        },
    },
    {
        "name": "run_shell",
        "description": "Runs an allowlisted shell command and returns its output. Allowed: ls, pwd, date, cat, grep, find, curl, ping, df, ps, uptime, etc.",
        "input_schema": {
            "type": "object",
            "properties": {"command": {"type": "string", "description": "Shell command to run."}},
            "required": ["command"],
        },
    },
    {
        "name": "take_screenshot",
        "description": "Captures the current screen and describes what is visible using Claude Vision.",
        "input_schema": {"type": "object", "properties": {}, "required": []},
    },
    {
        "name": "read_clipboard",
        "description": "Reads the current macOS clipboard contents.",
        "input_schema": {"type": "object", "properties": {}, "required": []},
    },
    {
        "name": "write_clipboard",
        "description": "Writes text to the macOS clipboard.",
        "input_schema": {
            "type": "object",
            "properties": {"text": {"type": "string", "description": "Text to copy to clipboard."}},
            "required": ["text"],
        },
    },

    # ── Developer ──────────────────────────────────────────────────────────────
    {
        "name": "read_file",
        "description": "Reads a file from the JARVIS workspace (up to 200 lines). Path is relative to repo root.",
        "input_schema": {
            "type": "object",
            "properties": {"path": {"type": "string", "description": "Relative file path, e.g. 'jarvis/agent.py'."}},
            "required": ["path"],
        },
    },
    {
        "name": "write_file",
        "description": "Writes or overwrites a file in the JARVIS workspace. Path is relative to repo root.",
        "input_schema": {
            "type": "object",
            "properties": {
                "path":    {"type": "string", "description": "Relative file path."},
                "content": {"type": "string", "description": "Full file content."},
            },
            "required": ["path", "content"],
        },
    },
    {
        "name": "git_status",
        "description": "Returns the current git branch, working-tree status, and recent commit log for the JARVIS repo.",
        "input_schema": {"type": "object", "properties": {}, "required": []},
    },
    {
        "name": "run_tests",
        "description": "Runs pytest on the JARVIS project and returns the results.",
        "input_schema": {
            "type": "object",
            "properties": {"test_path": {"type": "string", "description": "Path to test file or directory (default: '.')."}},
            "required": [],
        },
    },
    {
        "name": "search_codebase",
        "description": "Searches the JARVIS codebase for a pattern using ripgrep/grep and returns matching lines.",
        "input_schema": {
            "type": "object",
            "properties": {
                "pattern": {"type": "string", "description": "Search pattern (regex or plain text)."},
                "path":    {"type": "string", "description": "Sub-directory to search (default: '.' for all)."},
            },
            "required": ["pattern"],
        },
    },

    # ── Map ────────────────────────────────────────────────────────────────────
    {
        "name": "plan_route",
        "description": "Plans a driving route between two locations and draws it on the map.",
        "input_schema": {
            "type": "object",
            "properties": {
                "origin":      {"type": "string", "description": "Starting location."},
                "destination": {"type": "string", "description": "Destination location."},
            },
            "required": ["origin", "destination"],
        },
    },
    {
        "name": "show_location",
        "description": "Flies the map to a named place (city, address, landmark).",
        "input_schema": {
            "type": "object",
            "properties": {"place": {"type": "string", "description": "Place name, e.g. 'Tokyo' or 'Eiffel Tower'."}},
            "required": ["place"],
        },
    },
    {
        "name": "search_nearby",
        "description": "Finds places of interest (restaurants, hospitals, parks, etc.) near a location.",
        "input_schema": {
            "type": "object",
            "properties": {
                "query":    {"type": "string", "description": "What to search for, e.g. 'coffee shop'."},
                "location": {"type": "string", "description": "Anchor location (default: Stockholm)."},
            },
            "required": ["query"],
        },
    },

    # ── Vision ─────────────────────────────────────────────────────────────────
    {
        "name": "look_at_desk",
        "description": "Captures a frame from the MacBook camera and describes what is visible on the desk.",
        "input_schema": {
            "type": "object",
            "properties": {
                "question": {"type": "string", "description": "Specific question about the camera view."},
            },
            "required": [],
        },
    },

    # ── Media ──────────────────────────────────────────────────────────────────
    {
        "name": "play_music",
        "description": "Controls Spotify playback on macOS. Actions: play, pause, next, previous, search.",
        "input_schema": {
            "type": "object",
            "properties": {
                "action": {"type": "string", "description": "One of: play, pause, next, previous, search."},
                "query":  {"type": "string", "description": "Search query (required when action is 'search')."},
            },
            "required": ["action"],
        },
    },
    {
        "name": "set_volume",
        "description": "Sets the macOS system output volume (0–100).",
        "input_schema": {
            "type": "object",
            "properties": {"level": {"type": "integer", "description": "Volume level 0–100."}},
            "required": ["level"],
        },
    },
    {
        "name": "show_news_stream",
        "description": "Switches the JARVIS HUD to the news panel.",
        "input_schema": {
            "type": "object",
            "properties": {"channel": {"type": "string", "description": "Optional channel name to mention."}},
            "required": [],
        },
    },
]

# ── Dispatch ──────────────────────────────────────────────────────────────────
_MEMORY_TOOLS = {"remember_this", "recall_fact", "forget_fact"}
_AGENT_TOOLS  = {
    "plan_route", "look_at_desk",
    "show_location", "search_nearby", "show_news_stream",
    "play_music",
}

_DISPATCH: dict = {
    "get_current_time":  get_current_time,
    "save_note":         save_note,
    "remember_this":     remember_this,
    "recall_fact":       recall_fact,
    "forget_fact":       forget_fact,
    # info
    "web_search":        web_search,
    "get_news":          get_news,
    "get_weather":       get_weather,
    "get_stock_price":   get_stock_price,
    "get_market_summary":get_market_summary,
    # system
    "set_timer":         set_timer,
    "open_app":          open_app,
    "run_shell":         run_shell,
    "take_screenshot":   take_screenshot,
    "read_clipboard":    read_clipboard,
    "write_clipboard":   write_clipboard,
    # dev
    "read_file":         read_file,
    "write_file":        write_file,
    "git_status":        git_status,
    "run_tests":         run_tests,
    "search_codebase":   search_codebase,
    # map
    "plan_route":        plan_route,
    "show_location":     show_location,
    "search_nearby":     search_nearby,
    # vision
    "look_at_desk":      look_at_desk,
    # media
    "play_music":        play_music,
    "set_volume":        set_volume,
    "show_news_stream":  show_news_stream,
}


def execute_tool(name: str, tool_input: dict, memory: object, agent=None) -> str:
    fn = _DISPATCH.get(name)
    if fn is None:
        return f"Unknown tool: {name}"
    if name in _MEMORY_TOOLS:
        return fn(memory=memory, **tool_input)
    if name in _AGENT_TOOLS:
        return fn(agent=agent, **tool_input)
    return fn(**tool_input)
