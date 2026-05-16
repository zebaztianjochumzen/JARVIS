#!/usr/bin/env bash
# start.sh — Launch JARVIS backend + frontend locally
set -e

ROOT="$(cd "$(dirname "$0")" && pwd)"
VENV="$ROOT/.venv"

# ── Colours ───────────────────────────────────────────────────────────────────
GREEN="\033[0;32m"; YELLOW="\033[1;33m"; RED="\033[0;31m"; RESET="\033[0m"

info()  { echo -e "${GREEN}[JARVIS]${RESET} $*"; }
warn()  { echo -e "${YELLOW}[WARN]${RESET}  $*"; }
error() { echo -e "${RED}[ERROR]${RESET} $*"; exit 1; }

# ── Preflight checks ──────────────────────────────────────────────────────────
command -v python3 &>/dev/null || error "python3 not found. Install Python 3.11+."
command -v node    &>/dev/null || error "node not found. Install Node.js 18+."
command -v npm     &>/dev/null || error "npm not found."

# Require .env or AWS credentials
if [ ! -f "$ROOT/.env" ]; then
  if ! aws sts get-caller-identity &>/dev/null 2>&1; then
    warn ".env not found and AWS credentials not configured."
    warn "Copy .env.example → .env and fill in at least ANTHROPIC_API_KEY."
  else
    info "No .env — using AWS Secrets Manager for credentials."
  fi
fi

# ── Virtualenv ────────────────────────────────────────────────────────────────
if [ ! -d "$VENV" ]; then
  info "Creating virtualenv at .venv ..."
  python3 -m venv "$VENV"
fi

# Activate
source "$VENV/bin/activate"

# Install/update Python deps
if ! python -c "import anthropic" &>/dev/null 2>&1; then
  info "Installing Python dependencies..."
  pip install -q -r "$ROOT/requirements.txt"
fi

# ── Frontend deps ─────────────────────────────────────────────────────────────
if [ ! -d "$ROOT/frontend/node_modules" ]; then
  info "Installing frontend dependencies..."
  npm --prefix "$ROOT/frontend" install --silent
fi

# ── Playwright browsers (optional — browser automation tool only) ─────────────
if ! python -c "
from playwright.sync_api import sync_playwright
p = sync_playwright().__enter__()
b = p.chromium.launch(); b.close(); p.stop()
" &>/dev/null 2>&1; then
  info "Installing Playwright browser (optional, browser automation)..."
  python -m playwright install chromium 2>/dev/null || warn "Playwright browser install failed — browser_navigate tool will be unavailable. Run 'python -m playwright install chromium' manually when online."
fi

# ── Clear stale processes on our ports ───────────────────────────────────────
for PORT in 8000 5173; do
  PID=$(lsof -ti:"$PORT" 2>/dev/null || true)
  if [ -n "$PID" ]; then
    warn "Port $PORT in use — killing PID $PID"
    kill "$PID" 2>/dev/null || true
    sleep 0.5
  fi
done

# ── Start backend ─────────────────────────────────────────────────────────────
info "Starting backend  → http://localhost:8000"
JARVIS_ENV="${JARVIS_ENV:-dev}" uvicorn api.main:app \
  --host 0.0.0.0 --port 8000 --reload \
  --app-dir "$ROOT" \
  2>&1 | sed 's/^/[backend] /' &
BACKEND_PID=$!

# ── Inject frontend env vars from Secrets Manager ────────────────────────────
FRONTEND_ENV="$ROOT/frontend/.env.local"
> "$FRONTEND_ENV"  # truncate / create

MAPBOX_TOKEN=$(aws secretsmanager get-secret-value \
  --secret-id "jarvis/${JARVIS_ENV:-dev}/mapbox-token" \
  --query SecretString --output text 2>/dev/null || true)
if [ -n "$MAPBOX_TOKEN" ]; then
  echo "VITE_MAPBOX_TOKEN=$MAPBOX_TOKEN" >> "$FRONTEND_ENV"
  info "Mapbox token loaded from Secrets Manager."
else
  warn "Mapbox token not found in Secrets Manager — map will show token error."
fi

# ── Start frontend ────────────────────────────────────────────────────────────
info "Starting frontend → http://localhost:5173"
npm --prefix "$ROOT/frontend" run dev 2>&1 | sed 's/^/[frontend] /' &
FRONTEND_PID=$!

echo ""
info "JARVIS is running."
info "  HUD → http://localhost:5173"
info "  API → http://localhost:8000/api/status"
echo ""
info "Press Ctrl+C to stop."

# ── Shut both down on Ctrl+C ──────────────────────────────────────────────────
trap 'echo ""; info "Shutting down..."; kill $BACKEND_PID $FRONTEND_PID 2>/dev/null; exit 0' INT TERM

wait
