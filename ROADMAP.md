# JARVIS — Build Roadmap

> Vision: A personal AI assistant with the look, feel, and voice of the Iron Man JARVIS.
> Not a clone of anything — built from scratch, inspired by the character.

---

## The Vision

JARVIS is a voice-first AI assistant that lives on your machine and feels like a real intelligence.
It speaks back in a calm, precise British voice. It has a HUD-style interface that feels like a cockpit.
It knows who you are, remembers context across sessions, and can take real actions in the world.

The aesthetic: dark navy backgrounds, glowing blue rings, grid overlays, HUD brackets, clean monospace type.
The feeling: you are Tony Stark at your desk.

---

## Tech Stack

| Layer | Technology | Why |
|---|---|---|
| AI Brain | Claude API (claude-sonnet-4-6) | Best reasoning, tool use, long context |
| Voice In (STT) | OpenAI Whisper (local) | Fast, accurate, runs offline |
| Voice Out (TTS) | ElevenLabs API or local Coqui/Piper | Natural British male voice |
| Wake Word | Porcupine (Picovoice) | Offline, low-latency "Hey JARVIS" detection |
| Backend | Python + FastAPI | Async, WebSocket support for streaming |
| Frontend | React + HTML5 Canvas | HUD animations, real-time voice visualiser |
| Memory | SQLite (local) + S3 (backup) | Persistent facts, conversation summaries |
| Agent Tools | Custom Python functions | What JARVIS can actually do |
| Deployment | AWS EC2 (eu-north-1) — already set up | Remote access, always-on option |
| Hardware | Mac (primary), Raspberry Pi (optional kiosk) | Runs locally on Apple Silicon |

---

## Phase 1 — Core AI Brain

**Goal:** JARVIS can have a real conversation via text, with memory and personality.

### 1.1 Agent Framework
- [ ] Create `jarvis/agent.py` — wraps Claude API with system prompt
- [ ] Write the JARVIS persona system prompt (calm, precise, slightly dry British wit)
- [ ] Add conversation history management (rolling window + summarisation)
- [ ] Streaming responses (token by token, not waiting for full reply)

### 1.2 Persistent Memory
- [ ] Create `jarvis/memory.py` — SQLite-backed memory store
- [ ] Store: user facts, preferences, past tasks, summaries of old conversations
- [ ] Memory injection: relevant memories are retrieved and added to each prompt
- [ ] Memory tool: JARVIS can explicitly save and recall facts ("Remember that...")

### 1.3 Personality & Persona
- [ ] SOUL.md — defines JARVIS's character, tone, rules, and self-identity
- [ ] JARVIS should refer to the user by name
- [ ] JARVIS should never break character (no "As an AI language model...")
- [ ] JARVIS should have opinions and push back when appropriate

### 1.4 Simple CLI Interface (test harness)
- [ ] `python -m jarvis` — start a text conversation in the terminal
- [ ] Lets us test the brain before building voice or UI

---

## Phase 2 — Voice Pipeline

**Goal:** Speak to JARVIS and hear it respond. Hands-free.

### 2.1 Wake Word Detection
- [ ] Integrate Porcupine (Picovoice) for offline wake word detection
- [ ] Wake word: "Hey JARVIS" or "JARVIS"
- [ ] On detection: play a soft activation sound + start listening
- [ ] On silence/end-of-speech: stop recording and process

### 2.2 Speech-to-Text (STT)
- [ ] Integrate OpenAI Whisper (whisper.cpp or faster-whisper for speed)
- [ ] Run locally — no API calls for STT
- [ ] Target: < 500ms transcription latency for short commands
- [ ] Strip filler words and normalise punctuation before sending to Claude

### 2.3 Text-to-Speech (TTS)
- [ ] Primary: ElevenLabs API — use a calm British male voice
- [ ] Fallback: Coqui TTS or Piper (local, no internet needed)
- [ ] Stream audio chunks as they arrive — don't wait for full sentence
- [ ] JARVIS should not interrupt itself if you speak during a response

### 2.4 Voice Activity Detection (VAD)
- [ ] Use Silero VAD to detect when the user has stopped speaking
- [ ] Threshold tuning so ambient noise doesn't trigger false positives
- [ ] Visual indicator in UI when JARVIS is "listening" vs "thinking" vs "speaking"

### 2.5 Audio Pipeline
- [ ] `jarvis/voice/listener.py` — microphone capture + VAD + Whisper
- [ ] `jarvis/voice/speaker.py` — TTS audio playback with queue
- [ ] `jarvis/voice/pipeline.py` — orchestrates the full listen → think → speak loop

---

## Phase 3 — HUD Frontend

**Goal:** An Iron Man-style interface that looks stunning on your monitor.

### 3.1 Design Language
The interface should feel like a real piece of technology from a near-future world.

- **Background**: Deep navy `#0a0e1a` with a subtle dot-grid or line-grid overlay
- **Primary colour**: Electric blue `#00aaff` for active elements and glow effects
- **Secondary**: Ice white `#e8f4ff` for text and rings
- **Accent**: Amber `#ffaa00` for warnings or secondary data
- **Typography**: `JetBrains Mono` or `IBM Plex Mono` — monospace, technical, clean
- **Animations**: All transitions ease-in-out, 200-400ms — snappy but not jarring
- **Glow effects**: CSS `box-shadow` and `filter: blur` for the blue halo effect

### 3.2 Central Orb
- [ ] Animated circle that breathes / pulses when idle
- [ ] Expands and glows when listening (listening state)
- [ ] Fast spin/pulse when thinking (processing state)
- [ ] Slow wave animation when speaking (speaking state)
- [ ] "JARVIS" logotype centred inside
- [ ] Outer ring with tick marks (like a compass or radar sweep)

### 3.3 HUD Chrome
- [ ] Corner bracket decorations (top-left, top-right, bottom-left, bottom-right)
- [ ] Top bar: current time (24h), date, system status
- [ ] Bottom bar: navigation icons (Home, Tasks, Terminal, Music, Settings)
- [ ] Thin horizontal scan line that sweeps down the screen periodically
- [ ] Subtle grid overlay on the background (CSS `background-image: linear-gradient`)

### 3.4 Voice Visualiser
- [ ] Real-time audio waveform / frequency bars around the orb when speaking
- [ ] Built with Web Audio API + Canvas
- [ ] Bars glow blue and animate to the TTS audio output
- [ ] Collapses back to the ring when silent

### 3.5 Conversation Panel
- [ ] Sliding panel (right side or bottom) for the conversation transcript
- [ ] JARVIS responses appear with a typing/streaming animation character by character
- [ ] User input shown above, JARVIS reply below — clean minimal layout
- [ ] Timestamp on each message
- [ ] Panel can be hidden — HUD should work in voice-only mode too

### 3.6 Status Indicators
- [ ] System status bar: CPU %, memory, uptime
- [ ] AWS connection status (green/red dot)
- [ ] Microphone status (active/inactive)
- [ ] LLM model indicator (which Claude model is active)

### 3.7 Tech
- [ ] React + Vite for the frontend build
- [ ] WebSocket connection to FastAPI backend for streaming responses
- [ ] Web Audio API for microphone capture and TTS playback
- [ ] CSS custom properties for the full colour system
- [ ] `framer-motion` for all transitions and animations

---

## Phase 4 — Tools & Skills

**Goal:** JARVIS can take real actions, not just answer questions.

### 4.1 Tool Framework
- [ ] `jarvis/tools/` — directory for all tool definitions
- [ ] Each tool: a Python function + JSON schema description passed to Claude
- [ ] Claude decides when to call tools; JARVIS executes and returns results
- [ ] Tool calls are shown visually in the HUD ("Executing: web_search...")

### 4.2 Core Tools (Day One)
- [ ] **`web_search`** — search the web via Brave Search API or SerpAPI
- [ ] **`get_time`** — current time and date (timezone-aware)
- [ ] **`open_app`** — open a Mac app by name (`open -a "Spotify"`)
- [ ] **`set_timer`** — set a countdown timer with audio alert
- [ ] **`read_clipboard`** / **`write_clipboard`** — read/write Mac clipboard
- [ ] **`run_shell`** — execute a shell command (with a safety allowlist)
- [ ] **`take_screenshot`** — capture the screen and pass the image to Claude
- [ ] **`save_note`** — save a note to a local markdown file

### 4.3 Developer Tools
- [ ] **`read_file`** / **`write_file`** — read and write files in a workspace
- [ ] **`git_status`** — run `git status` and summarise the output
- [ ] **`run_tests`** — trigger the CI suite locally and report results
- [ ] **`search_codebase`** — grep/ripgrep the working directory

### 4.4 Smart Home (Future)
- [ ] **`control_lights`** — Philips Hue / Home Assistant integration
- [ ] **`get_weather`** — current and forecast weather
- [ ] **`play_music`** — Spotify playback control
- [ ] **`send_message`** — send a message via iMessage or Slack

### 4.5 Raspberry Pi Integration (Future)
- [ ] JARVIS running on a Raspberry Pi as a dedicated always-on kiosk
- [ ] Small touchscreen HUD display
- [ ] Physical LED ring (NeoPixel) that lights up on wake word
- [ ] Hardware mute button

---

## Phase 5 — Infrastructure & Deployment

**Goal:** JARVIS runs locally for speed, with cloud as an always-on backup.

### 5.1 Local-First Architecture
- [ ] JARVIS runs on your Mac as a background service
- [ ] `launchd` plist to auto-start on login
- [ ] Local SQLite database for memory and conversation history
- [ ] All voice processing (STT, wake word) stays local

### 5.2 FastAPI Backend
- [ ] `jarvis/server.py` — FastAPI app
- [ ] `POST /chat` — text message endpoint
- [ ] `WS /stream` — WebSocket for streaming responses to the frontend
- [ ] `GET /status` — health check, returns active model, memory stats
- [ ] `POST /voice` — receive audio blob, return transcription + response

### 5.3 AWS Deployment (EC2 — already provisioned)
- [ ] Deploy the FastAPI backend to the dev EC2 instance
- [ ] Systemd service file for auto-restart
- [ ] Nginx reverse proxy + HTTPS (Let's Encrypt)
- [ ] Remote access: JARVIS frontend accessible from any browser
- [ ] Fill in the `app` job in `deploy.yml` with actual deploy steps (SCP + restart)

### 5.4 Secrets Management
- [ ] `ANTHROPIC_API_KEY` — already in GitHub secrets, needed in EC2 env too
- [ ] `ELEVENLABS_API_KEY` — add to GitHub environment secrets
- [ ] `.env` file on EC2, never committed to git
- [ ] Gitleaks already enforces no secrets in code

---

## Phase 6 — Polish & Advanced Features

**Goal:** JARVIS feels alive and complete.

### 6.1 Proactive JARVIS
- [ ] JARVIS can interrupt and speak without being asked (e.g. "Your 3pm meeting starts in 10 minutes")
- [ ] Calendar integration (Google Calendar API)
- [ ] Daily briefing: JARVIS summarises the day when you sit down at your desk
- [ ] Threshold alerts: notify if an AWS resource is down

### 6.2 Multi-Modal
- [ ] JARVIS can see your screen (screenshot tool feeding into Claude's vision)
- [ ] "What's wrong with this code?" — screenshot your editor, Claude analyses it
- [ ] Webcam integration: JARVIS knows if you're at your desk

### 6.3 Fine-Tuned Voice
- [ ] Record 30+ minutes of a target voice (or use ElevenLabs voice cloning)
- [ ] Clone a custom "JARVIS voice" that sounds exactly right
- [ ] Test and A/B different voice settings for naturalness

### 6.4 SOUL.md — JARVIS Identity File
- [ ] Defines JARVIS's personality, rules, capabilities, and self-knowledge
- [ ] Loaded into every conversation as part of the system prompt
- [ ] Includes: who the user is, JARVIS's purpose, what it can and cannot do
- [ ] Updated over time as JARVIS learns more about the user

---

## Build Order (Suggested)

```
Week 1:  Phase 1 — Agent brain + CLI + memory (test everything works)
Week 2:  Phase 2 — Voice pipeline (wake word + STT + TTS)
Week 3:  Phase 3 — HUD frontend (the fun part)
Week 4:  Phase 4 — Core tools (web search, shell, clipboard, notes)
Week 5:  Phase 5 — Backend + EC2 deploy
Week 6+: Phase 6 — Polish, advanced tools, Raspberry Pi
```

---

## Open Questions

- [ ] Local LLM vs Claude API? (Local = faster + offline, Claude = smarter)
- [ ] ElevenLabs voice vs local TTS? (ElevenLabs = better quality, local = free + offline)
- [ ] Mac-only or also support Linux/Windows?
- [ ] Raspberry Pi kiosk: dedicated hardware or reuse existing Pi?
- [ ] Wake word: "Hey JARVIS" (Porcupine) or always-on microphone?

---

## What Success Looks Like

You sit down at your desk. JARVIS says *"Good morning. You have two meetings today and a pull request waiting for review."*
You say *"Hey JARVIS, deploy to dev."*
The HUD lights up. JARVIS responds: *"Initiating deployment to dev environment. Standing by."*
The GitHub Actions workflow triggers. JARVIS reports back when it's done.

That's the goal.
