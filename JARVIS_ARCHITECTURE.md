# JARVIS — Complete Architecture & Capability Reference

> **Stack:** Python 3.11 · FastAPI · Claude Sonnet 4.6 · React 19 · SQLite · Playwright · Whisper · OpenWakeWord · fastembed · edge-tts · yfinance · Telegram

---

## Table of Contents

1. [System Architecture](#1-system-architecture)
2. [Project File Structure](#2-project-file-structure)
3. [The AI Core — Agent Loop](#3-the-ai-core--agent-loop)
4. [Memory System](#4-memory-system)
5. [Tool Registry — All 55+ Tools](#5-tool-registry--all-55-tools)
6. [Voice Pipeline](#6-voice-pipeline)
7. [Autonomous Background Scheduler](#7-autonomous-background-scheduler)
8. [Telegram Bot](#8-telegram-bot)
9. [MCP Protocol Bridge](#9-mcp-protocol-bridge)
10. [Browser Automation](#10-browser-automation)
11. [Free Dictation Mode](#11-free-dictation-mode)
12. [HUD — Frontend Architecture](#12-hud--frontend-architecture)
13. [API Endpoint Reference](#13-api-endpoint-reference)
14. [End-to-End Data Flow](#14-end-to-end-data-flow)
15. [Configuration Reference](#15-configuration-reference)
16. [Dependency Graph](#16-dependency-graph)

---

## 1. System Architecture

```
┌─────────────────────────────────────────────────────────────────────┐
│                    BROWSER  (React 19 HUD)                          │
│                                                                     │
│  BootSequence · SystemVitals · Waveform · ToolTheater · TickerBar  │
│  11 Content Panels · NavBar · Orb · VoiceControl · GestureOverlay  │
└───────┬───────────────┬──────────────┬──────────────┬──────────────┘
        │ WebSocket /ws │ SSE /vitals  │ POST /tts    │ POST /transcribe
        │ JSON frames   │ 1 Hz metrics │ MP3 stream   │ audio → text
        ▼               ▼              ▼              ▼
┌─────────────────────────────────────────────────────────────────────┐
│                   FastAPI  (api/main.py)                            │
│                                                                     │
│  /ws           WebSocket gateway — streams tokens + tool events     │
│  /api/vitals   SSE — psutil CPU/RAM/NET every second               │
│  /api/tts      edge-tts neural TTS → streaming MP3                 │
│  /api/transcribe  faster-whisper STT ← audio blob                  │
│  /api/calendar    Google Calendar REST                              │
│  /api/stocks      yfinance watchlist                                │
│  /api/news        RSS aggregator                                    │
│  /api/briefing    weather snapshot                                  │
│  /api/memories    SQLite facts + Obsidian status                   │
│  /api/telegram/send  push Telegram message                         │
│  /api/browse      iframe proxy (strips X-Frame-Options)            │
└──────┬──────────────────────────────────────────────────────────────┘
       │ imports
       ▼
┌──────────────────────────────────────────────────────────────────┐
│                  JARVIS Backend  (jarvis/)                        │
│                                                                  │
│  agent.py          Claude Sonnet 4.6 · streaming · tool loop    │
│  memory.py         SQLite · embeddings · compression · Obsidian  │
│  obsidian.py       Vault sync — facts as markdown notes          │
│  scheduler.py      Daemon threads — briefing · alerts · digest   │
│  telegram_bot.py   pyTelegramBotAPI daemon thread                │
│  mcp_client.py     MCP stdio bridge — asyncio event loop         │
│  dictation.py      pynput hotkey → Whisper → paste              │
│  voice/stt.py      faster-whisper transcription                  │
│  voice/wakeword.py openwakeword "Hey JARVIS" detector            │
│  tools/            55+ tool implementations                      │
└──────────────────────────────────────────────────────────────────┘
       │
       ▼
┌──────────────────────────────────────────────────────────────────┐
│               External Services & Storage                         │
│                                                                  │
│  Anthropic API    Claude Sonnet 4.6 (inference)                 │
│  SQLite DB        ~/.jarvis/memory.db                           │
│  Obsidian Vault   <OBSIDIAN_VAULT_PATH>/JARVIS/                 │
│  Google APIs      Calendar + Gmail OAuth2                       │
│  wttr.in          Weather (no API key)                          │
│  DuckDuckGo       Web search (no API key)                       │
│  yfinance         Stock data (no API key)                       │
│  Telegram API     Bot messaging                                 │
│  AWS Secrets Mgr  API key storage (jarvis/secrets.py)          │
└──────────────────────────────────────────────────────────────────┘
```

---

## 2. Project File Structure

```
JARVIS/
├── api/
│   └── main.py                  FastAPI server — all HTTP + WebSocket endpoints
├── jarvis/
│   ├── agent.py                 Agent class — Claude inference loop + context compression
│   ├── memory.py                SQLite memory — facts, messages, embeddings, summaries
│   ├── obsidian.py              Obsidian vault sync — facts as .md notes
│   ├── scheduler.py             Autonomous background task scheduler
│   ├── telegram_bot.py          Telegram bot daemon thread
│   ├── mcp_client.py            MCP protocol client (asyncio)
│   ├── dictation.py             System-wide dictation hotkey
│   ├── secrets.py               AWS Secrets Manager / env var loader
│   ├── voice/
│   │   ├── stt.py               faster-whisper speech-to-text
│   │   └── wakeword.py          openwakeword "Hey JARVIS" listener
│   └── tools/
│       ├── __init__.py          Tool registry, TOOLS list, execute_tool()
│       ├── basic.py             Time, notes, memory tools
│       ├── info.py              Web search, news, weather, stocks
│       ├── system.py            Timer, apps, shell, screenshot, clipboard
│       ├── system_vitals.py     psutil CPU/RAM/disk/network
│       ├── dev.py               Files, git, tests, codebase search
│       ├── files.py             File manager (list, find, open, move, delete)
│       ├── creator.py           Document/code/email/HTML generator
│       ├── calendar_tool.py     Google Calendar OAuth2 + CRUD
│       ├── gmail_tool.py        Gmail OAuth2 — inbox, search, triage
│       ├── map_tools.py         Route planning, location, nearby search
│       ├── media.py             Spotify, volume, HUD panel navigation
│       ├── routing.py           Driving route solver
│       ├── vision.py            Webcam + Claude Vision
│       └── browser_tool.py      Playwright browser automation
├── frontend/
│   └── src/
│       ├── App.jsx              Root component — state, WebSocket, layout
│       ├── App.css              Global HUD styles
│       └── components/
│           ├── BootSequence.jsx  Cinematic startup animation
│           ├── SystemVitals.jsx  Live arc gauges (CPU/RAM/NET)
│           ├── Waveform.jsx      Audio waveform visualiser
│           ├── ToolTheater.jsx   Animated tool execution cards
│           ├── Orb.jsx           Central AI presence sphere
│           ├── Clock.jsx         Live digital clock
│           ├── NavBar.jsx        11-tab navigation
│           ├── TickerBar.jsx     Live stock + news ticker
│           ├── TimerRing.jsx     SVG countdown ring
│           ├── VoiceControl.jsx  PTT + mode toggle + wake-word UI
│           ├── GestureOverlay.jsx  Camera gesture recognition
│           ├── GridBackground.jsx  Animated grid backdrop
│           ├── BriefingPanel.jsx   Weather + daily summary
│           ├── StocksPanel.jsx     Live stock watchlist
│           ├── NewsPanel.jsx       RSS news feed
│           ├── MapPanel.jsx        Leaflet map + routing
│           ├── TerminalPanel.jsx   Tool log terminal
│           ├── CalendarPanel.jsx   Google Calendar view
│           ├── BrowserPanel.jsx    Playwright-powered iframe
│           ├── MusicPanel.jsx      Spotify control panel
│           ├── CameraPanel.jsx     Webcam + gesture feed
│           └── SettingsPanel.jsx   Configuration UI
├── vision/
│   └── server.py               YOLO + MediaPipe vision server (mounted at /vision)
├── mcp_servers.json            MCP server configuration
├── requirements.txt            Python dependencies
├── .env.example                Environment variable template
├── AGENT.md                    JARVIS system prompt / personality
└── JARVIS_ARCHITECTURE.md      This file
```

---

## 3. The AI Core — Agent Loop

### Model
**Claude Sonnet 4.6** (`claude-sonnet-4-6`) — Anthropic's production streaming model with native tool use. Every response is streamed token-by-token; there is no buffering before the user sees the first word.

### Agent Class (`jarvis/agent.py`)

```
Agent.__init__()
  ├── anthropic.Anthropic()          API client
  ├── Memory()                       SQLite connection
  ├── soul = AGENT.md / SOUL.md      System prompt file
  └── pending_actions: list[dict]    Queued HUD actions (tab switches, timers, etc.)
```

### `ask(user_input)` — Full Call Chain

```
1. memory.append_message("user", user_input)
      └── INSERT INTO messages (role="user", content=user_input)

2. should_compress(threshold=30)?
   ├── YES → _compress_context()
   │         ├── get_messages_for_compression(keep_recent=15)
   │         ├── Claude summarises oldest N messages (max_tokens=300)
   │         ├── memory.store_context_summary(summary, prune_ids)
   │         │     ├── DELETE FROM messages WHERE id IN prune_ids
   │         │     └── INSERT INTO context_summaries
   │         └── obsidian.write_daily_summary(summary)
   └── NO  → continue

3. messages = memory.get_messages_with_context(limit=20)
      ├── GET latest context_summary
      ├── IF summary → prepend {"role":"user","content":"[Context: ...]"}
      └── GET last 20 messages FROM messages ORDER BY id DESC

4. _run(messages)  ← main inference loop
   └── LOOP:
       a. mcp_client.get_mcp_tools() → all_tools = TOOLS + MCP_TOOLS
       b. client.messages.stream(
              model       = "claude-sonnet-4-6",
              max_tokens  = 1024,
              system      = soul + known facts block,
              tools       = all_tools,
              messages    = msg_list
          )
       c. For each token → stream_callback(token)
                          → WebSocket sends {"type":"token","text":token}
       d. stop_reason == "tool_use"?
          ├── YES → for each tool_use block:
          │         ├── execute_tool(name, input, memory, agent)
          │         ├── pending_actions.append(tool_log event)
          │         └── append tool_result to msg_list
          │         → LOOP back to (a)
          └── NO  → return full_text

5. memory.append_message("assistant", full_text)
6. WebSocket sends {"type":"done"}
7. pending_actions flushed → WebSocket sends each action JSON
```

### System Prompt Construction

Every inference call rebuilds the system prompt dynamically:

```python
soul_text + "\n\n## What you know about the user\n" + "\n".join(f"- {k}: {v}" for k, v in facts.items())
```

This means any fact remembered mid-conversation (`remember_this`) is immediately visible in the next turn's system prompt.

### Context Compression

When `len(messages) > 30`, the 15 oldest messages are summarised by Claude into 3–5 sentences and stored as a `context_summary`. The original rows are deleted from `messages`. The summary is injected as a synthetic `user` message at the head of every future context window. This keeps the effective context window bounded while preserving semantic continuity across arbitrarily long sessions.

---

## 4. Memory System

### Database: `~/.jarvis/memory.db`

```sql
CREATE TABLE messages (
    id         INTEGER PRIMARY KEY AUTOINCREMENT,
    role       TEXT NOT NULL,         -- 'user' | 'assistant'
    content    TEXT NOT NULL,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE facts (
    key        TEXT PRIMARY KEY,
    value      TEXT NOT NULL,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE fact_embeddings (
    key        TEXT PRIMARY KEY,
    embedding  TEXT NOT NULL          -- JSON array of floats (384-dim)
);

CREATE TABLE context_summaries (
    id         INTEGER PRIMARY KEY AUTOINCREMENT,
    summary    TEXT NOT NULL,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP
);
```

### Embedding Pipeline

**Model:** `fastembed` with `BAAI/bge-small-en-v1.5` (384 dimensions, ONNX runtime, CPU-only, ~33 MB).

```
set_fact(key, value)
  ├── UPSERT INTO facts
  ├── _embed(value) → 384-dim float vector
  ├── UPSERT INTO fact_embeddings (key, json.dumps(vector))
  └── obsidian.write_fact(key, value)

semantic_search(query, n=5)
  ├── _embed(query)
  ├── Load all fact_embeddings from DB
  ├── cosine_similarity(query_vec, each_fact_vec)  ← pure Python, no numpy
  ├── Sort by score DESC
  └── Return top-n (key, value, score) tuples
```

Cosine similarity is implemented in pure Python using `sum()` and `math.sqrt()` — no numpy, no GPU, no external ML library beyond fastembed itself.

### Obsidian Vault Sync

When `OBSIDIAN_VAULT_PATH` is set, every memory operation mirrors to disk:

```
<vault>/JARVIS/
├── Memory.md                  Auto-generated index of all facts (wikilinks)
├── Memory/
│   └── Facts/
│       ├── user_name.md       Individual fact note
│       ├── user_location.md
│       └── ...
├── Context.md                 Latest context compression summary
└── Daily/
    └── YYYY-MM-DD.md          Daily conversation summaries
```

Each fact note uses YAML frontmatter:
```yaml
---
type: jarvis-fact
key: user_name
created: 2026-05-12T09:14:00
updated: 2026-05-12T09:14:00
tags: [jarvis, memory]
---

Sebastian
```

All writes are wrapped in `try/except` — a missing vault or broken path never crashes the agent.

---

## 5. Tool Registry — All 55+ Tools

Tools are defined as JSON schemas in `jarvis/tools/__init__.py` and dispatched via `execute_tool()`. MCP tools are dynamically appended at inference time. The dispatch function handles three routing tiers:

```
execute_tool(name, input, memory, agent)
  ├── name.startswith("mcp_") → mcp_client.call_tool_sync(name, input)
  ├── name in _MEMORY_TOOLS   → fn(memory=memory, **input)
  ├── name in _AGENT_TOOLS    → fn(agent=agent, **input)
  └── else                    → fn(**input)
```

---

### Memory & Knowledge

| Tool | Description | Implementation |
|---|---|---|
| `remember_this(key, value)` | Store a persistent fact. Immediately updates the system prompt for the next turn and syncs to Obsidian. | SQLite UPSERT + fastembed vector + Obsidian write |
| `recall_fact(key)` | Exact key lookup. Returns value or "not found". | SQLite SELECT |
| `forget_fact(key)` | Delete a fact. Removes from DB, embeddings table, and Obsidian vault. | SQLite DELETE + Obsidian delete |
| `recall_semantic(query)` | Find the most relevant facts by meaning. Useful when the exact key is unknown. Returns top-5 with percentage match scores. | fastembed embed → cosine sort |
| `save_note(content)` | Append a timestamped line to `~/.jarvis/notes.txt`. | File append |

---

### Information

| Tool | Description | Source |
|---|---|---|
| `web_search(query, num_results=5)` | DuckDuckGo search — real-time results with title, URL, snippet. No API key required. | `duckduckgo-search` |
| `get_news(topic, num_articles=6)` | RSS aggregator across SVT Nyheter, Aftonbladet, Dagens Industri. Filters by topic keyword if provided. | `feedparser` + `requests` |
| `get_weather(city="Stockholm")` | Current conditions (temp, feels-like, humidity, wind) + 5-day forecast from wttr.in JSON API. | `wttr.in/City?format=j1` |
| `get_stock_price(ticker)` | Latest price, daily change, change%, volume for any yfinance ticker (stocks, ETFs, crypto). | `yfinance` |
| `get_market_summary()` | Snapshot of SPY (S&P 500), QQQ (NASDAQ), DIA (Dow Jones), VIX. | `yfinance` |

---

### Gmail — Read-Only OAuth2

Gmail uses a separate token file (`gmail_token.json`) with read-only scopes so it never conflicts with Calendar's write-access token (`token.json`).

| Tool | Description |
|---|---|
| `read_gmail_inbox(max_results=10, unread_only=False)` | Fetches emails from the primary inbox. Returns sender, subject, date, and a 200-char body snippet per email. |
| `search_gmail(query, max_results=5)` | Full Gmail search syntax: `from:boss@company.com`, `subject:invoice is:unread after:2026/05/01`, etc. |
| `gmail_triage()` | Fetches up to 15 unread emails, then asks Claude to categorise each as **URGENT** (needs same-day response), **ACTION** (requires follow-up), or **FYI** (informational only) with a one-line summary. |

---

### Google Calendar — Full CRUD

| Tool | Description |
|---|---|
| `get_calendar_events(days_ahead=1, max_results=15)` | Fetch upcoming events from the primary calendar. Returns start/end, title, location, description. |
| `show_calendar(days_ahead=1)` | Same as above, but also sends a `switch_tab: calendar` action to the HUD. |
| `create_calendar_event(title, start_time, end_time, description?, location?)` | Create an event. Times must be ISO 8601 (e.g. `2026-05-12T14:00:00`). Timezone defaults to UTC. |
| `delete_calendar_event(event_id)` | Delete by Google Calendar event ID (obtained from `get_calendar_events`). |

---

### System & OS

| Tool | Description | Platform Notes |
|---|---|---|
| `set_timer(duration_seconds, label?)` | Starts a countdown. Sends `timer_set` event → HUD shows SVG TimerRing around the Orb. On completion, JARVIS speaks "Timer complete, sir." | Cross-platform |
| `open_app(app_name)` | Launch an application. Uses `start` on Windows, `open -a` on macOS. | Platform-aware |
| `open_url(url, browser?)` | Resolves shortcut names (youtube, gmail, github, reddit, spotify, netflix, chatgpt, linkedin, twitter) to full URLs, then opens in the HUD browser panel. | Sends `show_browser` WS event |
| `run_shell(command)` | Runs an allowlisted shell command. Allowed: `ls`, `pwd`, `date`, `cat`, `grep`, `find`, `curl`, `ping`, `df`, `ps`, `uptime`, `echo`, `which`, `whoami`. Blocks dangerous patterns. | Subprocess |
| `take_screenshot()` | Captures the full screen, encodes as base64, sends to Claude Vision with "describe this screenshot" prompt. | PIL / MSS |
| `read_clipboard()` | Returns current clipboard contents as a string. | `pyperclip` |
| `write_clipboard(text)` | Copies text to the system clipboard. | `pyperclip` |
| `get_system_vitals()` | Reports CPU%, RAM used/total, disk used/free, cumulative network I/O since boot. Spoken output (e.g. "CPU at 34%, RAM 8.1 GB of 16 GB"). | `psutil` |

---

### File Manager

| Tool | Description |
|---|---|
| `list_files(directory="~", pattern="*")` | Lists files and folders. Supports glob patterns like `*.pdf`. |
| `find_file(name, search_path="~")` | Recursive file search by name glob. |
| `open_file(path)` | Opens a file with the default OS application (`xdg-open` / `open` / `start`). |
| `get_file_info(path)` | Returns file type, size in human-readable format, creation date, modification date. |
| `move_file(source, destination)` | Moves or renames a file or directory. |
| `delete_file(path)` | Moves to the OS trash/recycle bin (recoverable). Uses `send2trash`. |

---

### Developer Tools

| Tool | Description |
|---|---|
| `read_file(path)` | Reads up to 200 lines of a file in the JARVIS repo (relative path). |
| `write_file(path, content)` | Writes/overwrites a file in the JARVIS repo. |
| `git_status()` | Returns current branch, working-tree status (`git status`), and last 5 commits (`git log --oneline`). |
| `run_tests(test_path=".")` | Runs `pytest` on the JARVIS project and returns pass/fail summary + any error output. |
| `search_codebase(pattern, path=".")` | Runs ripgrep (or grep fallback) across the repo. Returns matching file:line:content triples. |

---

### Browser Automation — Playwright

A single Chromium instance is shared across all browser tool calls. A `threading.Lock()` serialises access. The browser starts headless by default; set `BROWSER_HEADLESS=0` to watch it work.

| Tool | Description |
|---|---|
| `browser_navigate(url)` | Navigate to a URL. Auto-prefixes `https://` if missing. Returns page title + first 2000 chars of `document.body.innerText`. |
| `browser_extract_text()` | Dumps the full `innerText` of the current page (up to 4000 chars). Useful for reading article content after navigating. |
| `browser_click(target)` | Tries `page.get_by_text(target, exact=True)` first; falls back to CSS selector. |
| `browser_fill(selector, value)` | Types `value` into the element matched by `selector`. |
| `browser_screenshot()` | Takes a PNG screenshot, encodes to base64, sends to Claude Vision, returns a natural-language description of the page layout and content. |
| `browser_execute_js(code)` | Evaluates arbitrary JavaScript via `page.evaluate()`. Returns `str(result)` truncated to 2000 chars. |

**Typical agentic pattern:**
```
browser_navigate("https://news.ycombinator.com")
browser_extract_text()          → Claude reads the headline list
browser_click("Ask HN: ...")    → navigate to a specific post
browser_extract_text()          → read comments
```

---

### Map & Location

| Tool | Description |
|---|---|
| `plan_route(origin, destination)` | Geocodes both locations, computes a driving route, sends `route` event to the HUD → MapPanel draws the polyline and sends a `switch_tab: map` action. |
| `show_location(place)` | Geocodes the place name, sends `show_location` event → MapPanel flies to it with a marker. |
| `search_nearby(query, location="Stockholm")` | Finds POIs matching `query` near `location` using OpenStreetMap Nominatim. |

---

### Media & HUD Navigation

| Tool | Description |
|---|---|
| `play_music(action, query?)` | Spotify actions: `play`, `pause`, `next`, `previous`, `search <query>`. Uses OS-level AppleScript / D-Bus depending on platform. |
| `set_volume(level)` | Sets system output volume 0–100 using platform-specific commands. |
| `navigate_to(tab)` | Sends `switch_tab` WS event. Valid tabs: `home`, `briefing`, `stocks`, `news`, `map`, `terminal`, `music`, `camera`, `settings`, `calendar`, `browser`. |
| `show_briefing()` | Navigates to briefing panel + fetches weather for spoken delivery. |
| `show_stocks()` | Navigates to stocks panel + fetches market summary for spoken delivery. |
| `show_news_stream(channel?)` | Navigates to news panel + fetches headlines for spoken delivery. |
| `show_calendar(days_ahead=1)` | Navigates to calendar panel + fetches today's events. |

---

### Creator

| Tool | Description |
|---|---|
| `create_document(filename, content, file_type="txt")` | Writes a file to the Desktop and opens it. Supports: `txt`, `md`, `html`, `py`, `js`, `css`. |
| `draft_email(to, subject, body)` | Opens the default mail client with a pre-filled compose window via `mailto:` URL. |
| `translate(text, target_language)` | Claude-powered translation — no external API needed. Handles any language pair. |
| `detect_language(text)` | Identifies the language of input text using Claude. |
| `generate_html(description, filename="jarvis_page")` | Generates a complete HTML page from a natural-language description, saves to Desktop, opens in browser. |
| `write_code(description, filename, language="python")` | Generates code in any language from a description, saves to Desktop, opens with the default editor. |

---

### Communication

| Tool | Description |
|---|---|
| `send_telegram(text)` | Pushes a message to the registered Telegram chat. Works even when the HUD is closed. Used for proactive alerts — price moves, reminders, briefings. |

---

### Vision

| Tool | Description |
|---|---|
| `look_at_desk(question?)` | Captures a frame from the default webcam, encodes to base64, sends to Claude Vision with an optional specific question (e.g. "Is there a coffee cup on the desk?"). Returns a natural-language description. |

---

### MCP — Extensible Tool Bridge

Any external MCP (Model Context Protocol) server configured in `mcp_servers.json` is automatically discovered at startup and its tools are injected into Claude's tool list with the prefix `mcp_<server>_<tool>`.

**Example configuration:**
```json
{
  "servers": [
    {
      "name": "github",
      "command": "npx",
      "args": ["-y", "@modelcontextprotocol/server-github"],
      "env": { "GITHUB_PERSONAL_ACCESS_TOKEN": "ghp_..." }
    },
    {
      "name": "slack",
      "command": "npx",
      "args": ["-y", "@modelcontextprotocol/server-slack"],
      "env": { "SLACK_BOT_TOKEN": "xoxb-..." }
    }
  ]
}
```

Results in tools like:
- `mcp_github_create_issue`
- `mcp_github_list_pull_requests`
- `mcp_slack_post_message`
- `mcp_slack_list_channels`

Each MCP server runs as a persistent stdio subprocess in its own async context. Calls cross the sync/async boundary via `asyncio.run_coroutine_threadsafe()` with a 30-second timeout.

---

## 6. Voice Pipeline

### Wake Word Detection

```
sounddevice (16 kHz, mono)
    │
    ▼
openwakeword (hey_jarvis_v0.1 model)
    │  threshold: WAKEWORD_THRESHOLD (default 0.5)
    │  debounce:  1.5 seconds
    ▼
_broadcast() → all registered queue.Queue listeners
    │
    ▼
WebSocket /ws/wakeword
    │  {"type": "wake_word_detected"}
    ▼
VoiceControl.jsx → activates listening mode
```

The listener runs in a daemon thread. It gracefully no-ops if `sounddevice` or `openwakeword` are not installed. The 1.5-second debounce prevents double-triggers from a single wake phrase.

### Speech-to-Text — Two Modes

**Mode 1: Browser STT (Web Speech API)**
- Uses the browser's built-in speech recognition (requires online connection)
- Instant feedback, no backend round-trip
- No audio data leaves the browser before transcription

**Mode 2: Whisper (faster-whisper)**
```
VoiceControl.jsx
  ├── getUserMedia({ audio: true })
  ├── MediaRecorder (webm/opus)
  ├── AudioAnalyser (FFT 256) → VAD
  │     SILENCE_MS = 1400ms of near-silence → stop
  │     MAX_RECORD_MS = 15000ms hard limit
  └── Blob → FormData → POST /api/transcribe
                              │
                    faster-whisper (CPU, int8 quant)
                    model: WHISPER_MODEL env var (tiny/base/small/medium)
                    VAD filter: true
                    language: auto-detect
                              │
                    {"transcript": "..."}
```

**faster-whisper advantages:**
- Runs entirely on CPU with int8 quantisation — no GPU required
- 4× faster than openai-whisper at equivalent accuracy
- Works offline after model download
- VAD filter removes silence, improving accuracy

### Text-to-Speech

```
Agent response (full text after "done")
    │
    ├── Strip markdown (*_`#>)
    ▼
POST /api/tts { text, voice: "en-US-GuyNeural" }
    │
    ▼
edge_tts.Communicate(text, voice)
    │  Streams MP3 chunks from Microsoft's TTS service
    ▼
StreamingResponse → browser
    │
    ▼
new Audio(objectURL).play()
    │
    ▼
audioRef.current → can be paused by handleInterrupt()
```

`en-US-GuyNeural` is a free Microsoft neural voice — no API key or billing required. Other voices can be set via the `voice` field in the POST body.

---

## 7. Autonomous Background Scheduler

The scheduler (`jarvis/scheduler.py`) starts three daemon threads on server boot, independent of any user session.

### Client Registry Pattern

```python
# Per WebSocket session:
sched_q = queue.Queue()
_scheduler.add_client(sched_q)   # on WS connect

# _watch_scheduler() coroutine polls every 10 seconds:
event = sched_q.get_nowait()
asyncio.create_task(run_agent(event["message"]))

_scheduler.remove_client(sched_q)  # on WS disconnect
```

This means scheduled tasks run through the full agent pipeline — tool use, memory, streaming — exactly as if the user had typed the message.

### Thread: Morning Briefing

```
Loop every 60s:
    current_hour == BRIEFING_HOUR and not already_sent_today?
    └── broadcast({"type":"scheduled_task","message":"Good morning! Please give me my daily briefing..."})
        └── Agent generates: weather + calendar events + top news + market snapshot
```

### Thread: Stock Alerts

```
Loop every 300s (5 minutes):
    For each ticker in ALERT_TICKERS:
        yfinance.download(ticker, period="2d")
        pct_change = (today_close - yesterday_close) / yesterday_close * 100
        abs(pct_change) >= PRICE_ALERT_PCT?
        └── broadcast(alert message)
            └── Agent announces the move + context
            └── send_telegram(alert) if Telegram configured
```

### Thread: Email Digest

```
Opt-in via EMAIL_DIGEST_ENABLED=1
Loop every EMAIL_DIGEST_INTERVAL_MIN minutes:
    broadcast("Please triage my inbox and summarise any urgent emails.")
    └── Agent calls gmail_triage() automatically
```

---

## 8. Telegram Bot

```
TELEGRAM_BOT_TOKEN in .env
    │
    ▼
telegram_bot.start(agent_factory)
    │
    ├── threading.Thread(target=_run, daemon=True)
    └── telebot.TeleBot(token, threaded=False)
            │
            ├── /start → register chat_id
            │            persist to ~/.jarvis/telegram_chat_id
            │            (survives server restarts)
            │
            └── Any text → agent.ask(message.text)
                           ├── Full tool use (same memory, same tools)
                           ├── Split response into 4096-char chunks
                           └── bot.reply_to(message, chunk)
```

**Proactive sends** (JARVIS → user, no prompt needed):
```python
send_telegram("NVDA is up 4.2% — breaking above resistance at $950.")
# Works from scheduler alerts, tool calls, or any agent-triggered event
```

The `chat_id` persists across restarts so proactive alerts work even if the bot was restarted overnight.

---

## 9. MCP Protocol Bridge

```
mcp_servers.json
    │
    ▼
mcp_client.start()
    │
    ├── asyncio.new_event_loop() in daemon thread "mcp-event-loop"
    └── _run_all_sessions(servers)
            │
            ├── For each server:
            │   async with stdio_client(StdioServerParameters(...)) as (read, write):
            │       async with ClientSession(read, write) as session:
            │           session.initialize()
            │           tools = session.list_tools()
            │           _register_tools(server_name, tools)
            │               └── mcp_<server>_<tool> → (server, original_name) mapping
            │           asyncio.sleep(inf)   ← keep session alive
            │
            └── On tool call:
                asyncio.run_coroutine_threadsafe(
                    _call_async(server, tool, args), _loop
                ).result(timeout=30)
```

The `asyncio.sleep(float("inf"))` pattern keeps each MCP session open for the lifetime of the process. If a server disconnects, the session is removed from `_sessions` and the tool becomes unavailable until restart.

---

## 10. Browser Automation

```
jarvis/tools/browser_tool.py

Global singletons:
  _playwright: sync_playwright instance
  _browser:    Chromium browser (headless by default)
  _page:       Single shared page
  _lock:       threading.Lock() — all ops serialised

_get_page():
  ├── if _page exists and not closed → return it
  └── else:
      sync_playwright().start()
      _playwright.chromium.launch(headless=BROWSER_HEADLESS)
      browser.new_context(
          viewport={"width": 1280, "height": 800},
          user_agent="Mozilla/5.0 ... Chrome/120.0.0.0"
      )
      ctx.new_page()
```

The browser launches lazily on first use — no startup overhead unless a browser tool is actually called.

**Claude Vision integration** (browser_screenshot):
```python
img_bytes = page.screenshot(full_page=False)
b64 = base64.standard_b64encode(img_bytes).decode()
client.messages.create(
    model="claude-sonnet-4-6",
    messages=[{"role":"user","content":[
        {"type":"image","source":{"type":"base64","media_type":"image/png","data":b64}},
        {"type":"text","text":"Describe the key content and layout of this web page screenshot concisely."}
    ]}]
)
```

---

## 11. Free Dictation Mode

```
DICTATION_HOTKEY = Ctrl+Shift+Space  (configurable)

pynput.keyboard.GlobalHotKeys
    │
    ├── on_press:
    │   sounddevice.InputStream(samplerate=16000, channels=1, dtype="int16")
    │   └── accumulate frames while _recording=True (max 30s)
    │
    └── on_release (space key up):
        numpy int16 array → WAV bytes (pure struct.pack, no scipy)
            │
            ▼
        POST /api/transcribe (format=wav)
            │
            ▼
        faster-whisper transcript
            │
            ▼
        pyperclip.copy(transcript)
        time.sleep(0.1)
        pyautogui.hotkey("ctrl", "v")
        └── text pasted at current cursor position in any application
```

This works system-wide — in any text editor, browser, IDE, or chat app. The WAV header is built manually with `struct.pack` to avoid a scipy dependency.

---

## 12. HUD — Frontend Architecture

### State Management (App.jsx)

```javascript
const [tab,          setTab]          = useState('home')
const [thinking,     setThinking]     = useState(false)   // Claude is processing
const [speaking,     setSpeaking]     = useState(false)   // TTS audio is playing
const [userSpeaking, setUserSpeaking] = useState(false)   // mic is active
const [route,        setRoute]        = useState(null)    // map route data
const [showLocation, setShowLocation] = useState(null)    // map fly-to target
const [toolLogs,     setToolLogs]     = useState([])      // terminal + ToolTheater
const [activeTimer,  setActiveTimer]  = useState(null)    // {duration, label, endsAt}
const [browserUrl,   setBrowserUrl]   = useState('')      // BrowserPanel target
```

### WebSocket Message Protocol

| Message type | Direction | Payload | Handler |
|---|---|---|---|
| `token` | Server → Browser | `{type, text}` | Append to buffer, `setThinking(false)`, `setSpeaking(true)` |
| `done` | Server → Browser | `{type}` | Flush buffer → TTS if voice mode, `setSpeaking(false)` |
| `tool_log` | Server → Browser | `{type, tool, input, result, ts}` | Append to `toolLogs` → ToolTheater + TerminalPanel |
| `switch_tab` | Server → Browser | `{type, tab}` | `setTab(tab)` |
| `route` | Server → Browser | `{type, ...routeData}` | `setRoute(data)`, `setTab("map")` |
| `show_location` | Server → Browser | `{type, place, lat, lon}` | `setShowLocation(data)`, `setTab("map")` |
| `show_browser` | Server → Browser | `{type, url}` | `setBrowserUrl(url)`, `setTab("browser")` |
| `timer_set` | Server → Browser | `{type, duration_seconds, label}` | `setActiveTimer({...})`, `setTab("home")` |
| `error` | Server → Browser | `{type, message}` | `setSpeaking(false)`, `setThinking(false)` |
| `{message}` | Browser → Server | `{message: "text"}` | Agent processes |
| `{interrupt}` | Browser → Server | `{type: "interrupt"}` | Agent cancels stream |

### Phase D HUD Overlay Components

#### BootSequence
- Checks `sessionStorage.getItem('jarvis_booted')` — skips entirely on subsequent loads
- 11 staggered text lines with `opacity` + `translateX` CSS transitions
- Timed sequence: 0ms → 2950ms line reveals, then 200ms fade-out, then 700ms unmount
- Corner bracket decorations on the boot overlay

#### SystemVitals
- `EventSource('http://localhost:8000/api/vitals')` — SSE connection
- 4 arc gauges using SVG `stroke-dasharray` trick:
  - Track: `strokeDasharray="${arc} ${circ}"` (270° of full circle, dimmed)
  - Fill:  `strokeDasharray="${arc * pct} ${circ}"` animated with CSS transition
  - Both rotated `rotate(135, cx, cy)` so 0% starts at bottom-left
- Colour coding: CPU and RAM turn amber at 60%+, red at 80%+
- Network: computes KB/s from successive cumulative byte counter deltas
- Disappears gracefully if the SSE stream is unavailable

#### Waveform
- Canvas `requestAnimationFrame` loop — 60fps, zero DOM manipulation
- 48 bars, each `lerp`-smoothed toward a mode-specific target height:
  - **recording** (red): random jitter × envelope shape (louder in the middle)
  - **speaking** (blue): two layered sine waves (phase1 + 0.45·sin, phase2 + 0.20·sin)
  - **idle** (dim blue): very slow, very low amplitude shimmer
- Speed multiplier for lerp: 0.28 active, 0.04 idle — smooth transitions between modes
- Positioned `bottom: 88px` center — sits above the VoiceControl buttons

#### ToolTheater
- Tracks `logs.length` via `useEffect` — detects new entries without comparing objects
- Each new log creates a card with a unique `id` (tool + ts + random hex)
- Card lifecycle: `entering (translateX(110%))` → `visible (translateX(0))` → `leaving (translateX(110%))`
  - Enter: `cubic-bezier(0.34, 1.56, 0.64, 1)` — spring overshoot for kinetic feel
  - Exit: standard `ease`
- Draining progress bar: width transitions from 100%→0% over `CARD_TTL=4200ms` linear
- Maximum 5 cards visible (oldest pruned on overflow)

### Content Panels

| Panel | Tab | Key Components |
|---|---|---|
| Home | `home` | Orb (animated sphere) + TimerRing (SVG arc countdown) + Clock |
| Briefing | `briefing` | Weather widget, temperature, wind, humidity |
| Stocks | `stocks` | Live watchlist: SPY, QQQ, AAPL, NVDA, TSLA, MSFT, GOOGL, AMZN, META, BTC-USD |
| News | `news` | RSS cards from SVT, Aftonbladet, Dagens industri — sorted by publish time |
| Map | `map` | React-Leaflet — fly-to animations, route polylines, POI markers |
| Terminal | `terminal` | Scrolling log of every tool call with timestamp |
| Calendar | `calendar` | Google Calendar events list, create/delete UI |
| Browser | `browser` | `<iframe>` proxied through `/api/browse` to strip X-Frame-Options |
| Music | `music` | Spotify playback controls + now-playing display |
| Camera | `camera` | Live webcam feed + gesture recognition overlay (MediaPipe) |
| Settings | `settings` | Voice mode toggle, model info, API status |

### Gesture System

MediaPipe Hands runs in the vision server (`/vision`). Detected gestures are sent to `GestureOverlay.jsx` which maps them to agent commands:

| Gesture | Command sent to Agent |
|---|---|
| `swipe_right` | "Skip to the next Spotify track" |
| `swipe_left` | "Go back to the previous Spotify track" |
| `swipe_up` | "Turn the volume up" |
| `swipe_down` | "Turn the volume down" |

When a gesture triggers a command, `gestureActiveRef.current = true` — this tells the `done` handler to speak the response via TTS even though the user didn't explicitly use voice mode.

---

## 13. API Endpoint Reference

| Method | Path | Auth | Description |
|---|---|---|---|
| `WS` | `/ws` | — | Main chat WebSocket |
| `WS` | `/ws/wakeword` | — | Wake-word event push |
| `GET` | `/api/vitals` | — | SSE system metrics stream |
| `POST` | `/api/tts` | — | `{text, voice?}` → MP3 stream |
| `POST` | `/api/transcribe` | — | `audio` file + `format` → `{transcript}` |
| `GET` | `/api/calendar` | OAuth | `?days=N` → `{events:[...]}` |
| `GET` | `/api/stocks` | — | Live watchlist data |
| `GET` | `/api/news` | — | RSS aggregated articles |
| `GET` | `/api/briefing` | — | Weather snapshot |
| `GET` | `/api/memories` | — | All facts + context summary + Obsidian status |
| `POST` | `/api/telegram/send` | — | `{text}` → push to Telegram |
| `GET` | `/api/browse` | — | `?url=...` → proxied HTML (iframe-safe) |
| `GET` | `/api/spotify/now-playing` | — | Current Spotify track |
| `POST` | `/api/spotify/control` | — | `{action, query?}` → Spotify control |

---

## 14. End-to-End Data Flow

### Voice Query: "Hey JARVIS, what's the weather in Tokyo?"

```
[HARDWARE]
Microphone → sounddevice stream → openwakeword
    └── score("hey_jarvis") >= 0.5 → debounce 1.5s
    └── _broadcast({"type": "wake_word_detected"})

[WS /ws/wakeword]
    └── browser receives {"type": "wake_word_detected"}
    └── VoiceControl.jsx activates → startWhisperRecording()

[BROWSER]
getUserMedia() → MediaRecorder (webm/opus)
AudioAnalyser → VAD (silence after 1.4s of quiet)
    └── 1.4s silence detected → stop recording
    └── FormData(audio=blob, format=webm)

[POST /api/transcribe]
faster-whisper (CPU, int8) → {"transcript": "what's the weather in Tokyo?"}

[BROWSER → WS /ws]
wsRef.current.send({"message": "what's the weather in Tokyo?"})
    └── setThinking(true)

[FASTAPI WebSocket handler]
asyncio.create_task(run_agent("what's the weather in Tokyo?"))
    └── loop.run_in_executor(None, lambda: agent.ask(msg, on_token, on_action))

[AGENT]
memory.append_message("user", "what's the weather in Tokyo?")
should_compress(30)? → NO (< 30 messages)
messages = get_messages_with_context(20)

client.messages.stream(
    model="claude-sonnet-4-6",
    tools=TOOLS + mcp_tools,
    messages=[...history..., {"role":"user","content":"what's the weather in Tokyo?"}]
)

[CLAUDE → token stream]
"I'll check..." → on_token("I'll check...") → WS {"type":"token","text":"I'll check..."}
stop_reason = "tool_use"
    tool: get_weather, input: {"city": "Tokyo"}

[execute_tool]
get_weather("Tokyo") → wttr.in/Tokyo?format=j1
    └── returns "Tokyo: 22°C, feels like 24°C, humidity 68%, wind 12 km/h, Partly cloudy. 
                5-day forecast: Tue 24°C, Wed 19°C..."

pending_actions.append({"type":"tool_log","tool":"get_weather","input":{"city":"Tokyo"},"result":"...","ts":"14:23:05"})

pending_actions.append({"type":"switch_tab","tab":"briefing"})
    └── on_action callback → WS {"type":"switch_tab","tab":"briefing"}
    └── setTab("briefing") → BriefingPanel becomes visible

[CLAUDE → token stream (second pass)]
"Tokyo is currently 22°C..." → tokens stream to browser
stop_reason = "end_turn"

[FASTAPI]
WS {"type":"done"}
WS {"type":"tool_log","tool":"get_weather",...}  ← ToolTheater shows card

[BROWSER]
setSpeaking(false)
speakViaApi("Tokyo is currently 22°C...")
    └── POST /api/tts → edge-tts → MP3 stream
    └── new Audio(blobUrl).play()
    └── Waveform switches to "speaking" mode (blue sine wave)

[MEMORY]
memory.append_message("assistant", "Tokyo is currently 22°C...")
```

---

## 15. Configuration Reference

All variables are set in `.env` (copy from `.env.example`).

| Variable | Default | Description |
|---|---|---|
| `ANTHROPIC_API_KEY` | *(required)* | Anthropic API key — stored in AWS Secrets Manager or .env |
| `JARVIS_USER_NAME` | *(empty)* | Name JARVIS uses when greeting the user |
| `JARVIS_MEMORY_PATH` | `~/.jarvis/memory.db` | SQLite database path |
| `OBSIDIAN_VAULT_PATH` | *(empty)* | Absolute path to Obsidian vault. Leave blank to disable sync. |
| `BRIEFING_HOUR` | `8` | Hour (24h) for the morning briefing |
| `WAKEWORD_THRESHOLD` | `0.5` | openwakeword confidence threshold (0.0–1.0) |
| `ALERT_TICKERS` | `AAPL,NVDA,BTC-USD` | Comma-separated tickers for price alerts |
| `PRICE_ALERT_PCT` | `2.5` | Minimum % move to trigger a stock alert |
| `EMAIL_DIGEST_ENABLED` | `0` | Set to `1` to enable hourly email digest |
| `EMAIL_DIGEST_INTERVAL_MIN` | `60` | Minutes between email digest runs |
| `WHISPER_MODEL` | `base` | faster-whisper model size: `tiny`, `base`, `small`, `medium` |
| `TELEGRAM_BOT_TOKEN` | *(empty)* | BotFather token. Leave blank to disable Telegram. |
| `BROWSER_HEADLESS` | `1` | Set to `0` to show the Playwright browser window |
| `DICTATION_HOTKEY` | `<ctrl>+<shift>+space` | pynput global hotkey for free dictation |

---

## 16. Dependency Graph

```
Core
├── anthropic>=0.40.0          Claude API client (streaming, tool use)
├── fastapi>=0.110.0           Async HTTP + WebSocket server
├── uvicorn>=0.29.0            ASGI server
└── python-dotenv>=1.0.0       .env loading

Memory & Intelligence
├── fastembed>=0.3.0           ONNX embeddings (no GPU required)
├── boto3>=1.34.0              AWS Secrets Manager

Voice
├── faster-whisper>=1.0.0      Whisper STT (CPU int8 quantised)
├── python-multipart>=0.0.9    File upload parsing
├── openwakeword>=0.6.0        "Hey JARVIS" wake word
├── sounddevice>=0.4.6         Microphone input stream
└── edge-tts>=7.0.0            Microsoft neural TTS (free)

Google Integration
├── google-api-python-client>=2.100.0
├── google-auth-httplib2>=0.2.0
└── google-auth-oauthlib>=1.2.0

Data & Web
├── yfinance>=0.2.0            Stock + crypto prices
├── feedparser>=6.0.0          RSS feed parsing
├── httpx>=0.27.0              Async HTTP client
├── duckduckgo-search>=6.0.0   Web search (no API key)
└── requests>=2.31.0           Sync HTTP client

Phase C — Reach
├── mcp>=1.0.0                 Model Context Protocol client
├── pyTelegramBotAPI>=4.14.0   Telegram bot
├── playwright>=1.40.0         Chromium browser automation
├── pynput>=1.7.0              Global hotkey listener
├── pyautogui>=0.9.54          Keyboard simulation (paste)
└── pyperclip>=1.8.0           Clipboard access

Phase D — Vitals
└── psutil>=5.9.0              CPU/RAM/disk/network metrics

Vision
├── ultralytics>=8.0.0         YOLO object detection
├── opencv-python>=4.8.0       Camera capture + image processing
└── mediapipe>=0.10.0          Hand gesture recognition

Frontend (npm)
├── react@^19.2.5
├── react-dom@^19.2.5
├── leaflet@^1.9.4             Map rendering
└── react-leaflet@^5.0.0      React map bindings
```

---

*Generated: 2026-05-12 — JARVIS v4.0*
