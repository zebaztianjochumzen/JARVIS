# JARVIS

Just A Rather Very Intelligent System — a personal AI operating system built around one person.

One brain accessible from the browser HUD or Telegram. Calm, precise, quietly capable.

---

## Requirements

- **Python 3.11+**
- **Node.js 18+**
- **AWS CLI** configured (or a `.env` file — see below)

---

## Quick start

```bash
git clone <repo>
cd JARVIS
./start.sh
```

Open **http://localhost:5173** in your browser. Done.

The script handles everything on first run: Python packages, Node modules, Playwright browser.

---

## Configuration

JARVIS pulls secrets from **AWS Secrets Manager** by default (used in production).
For local dev, create a `.env` file instead:

```bash
cp .env.example .env
# then fill in the values
```

### Required

| Variable | Where to get it |
|---|---|
| `ANTHROPIC_API_KEY` | console.anthropic.com |

### Optional (enables more features)

| Variable | Feature |
|---|---|
| `TELEGRAM_BOT_TOKEN` | Talk to JARVIS via Telegram — create a bot with [@BotFather](https://t.me/BotFather) |
| `TELEGRAM_OWNER_ID` | Your Telegram user ID — get it from [@userinfobot](https://t.me/userinfobot) |
| `ELEVENLABS_API_KEY` | High-quality TTS voice (falls back to free edge-tts without it) |
| `SPOTIFY_CLIENT_ID` / `SPOTIFY_CLIENT_SECRET` / `SPOTIFY_REFRESH_TOKEN` | Music control — run `python scripts/spotify_auth.py` to generate the refresh token |
| `GOOGLE_CREDENTIALS` / `GOOGLE_CALENDAR_TOKEN` / `GOOGLE_GMAIL_TOKEN` | Calendar + Gmail integration |
| `OBSIDIAN_VAULT_PATH` | Mirror JARVIS memories into an Obsidian vault |

---

## Manual start (without the script)

```bash
# Terminal 1 — backend
JARVIS_ENV=dev uvicorn api.main:app --host 0.0.0.0 --port 8000 --reload

# Terminal 2 — frontend
cd frontend && npm run dev
```

---

## Structure

```
JARVIS/
├── api/            FastAPI backend + WebSocket gateway
├── jarvis/         Core agent, tools, memory, voice, Telegram bot
├── frontend/       React HUD (browser interface)
├── vision/         Camera + gesture server
├── skills/         Pluggable skill definitions
├── scripts/        Utility scripts (Spotify auth, etc.)
├── terraform/      AWS infrastructure (EC2 deployment)
├── start.sh        One-command local launcher
└── .env.example    Config template
```

---

## Talking to JARVIS

**Browser** — open http://localhost:5173, type or speak into the HUD.

**Telegram** — message your bot directly. JARVIS responds as a full agent with access to all tools.

---

## Production (EC2)

Infrastructure lives in `terraform/`. Deploy with:

```bash
cd terraform
terraform init
terraform apply
```

Secrets are stored in AWS Secrets Manager under `jarvis/prod/*`.
