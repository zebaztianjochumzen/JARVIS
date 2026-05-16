"""Tool registry — exposes TOOLS list and execute_tool() to the agent."""

from jarvis.tools.basic    import get_current_time, save_note, remember_this, recall_fact, forget_fact, recall_semantic
from jarvis.tools.routing  import plan_route
from jarvis.tools.vision   import look_at_desk
from jarvis.tools.info     import web_search, get_news, get_weather, get_stock_price, get_market_summary
from jarvis.tools.system   import set_timer, open_app, open_url, run_shell, take_screenshot, read_clipboard, write_clipboard
from jarvis.tools.dev      import read_file, write_file, git_status, run_tests, search_codebase
from jarvis.tools.map_tools import show_location, search_nearby
from jarvis.tools.media    import play_music, set_volume, show_news_stream, show_stocks, show_briefing, navigate_to
from jarvis.tools.files    import list_files, find_file, open_file, get_file_info, move_file, delete_file
from jarvis.tools.creator  import create_document, draft_email, translate, detect_language, generate_html, write_code
from jarvis.tools.calendar_tool import get_calendar_events, create_calendar_event, delete_calendar_event, show_calendar
from jarvis.tools.gmail_tool    import read_gmail_inbox, search_gmail, gmail_triage
from jarvis.tools.browser_tool  import (
    browser_navigate, browser_extract_text, browser_click,
    browser_fill, browser_screenshot, browser_execute_js,
)
from jarvis.tools.system_vitals  import get_system_vitals
from jarvis.tools.orchestration  import spawn_parallel_research, parallel_web_search

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
    {
        "name": "recall_semantic",
        "description": (
            "Search memory by MEANING rather than exact key. Use this when the user asks "
            "something like 'what do you know about my work' or 'anything related to music' "
            "and you are not sure of the exact fact key. Returns the most relevant stored facts."
        ),
        "input_schema": {
            "type": "object",
            "properties": {
                "query": {"type": "string", "description": "Natural-language description of what to search for."},
            },
            "required": ["query"],
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
        "name": "open_url",
        "description": "Opens a URL or website in Chrome. Supports shortcuts: youtube, gmail, google, github, reddit, spotify, netflix, chatgpt, linkedin, twitter.",
        "input_schema": {
            "type": "object",
            "properties": {
                "url":     {"type": "string", "description": "Full URL or shortcut name like 'youtube'."},
                "browser": {"type": "string", "description": "Browser app name (default: Google Chrome)."},
            },
            "required": ["url"],
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
        "description": "Switches the JARVIS HUD to the news panel AND fetches today's top headlines so you can summarise them verbally.",
        "input_schema": {
            "type": "object",
            "properties": {"channel": {"type": "string", "description": "Optional channel name."}},
            "required": [],
        },
    },
    {
        "name": "show_stocks",
        "description": "Switches the JARVIS HUD to the stocks panel AND fetches a live market summary so you can read it out.",
        "input_schema": {"type": "object", "properties": {}, "required": []},
    },
    {
        "name": "show_briefing",
        "description": "Switches the JARVIS HUD to the daily briefing panel AND fetches weather + market snapshot for spoken delivery.",
        "input_schema": {"type": "object", "properties": {}, "required": []},
    },
    {
        "name": "navigate_to",
        "description": "Navigates the JARVIS HUD to any named panel. Use for music, camera, map, terminal, settings, or home.",
        "input_schema": {
            "type": "object",
            "properties": {"tab": {"type": "string", "description": "One of: home, briefing, stocks, news, map, terminal, music, camera, settings."}},
            "required": ["tab"],
        },
    },

    # ── Files ──────────────────────────────────────────────────────────────────
    {
        "name": "list_files",
        "description": "Lists files and folders in a directory on the user's Mac.",
        "input_schema": {
            "type": "object",
            "properties": {
                "directory": {"type": "string", "description": "Directory path (default: home ~). Use ~ for shortcuts like ~/Desktop."},
                "pattern":   {"type": "string", "description": "Glob pattern filter, e.g. '*.pdf' (default: all)."},
            },
            "required": [],
        },
    },
    {
        "name": "find_file",
        "description": "Searches for files by name pattern under a directory.",
        "input_schema": {
            "type": "object",
            "properties": {
                "name":        {"type": "string", "description": "Filename or glob pattern, e.g. '*.pdf' or 'report*.docx'."},
                "search_path": {"type": "string", "description": "Root directory to search (default: ~)."},
            },
            "required": ["name"],
        },
    },
    {
        "name": "open_file",
        "description": "Opens a file or folder with the default macOS application.",
        "input_schema": {
            "type": "object",
            "properties": {"path": {"type": "string", "description": "Full or ~ path to the file."}},
            "required": ["path"],
        },
    },
    {
        "name": "get_file_info",
        "description": "Returns metadata about a file: type, size, creation and modification dates.",
        "input_schema": {
            "type": "object",
            "properties": {"path": {"type": "string", "description": "Path to the file."}},
            "required": ["path"],
        },
    },
    {
        "name": "move_file",
        "description": "Moves or renames a file or folder.",
        "input_schema": {
            "type": "object",
            "properties": {
                "source":      {"type": "string", "description": "Current path."},
                "destination": {"type": "string", "description": "New path or directory."},
            },
            "required": ["source", "destination"],
        },
    },
    {
        "name": "delete_file",
        "description": "Moves a file to the macOS Trash (safe, recoverable).",
        "input_schema": {
            "type": "object",
            "properties": {"path": {"type": "string", "description": "Path to the file to trash."}},
            "required": ["path"],
        },
    },

    # ── Calendar ───────────────────────────────────────────────────────────────
    {
        "name": "show_calendar",
        "description": "Navigate the HUD to the calendar panel and return today's events for spoken delivery. Use when user asks about their schedule, meetings, or what's on today.",
        "input_schema": {
            "type": "object",
            "properties": {
                "days_ahead": {"type": "integer", "description": "How many days ahead to show (default 1 = today only)."},
            },
            "required": [],
        },
    },
    {
        "name": "get_calendar_events",
        "description": "Fetch upcoming Google Calendar events without navigating. Use for quick lookups or when already on the calendar panel.",
        "input_schema": {
            "type": "object",
            "properties": {
                "days_ahead":   {"type": "integer", "description": "Number of days ahead to fetch (default 1)."},
                "max_results":  {"type": "integer", "description": "Max events to return (default 15)."},
            },
            "required": [],
        },
    },
    {
        "name": "create_calendar_event",
        "description": "Create a new event in Google Calendar. Start and end times must be ISO 8601 format (e.g. 2026-05-12T14:00:00).",
        "input_schema": {
            "type": "object",
            "properties": {
                "title":       {"type": "string", "description": "Event title."},
                "start_time":  {"type": "string", "description": "Start time in ISO 8601."},
                "end_time":    {"type": "string", "description": "End time in ISO 8601."},
                "description": {"type": "string", "description": "Optional event description."},
                "location":    {"type": "string", "description": "Optional location."},
            },
            "required": ["title", "start_time", "end_time"],
        },
    },
    {
        "name": "delete_calendar_event",
        "description": "Delete a Google Calendar event by its event ID.",
        "input_schema": {
            "type": "object",
            "properties": {
                "event_id": {"type": "string", "description": "The Google Calendar event ID."},
            },
            "required": ["event_id"],
        },
    },

    # ── Gmail ──────────────────────────────────────────────────────────────────
    {
        "name": "read_gmail_inbox",
        "description": "Fetch recent emails from Gmail inbox. Set unread_only=true to see only unread messages.",
        "input_schema": {
            "type": "object",
            "properties": {
                "max_results":  {"type": "integer", "description": "How many emails to fetch (default 10, max 20)."},
                "unread_only":  {"type": "boolean", "description": "If true, only fetch unread emails (default false)."},
            },
            "required": [],
        },
    },
    {
        "name": "search_gmail",
        "description": "Search Gmail with a query string. Supports Gmail search operators e.g. 'from:boss@company.com', 'subject:invoice is:unread', 'after:2026/05/01'.",
        "input_schema": {
            "type": "object",
            "properties": {
                "query":       {"type": "string",  "description": "Gmail search query string."},
                "max_results": {"type": "integer", "description": "Number of results (default 5)."},
            },
            "required": ["query"],
        },
    },
    {
        "name": "gmail_triage",
        "description": "Fetch all unread inbox emails and categorise them as URGENT / ACTION / FYI with a one-line summary of each. Call this when the user says 'triage my inbox', 'what emails need attention', or 'run email triage'.",
        "input_schema": {"type": "object", "properties": {}, "required": []},
    },

    # ── System vitals ──────────────────────────────────────────────────────────
    {
        "name": "get_system_vitals",
        "description": "Returns live CPU%, RAM usage, disk usage, and network I/O for the host machine. Use when the user asks about performance, resource usage, or system health.",
        "input_schema": {"type": "object", "properties": {}, "required": []},
    },

    # ── Browser automation ─────────────────────────────────────────────────────
    {
        "name": "browser_navigate",
        "description": "Navigate the embedded Playwright browser to a URL and return the page title and visible text. Use for reading web pages, filling in forms, or automating web tasks.",
        "input_schema": {
            "type": "object",
            "properties": {"url": {"type": "string", "description": "Full URL (https://...) or domain."}},
            "required": ["url"],
        },
    },
    {
        "name": "browser_extract_text",
        "description": "Extract all visible text from the page currently loaded in the Playwright browser.",
        "input_schema": {"type": "object", "properties": {}, "required": []},
    },
    {
        "name": "browser_click",
        "description": "Click a web element by its visible text label or CSS selector.",
        "input_schema": {
            "type": "object",
            "properties": {"target": {"type": "string", "description": "Visible text or CSS selector of the element to click."}},
            "required": ["target"],
        },
    },
    {
        "name": "browser_fill",
        "description": "Type text into an input field or textarea identified by a CSS selector.",
        "input_schema": {
            "type": "object",
            "properties": {
                "selector": {"type": "string", "description": "CSS selector for the input element."},
                "value":    {"type": "string", "description": "Text to type."},
            },
            "required": ["selector", "value"],
        },
    },
    {
        "name": "browser_screenshot",
        "description": "Take a screenshot of the current browser page and return a Claude Vision description of what is visible.",
        "input_schema": {"type": "object", "properties": {}, "required": []},
    },
    {
        "name": "browser_execute_js",
        "description": "Run arbitrary JavaScript in the current browser page and return the result.",
        "input_schema": {
            "type": "object",
            "properties": {"code": {"type": "string", "description": "JavaScript expression to evaluate."}},
            "required": ["code"],
        },
    },

    # ── Messaging (OpenClaw multi-platform) ────────────────────────────────────
    {
        "name": "send_telegram",
        "description": "Send a proactive message to the user's Telegram chat. Use for alerts, reminders, price notifications, or anything the user should know even when the HUD isn't open.",
        "input_schema": {
            "type": "object",
            "properties": {"text": {"type": "string", "description": "Message text to send."}},
            "required": ["text"],
        },
    },
    {
        "name": "send_message",
        "description": "Broadcast a message to ALL connected OpenClaw channels (Telegram, WhatsApp, Discord, Signal). Prefer this over send_telegram when OpenClaw is configured.",
        "input_schema": {
            "type": "object",
            "properties": {"text": {"type": "string", "description": "Message text to broadcast."}},
            "required": ["text"],
        },
    },

    # ── Orchestration (multi-agent) ────────────────────────────────────────────
    {
        "name": "spawn_parallel_research",
        "description": (
            "Spawn parallel research sub-agents for multiple topics simultaneously. "
            "Use when the user asks to compare or research several distinct subjects at once. "
            "E.g. 'research the top 5 AI chip companies' → topics=['NVIDIA','AMD','Intel','Qualcomm','Apple']."
        ),
        "input_schema": {
            "type": "object",
            "properties": {
                "topics":         {"type": "array",  "items": {"type": "string"}, "description": "List of topics to research in parallel (max 8)."},
                "query_template": {"type": "string", "description": "Query template with {topic} placeholder, e.g. 'latest news on {topic}'. Default: '{topic}'."},
            },
            "required": ["topics"],
        },
    },
    {
        "name": "parallel_web_search",
        "description": (
            "Run multiple DuckDuckGo searches simultaneously and return all results merged. "
            "Faster than sequential tool calls when you need information from several independent queries."
        ),
        "input_schema": {
            "type": "object",
            "properties": {
                "queries": {"type": "array", "items": {"type": "string"}, "description": "List of search queries to run in parallel (max 6)."},
            },
            "required": ["queries"],
        },
    },

    # ── Creator ────────────────────────────────────────────────────────────────
    {
        "name": "create_document",
        "description": "Creates a text, markdown, HTML, or code file on the Desktop with the given content and opens it.",
        "input_schema": {
            "type": "object",
            "properties": {
                "filename":  {"type": "string", "description": "Filename without extension, e.g. 'meeting_notes'."},
                "content":   {"type": "string", "description": "Full file content."},
                "file_type": {"type": "string", "description": "Type: txt, md, html, py, js, css (default: txt)."},
            },
            "required": ["filename", "content"],
        },
    },
    {
        "name": "draft_email",
        "description": "Opens Apple Mail with a pre-filled email draft ready to send.",
        "input_schema": {
            "type": "object",
            "properties": {
                "to":      {"type": "string", "description": "Recipient email address."},
                "subject": {"type": "string", "description": "Email subject."},
                "body":    {"type": "string", "description": "Email body text."},
            },
            "required": ["to", "subject", "body"],
        },
    },
    {
        "name": "translate",
        "description": "Translates text to a target language using Claude AI.",
        "input_schema": {
            "type": "object",
            "properties": {
                "text":            {"type": "string", "description": "Text to translate."},
                "target_language": {"type": "string", "description": "Target language, e.g. 'Swedish', 'Spanish', 'French'."},
            },
            "required": ["text", "target_language"],
        },
    },
    {
        "name": "detect_language",
        "description": "Detects the language of a piece of text.",
        "input_schema": {
            "type": "object",
            "properties": {"text": {"type": "string", "description": "Text to identify."}},
            "required": ["text"],
        },
    },
    {
        "name": "generate_html",
        "description": "Generates a complete HTML page from a description, saves it to the Desktop, and opens it in the browser.",
        "input_schema": {
            "type": "object",
            "properties": {
                "description": {"type": "string", "description": "What the HTML page should contain or do."},
                "filename":    {"type": "string", "description": "Output filename without .html extension (default: jarvis_page)."},
            },
            "required": ["description"],
        },
    },
    {
        "name": "write_code",
        "description": "Generates code from a description, saves it to the Desktop, and opens it.",
        "input_schema": {
            "type": "object",
            "properties": {
                "description": {"type": "string", "description": "What the code should do."},
                "filename":    {"type": "string", "description": "Output filename without extension."},
                "language":    {"type": "string", "description": "Programming language: python, js, html, css (default: python)."},
            },
            "required": ["description", "filename"],
        },
    },
]

# ── Messaging dispatch helpers ────────────────────────────────────────────────

def _send_telegram_dispatch(text: str) -> str:
    try:
        from jarvis import telegram_bot
        return telegram_bot.send_message(text)
    except ImportError:
        return "Telegram module not available."


def _send_message_dispatch(text: str) -> str:
    """Broadcast to all connected OpenClaw channels; fall back to Telegram."""
    try:
        from jarvis import openclaw_gateway
        if openclaw_gateway._gateway_ok:
            # OpenClaw gateway is up — it handles multi-platform routing
            # The gateway broadcasts via its own channel connections.
            # We also push via Telegram as a reliable fallback.
            try:
                from jarvis import telegram_bot
                telegram_bot.send_message(text)
            except Exception:
                pass
            return "Message broadcast to all OpenClaw channels."
    except ImportError:
        pass
    # Fallback: Telegram only
    return _send_telegram_dispatch(text)


# ── Dispatch ──────────────────────────────────────────────────────────────────
_MEMORY_TOOLS = {"remember_this", "recall_fact", "forget_fact", "recall_semantic"}
_AGENT_TOOLS  = {
    "plan_route", "look_at_desk",
    "show_location", "search_nearby",
    "show_news_stream", "show_stocks", "show_briefing", "navigate_to",
    "play_music",
    "list_files", "find_file", "open_file", "get_file_info", "move_file", "delete_file",
    "open_url", "open_app",
    "create_document", "draft_email", "translate", "detect_language", "generate_html", "write_code",
    "show_calendar", "get_calendar_events", "create_calendar_event", "delete_calendar_event",
    "read_gmail_inbox", "search_gmail", "gmail_triage",
}

_DISPATCH: dict = {
    "get_current_time":  get_current_time,
    "save_note":         save_note,
    "remember_this":     remember_this,
    "recall_fact":       recall_fact,
    "forget_fact":       forget_fact,
    "recall_semantic":   recall_semantic,
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
    # media / navigation
    "play_music":        play_music,
    "set_volume":        set_volume,
    "show_news_stream":  show_news_stream,
    "show_stocks":       show_stocks,
    "show_briefing":     show_briefing,
    "navigate_to":       navigate_to,
    # files
    "list_files":        list_files,
    "find_file":         find_file,
    "open_file":         open_file,
    "get_file_info":     get_file_info,
    "move_file":         move_file,
    "delete_file":       delete_file,
    # calendar
    "show_calendar":          show_calendar,
    "get_calendar_events":    get_calendar_events,
    "create_calendar_event":  create_calendar_event,
    "delete_calendar_event":  delete_calendar_event,
    # gmail
    "read_gmail_inbox":  read_gmail_inbox,
    "search_gmail":      search_gmail,
    "gmail_triage":      gmail_triage,
    # creator
    "create_document":   create_document,
    "draft_email":       draft_email,
    "translate":         translate,
    "detect_language":   detect_language,
    "generate_html":     generate_html,
    "write_code":        write_code,
    # web
    "open_url":          open_url,
    # system vitals
    "get_system_vitals":     get_system_vitals,
    # browser automation
    "browser_navigate":      browser_navigate,
    "browser_extract_text":  browser_extract_text,
    "browser_click":         browser_click,
    "browser_fill":          browser_fill,
    "browser_screenshot":    browser_screenshot,
    "browser_execute_js":    browser_execute_js,
    # telegram / openclaw messaging
    "send_telegram":              _send_telegram_dispatch,
    "send_message":               _send_message_dispatch,
    # orchestration
    "spawn_parallel_research":    spawn_parallel_research,
    "parallel_web_search":        parallel_web_search,
}


# Auto-navigate to a panel whenever certain tools are called
_TAB_FOR_TOOL: dict[str, str] = {
    "get_news":           "news",
    "show_news_stream":   "news",
    "get_stock_price":    "stocks",
    "get_market_summary": "stocks",
    "show_stocks":        "stocks",
    "get_weather":        "briefing",
    "show_briefing":      "briefing",
    "plan_route":         "map",
    "show_location":      "map",
    "search_nearby":      "map",
    "look_at_desk":       "camera",
    "show_calendar":      "calendar",
    "get_calendar_events":"calendar",
}


def execute_tool(name: str, tool_input: dict, memory: object, agent=None, action_callback=None) -> str:
    # Route MCP tools through the MCP client
    if name.startswith("mcp_"):
        try:
            from jarvis import mcp_client
            return mcp_client.call_tool_sync(name, tool_input)
        except ImportError:
            return "MCP client not available."

    # ── Approval gate for dangerous tools ─────────────────────────────────────
    try:
        from jarvis.approval import needs_approval, request_approval
        if needs_approval(name):
            if action_callback:
                action_callback({"type": "approval_pending", "tool": name, "input": tool_input})
            approved = request_approval(name, tool_input)
            if not approved:
                return f"Cancelled: '{name}' was denied or timed out."
    except ImportError:
        pass

    fn = _DISPATCH.get(name)
    if fn is None:
        return f"Unknown tool: {name}"

    # Fire timer_set event so the UI can show a countdown
    if name == 'set_timer' and 'duration_seconds' in tool_input:
        timer_action = {
            "type":             "timer_set",
            "duration_seconds": tool_input["duration_seconds"],
            "label":            tool_input.get("label", "Timer"),
        }
        if action_callback:
            action_callback(timer_action)
        elif agent is not None:
            agent.pending_actions.append(timer_action)

    # Fire switch_tab immediately via callback so the UI navigates during streaming
    if name in _TAB_FOR_TOOL:
        action = {"type": "switch_tab", "tab": _TAB_FOR_TOOL[name]}
        if action_callback:
            action_callback(action)
        elif agent is not None:
            agent.pending_actions.append(action)

    if name in _MEMORY_TOOLS:
        return fn(memory=memory, **tool_input)
    if name in _AGENT_TOOLS:
        result = fn(agent=agent, **tool_input)
    else:
        result = fn(**tool_input)

    # open_url returns the resolved URL — send it to the HUD browser panel
    if name == "open_url":
        action = {"type": "show_browser", "url": result}
        if action_callback:
            action_callback(action)
        elif agent is not None:
            agent.pending_actions.append(action)
        return f"Opening {result} in the JARVIS browser."

    return result
