# JARVIS — Build Roadmap

> Vision: A personal AI assistant with the look, feel, and voice of the Iron Man JARVIS.
> Built from scratch. The goal is to match the actual JARVIS from the movies as closely as possible.

---

## The Vision

JARVIS is a persistent AI presence on your screen. It lives in the corner as a glowing orb,
always listening, always watching. The main screen is a live intelligence dashboard —
world news, markets, maps, briefings — all rendered in a dark HUD aesthetic.

You speak to it. It speaks back in a calm, precise British voice.
It knows what's on your desk. It knows what's happening in the world.
It knows your schedule, your tasks, your codebase.

The screen looks like a cockpit. You feel like Tony Stark.

---

## The Interface — What It Looks Like

From the reference screenshots, the layout is:

```
┌─────────────────────────────────────────────────────────────────┐
│  STOCK TICKER  ·  DOW  ·  NASDAQ  ·  S&P 500  ·  BTC  ·  ...  │  ← top bar, always visible
├──────────────────────────────────────┬──────────────────────────┤
│                                      │                          │
│   MAIN PANEL                         │   SIDE PANEL            │
│   (news feed / map / camera /        │   (stock chart /        │
│    briefing / terminal)              │    JARVIS response /    │
│                                      │    news headlines)      │
│                                      │                          │
├──────────────────────────────────────┴──────────────────────────┤
│  [home] [map] [news] [terminal] [music]    ·  status  ·  time  │  ← bottom bar
│                                                     ┌─────────┐ │
│                                                     │  JARVIS │ │  ← persistent orb, bottom right
│                                                     └─────────┘ │
└─────────────────────────────────────────────────────────────────┘
```

The JARVIS orb lives permanently in the bottom-right corner. Every mode shares the same
top ticker, bottom nav, and corner orb. The main + side panels change per mode.

---

## Design Language

| Element | Value |
|---|---|
| Background | `#080c14` — near-black navy |
| Grid overlay | Subtle dot grid or fine line grid, 5% opacity |
| Primary glow | `#0af` — electric blue |
| Ring / orb | White circle + blue halo blur |
| Text | `#c8dff0` — cool ice white |
| Accent / alerts | `#f0a500` — amber |
| Font | `JetBrains Mono` or `IBM Plex Mono` — monospace throughout |
| HUD chrome | Corner brackets, tick marks on edges, scan line sweep |
| Animations | All CSS ease-in-out 150–300ms, nothing bouncy |

---

## Tech Stack

| Layer | Technology | Why |
|---|---|---|
| AI Brain | Claude API (`claude-sonnet-4-6`) | Best reasoning, tool use, vision |
| Voice In (STT) | OpenAI Whisper (local, faster-whisper) | Fast, offline, accurate |
| Voice Out (TTS) | ElevenLabs API — British male voice | Natural, character-accurate |
| Wake Word | Porcupine (Picovoice) | Offline "Hey JARVIS" detection |
| Backend | Python + FastAPI + WebSockets | Async, real-time streaming |
| Frontend | React + Vite + Canvas | HUD panels, animations, audio viz |
| News feed | RSS aggregation + live video embed | World news headlines + stream |
| Market data | Yahoo Finance API or Alpaca | Real-time stocks, crypto |
| Maps | Mapbox GL JS (dark theme) | Interactive routing, dark styled |
| Vision | Raspberry Pi 5 + Camera + YOLO | Object detection on your desk |
| Memory | SQLite (local) + S3 backup | Persistent facts + conversation |
| Deployment | AWS EC2 eu-north-1 — already set up | Always-on remote access |

---

## Phase 1 — AI Brain & Personality

**Goal:** JARVIS can have a real conversation with memory and a locked persona.

### 1.1 Agent Core (`jarvis/agent.py`)
- [ ] Wrap Claude API with streaming support (token-by-token, not batch)
- [ ] Conversation history with rolling window + auto-summarisation when context grows
- [ ] Tool call execution loop — Claude decides what tool to run, JARVIS executes it

### 1.2 SOUL.md — JARVIS Identity
- [ ] Defines who JARVIS is, his tone, his rules, his personality
- [ ] Loaded into every conversation as the system prompt
- [ ] JARVIS: calm, precise, dry British wit, never breaks character
- [ ] JARVIS refers to the user by name and tracks preferences
- [ ] Never says "As an AI language model..." — always stays in persona

### 1.3 Persistent Memory (`jarvis/memory.py`)
- [ ] SQLite-backed store: user facts, preferences, task history, summaries
- [ ] Semantic retrieval — relevant memories injected into each prompt
- [ ] Memory tools: `remember_this`, `recall`, `forget`
- [ ] Survives restarts — memory persists across sessions

### 1.4 CLI Test Harness
- [ ] `python -m jarvis` — text conversation in the terminal
- [ ] Lets us test brain + memory before building voice or UI

---

## Phase 2 — Voice Pipeline

**Goal:** Fully hands-free. Speak, JARVIS responds, no keyboard needed.

### 2.1 Wake Word (`jarvis/voice/wakeword.py`)
- [ ] Porcupine offline wake word: "Hey JARVIS"
- [ ] On detection: soft activation chime + start recording
- [ ] LED / orb pulse animation triggered via WebSocket event

### 2.2 Speech-to-Text (`jarvis/voice/listener.py`)
- [ ] faster-whisper running locally (small or medium model)
- [ ] VAD (Silero) to detect end of speech — stop recording when you stop talking
- [ ] Target latency: < 400ms transcription for short commands
- [ ] Strip filler words before sending to Claude

### 2.3 Text-to-Speech (`jarvis/voice/speaker.py`)
- [ ] ElevenLabs API — calm British male voice
- [ ] Stream audio chunks as they arrive — don't wait for full sentence
- [ ] Fallback: Piper TTS (local, offline, free)
- [ ] JARVIS does not interrupt itself if you speak mid-response

### 2.4 Voice Pipeline Orchestrator (`jarvis/voice/pipeline.py`)
- [ ] Loop: listen → transcribe → think → speak → listen
- [ ] State machine: IDLE → LISTENING → THINKING → SPEAKING
- [ ] State broadcast via WebSocket so the HUD orb animates correctly

---

## Phase 3 — HUD Frontend

**Goal:** The Iron Man interface. Everything from the reference screenshots.

### 3.1 App Shell & Layout
- [ ] React + Vite project in `frontend/`
- [ ] Full-screen dark layout: top bar + main panel + side panel + bottom nav
- [ ] CSS Grid layout, responsive to monitor size
- [ ] Background: `#080c14` + subtle dot-grid overlay
- [ ] Corner HUD bracket decorations (CSS pseudo-elements)
- [ ] Horizontal scan-line sweep animation on a timer

### 3.2 JARVIS Orb (Persistent, Bottom-Right)
- [ ] White ring with electric blue outer glow (`box-shadow + filter: blur`)
- [ ] "JARVIS" logotype centred inside
- [ ] Idle state: slow breathing pulse
- [ ] Listening state: faster pulse, ring expands
- [ ] Thinking state: spinning arc animation
- [ ] Speaking state: audio-reactive waveform around the ring (Web Audio API)
- [ ] Orb state driven by WebSocket messages from the backend

### 3.3 Top Stock Ticker Bar
- [ ] Scrolling horizontal ticker: DOW · NASDAQ · S&P 500 · BTC · ETH · custom stocks
- [ ] Each item: symbol, price, % change, colour-coded (green up / red down)
- [ ] Real-time updates every 30 seconds
- [ ] Amber alert colour if any index moves > 2% in a session

### 3.4 Bottom Navigation Bar
- [ ] Icon nav: Home · Map · News · Terminal · Music · Settings
- [ ] Active mode highlighted with blue glow underline
- [ ] Right side: clock (24h HH:MM:SS), date, system status dot

### 3.5 Mode: HOME (default)
- [ ] Left panel: JARVIS conversation transcript — streaming character-by-character
- [ ] Right panel: daily briefing summary (auto-generated by JARVIS at startup)
- [ ] Briefing covers: weather, calendar events, top news, market summary
- [ ] Each message timestamped in monospace

### 3.6 Mode: NEWS
- [ ] Left panel: embedded live news video stream (Al Jazeera, BBC World, etc.)
- [ ] Right panel: live news headlines (RSS feed, auto-refreshed)
- [ ] JARVIS can summarise any headline on command: "Tell me more about that"
- [ ] Ticker at bottom of news panel with latest headlines scrolling

### 3.7 Mode: MAP
- [ ] Full-panel Mapbox GL JS map — dark style (`mapbox://styles/mapbox/dark-v11`)
- [ ] Default view: your location or Stockholm
- [ ] Voice commands: "Show me the route from Stockholm to Oslo"
- [ ] JARVIS can plot routes, drop pins, show points of interest
- [ ] Live traffic overlay optional

### 3.8 Mode: TERMINAL
- [ ] Embedded terminal view — shows live tool execution output
- [ ] When JARVIS runs a shell command or git operation, output streams here
- [ ] Monospace font, green-on-dark colour scheme within the panel
- [ ] Previous commands scrollable

### 3.9 Mode: MUSIC
- [ ] Spotify integration: now playing, album art (dark-tinted), progress bar
- [ ] Voice control: "Play something calm" / "Skip" / "Pause"
- [ ] Audio visualiser bars in the panel (same Web Audio API as orb)

### 3.10 Stock Chart Panel (companion to HOME / NEWS)
- [ ] Line chart for a selected stock/index
- [ ] Dark-styled: `#0af` line on `#0d1420` background
- [ ] 1D / 1W / 1M / 1Y timeframes
- [ ] Voice: "Show me Bitcoin this week"

---

## Phase 4 — Vision (Raspberry Pi 5)

**Goal:** JARVIS can see your desk and identify what's on it.

### 4.1 Hardware Setup
- Raspberry Pi 5 with a camera module (Pi Camera v3 or USB webcam)
- Runs a lightweight object detection model (YOLOv8-nano or similar)
- Connects to the JARVIS backend over local network (HTTP or MQTT)

### 4.2 Vision Server (`vision/server.py` — runs on the Pi)
- [ ] Captures frames from the camera at configurable FPS
- [ ] Runs YOLO inference on each frame
- [ ] Sends detection results (object label + confidence + bounding box) to JARVIS backend
- [ ] Optional: streams the annotated video feed for display in the HUD

### 4.3 JARVIS Vision Tool
- [ ] `look_at_desk()` — queries the Pi for current detections
- [ ] Claude can call this tool when needed: "What's on my desk right now?"
- [ ] JARVIS can proactively comment: "I notice your phone is on your desk"
- [ ] Object list shown as a live overlay in the CAMERA mode panel

### 4.4 Mode: CAMERA (HUD panel)
- [ ] Shows the Pi camera feed with bounding box overlays
- [ ] Object labels in HUD style (brackets + monospace text)
- [ ] Detection log on the side: timestamp + object + confidence

---

## Phase 5 — Tools & Skills

**Goal:** JARVIS can take real actions in the world.

### 5.1 Tool Framework (`jarvis/tools/`)
- [ ] Each tool: Python function + JSON schema for Claude's tool use API
- [ ] Tool execution shown live in the TERMINAL panel
- [ ] Claude decides which tools to call; JARVIS executes and returns results

### 5.2 Information Tools
- [ ] `web_search` — Brave Search API or SerpAPI
- [ ] `get_news` — fetch latest RSS headlines by topic
- [ ] `get_weather` — current + 5-day forecast (OpenWeatherMap)
- [ ] `get_stock_price` — live price for any ticker
- [ ] `get_market_summary` — snapshot of major indices

### 5.3 System Tools
- [ ] `get_time` — current time, timezone-aware
- [ ] `set_timer` — countdown with audio alert
- [ ] `open_app` — open a Mac app by name
- [ ] `run_shell` — execute shell command (safety allowlist)
- [ ] `take_screenshot` — capture screen, pass to Claude vision
- [ ] `read_clipboard` / `write_clipboard`
- [ ] `save_note` — append to a local markdown notes file

### 5.4 Developer Tools
- [ ] `read_file` / `write_file` — workspace file access
- [ ] `git_status` — summarise current git state
- [ ] `run_tests` — trigger local CI and stream results to TERMINAL panel
- [ ] `search_codebase` — ripgrep the working directory

### 5.5 Map Tools
- [ ] `plan_route` — get directions between two places (Mapbox Directions API)
- [ ] `show_location` — fly the map to a named place
- [ ] `search_nearby` — find places of interest near a location

### 5.6 Media Tools
- [ ] `play_music` — Spotify playback control
- [ ] `set_volume` — system volume
- [ ] `show_news_stream` — switch HUD to news mode and load a specific channel

---

## Phase 6 — Infrastructure & Deployment

**Goal:** JARVIS runs locally for speed, cloud for remote access.

### 6.1 FastAPI Backend (`jarvis/server.py`)
- [ ] `WS /stream` — WebSocket for real-time streaming to the frontend
- [ ] `POST /chat` — text message endpoint
- [ ] `POST /voice` — receive audio blob, return transcription + streamed response
- [ ] `GET /status` — health check, model info, memory stats
- [ ] `POST /vision` — receive detection data from the Pi

### 6.2 Local Service (Mac)
- [ ] `launchd` plist: JARVIS auto-starts on login
- [ ] Backend runs on `localhost:8000`
- [ ] Frontend served from `localhost:3000`

### 6.3 EC2 Deploy (already provisioned)
- [ ] Fill in the `app` job in `deploy.yml` — SCP build + systemd restart
- [ ] Nginx reverse proxy + HTTPS (Let's Encrypt)
- [ ] Remote access: full JARVIS HUD accessible from any browser
- [ ] Environment variables for all API keys (never committed)

---

## Phase 7 — Proactive & Advanced

**Goal:** JARVIS acts without being asked. Feels alive.

### 7.1 Proactive Briefings
- [ ] Morning briefing on first interaction: weather, calendar, news, markets
- [ ] JARVIS speaks the briefing unprompted when you sit down (webcam presence detection)
- [ ] "Good morning, sir. Markets are down 1.2%. You have two meetings today."

### 7.2 Calendar Integration
- [ ] Google Calendar API — read upcoming events
- [ ] JARVIS reminds you 10 minutes before meetings
- [ ] "Your 3pm call starts in 9 minutes."

### 7.3 AWS Monitoring
- [ ] JARVIS watches the EC2 instances and alerts if one goes down
- [ ] "Dev environment has been unreachable for 5 minutes."

### 7.4 Custom JARVIS Voice
- [ ] Fine-tune an ElevenLabs voice clone to match the movie character
- [ ] Test multiple voice profiles — pick the one that feels right

---

## Build Order

```
Week 1:  Phase 1 — Agent brain + memory + CLI test harness
Week 2:  Phase 2 — Wake word + STT + TTS voice loop
Week 3:  Phase 3 — HUD shell + orb + home mode (conversation panel)
Week 4:  Phase 3 — News mode + stock ticker + market chart
Week 5:  Phase 3 — Map mode + Phase 5 core tools
Week 6:  Phase 4 — Pi vision server + camera panel
Week 7:  Phase 6 — EC2 deploy + Phase 5 remaining tools
Week 8+: Phase 7 — Proactive briefings, calendar, polish
```

---

## What Success Looks Like

You walk into your room. JARVIS detects you via the camera.

*"Good morning. Markets opened down 1.4% — Bitcoin is holding above 60k.
You have a call at 2pm and three pull requests waiting for review.
There is also a coffee mug and what appears to be a Raspberry Pi on your desk."*

You say: *"Hey JARVIS, show me the news."*

The HUD switches to NEWS mode. Al Jazeera streams on the left.
Headlines scroll on the right. The orb pulses softly in the corner.

You say: *"Summarise the top story."*

JARVIS reads it, condenses it, speaks it back.

That is the goal.
