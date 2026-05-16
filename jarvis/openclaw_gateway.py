"""OpenClaw Gateway — multi-platform messaging bridge for JARVIS.

Routes incoming messages from Telegram, WhatsApp, Discord, Signal, and
iMessage through the same JarvisAgent.ask() pipeline. One brain, all
platforms. Also enforces guest-session sandboxing so family/friends get
a restricted tool set without shell or file-write access.

Architecture:
  OpenClaw Gateway (separate process, port 18789)
    ↓  POST /openclaw/agent/execute
  JARVIS FastAPI (api/main.py mounts OpenClaw routers)
    ↓  JarvisAgentAdapter.execute(query, session_name)
  Agent.ask(query, tool_filter=GUEST_BLOCKED if guest)
    ↓  response text
  OpenClaw → originating platform (WhatsApp / Discord / etc.)

Session trust model:
  Admin sessions  — full tool access (your own accounts)
  Guest sessions  — sandboxed: no shell, no file writes, no browser

Setup:
  1. npm install -g openclaw@latest && openclaw onboard && openclaw start
  2. Set OPENCLAW_GATEWAY_WS_URL=ws://localhost:18789 in .env
  3. Set OPENCLAW_API_KEY=<your-secret> in .env
  4. Set OPENCLAW_ADMIN_SESSIONS=telegram:dm:123456789 (comma-separated)
     to grant your account full operator access.
"""

import os
import threading
from typing import Optional

_started    = False
_gateway_ok = False
_adapter: Optional["JarvisAgentAdapter"] = None

# Tools blocked for sandboxed guest sessions
GUEST_BLOCKED_TOOLS: frozenset[str] = frozenset({
    "run_shell",
    "write_file",
    "delete_file",
    "move_file",
    "browser_navigate",
    "browser_click",
    "browser_fill",
    "browser_execute_js",
    "browser_screenshot",
    "browser_extract_text",
    "draft_email",
    "git_status",
    "run_tests",
    "search_codebase",
    "read_file",
})

_admin_sessions: set[str] = set()


# ── Public API ────────────────────────────────────────────────────────────────

def start(agent_factory) -> None:
    """Start the OpenClaw gateway bridge in a daemon thread."""
    global _started, _adapter

    ws_url = os.environ.get("OPENCLAW_GATEWAY_WS_URL", "").strip()
    if _started:
        return
    if not ws_url:
        print("[OpenClaw] OPENCLAW_GATEWAY_WS_URL not set — gateway disabled.", flush=True)
        return

    _started = True

    raw = os.environ.get("OPENCLAW_ADMIN_SESSIONS", "").strip()
    _admin_sessions.update(s.strip() for s in raw.split(",") if s.strip())

    _adapter = JarvisAgentAdapter(agent_factory)

    t = threading.Thread(target=_run, daemon=True, name="openclaw-gateway")
    t.start()
    print(f"[OpenClaw] Gateway thread started (ws: {ws_url})", flush=True)


def get_adapter() -> Optional["JarvisAgentAdapter"]:
    """Return the adapter for use by FastAPI routers."""
    return _adapter


def is_admin_session(session_name: str) -> bool:
    """True when the session has full operator-level tool access."""
    return not _admin_sessions or session_name in _admin_sessions


def get_status() -> dict:
    return {
        "running":        _started,
        "gateway_ok":     _gateway_ok,
        "admin_sessions": list(_admin_sessions),
        "configured":     bool(os.environ.get("OPENCLAW_GATEWAY_WS_URL", "").strip()),
    }


# ── JARVIS ↔ OpenClaw adapter ─────────────────────────────────────────────────

class JarvisAgentAdapter:
    """Presents JARVIS Agent as an OpenClaw-compatible executor.

    The OpenClaw FastAPI router calls adapter.execute(query, session_name).
    Guest sessions have dangerous tools stripped before the inference call.
    Each platform session gets its own persistent Agent instance so
    conversation history is preserved per-user.
    """

    def __init__(self, agent_factory) -> None:
        self._factory = agent_factory
        self._agents: dict[str, object] = {}  # session_name → Agent
        self._lock = threading.Lock()

    def _get_or_create(self, session_name: str):
        with self._lock:
            if session_name not in self._agents:
                self._agents[session_name] = self._factory()
            return self._agents[session_name]

    def execute(self, query: str, session_name: str = "main") -> str:
        """Synchronous execute — called by OpenClaw routers."""
        agent = self._get_or_create(session_name)
        tool_filter = None if is_admin_session(session_name) else GUEST_BLOCKED_TOOLS
        return agent.ask(query, tool_filter=tool_filter)

    def execute_stream(self, query: str, session_name: str = "main", stream_callback=None):
        """Streaming execute — yields response incrementally."""
        agent = self._get_or_create(session_name)
        tool_filter = None if is_admin_session(session_name) else GUEST_BLOCKED_TOOLS
        return agent.ask(query, stream_callback=stream_callback, tool_filter=tool_filter)

    def active_sessions(self) -> list[str]:
        with self._lock:
            return list(self._agents.keys())


# ── Background gateway connection ─────────────────────────────────────────────

def _run() -> None:
    global _gateway_ok

    try:
        from openclaw_sdk import OpenClawClient, ClientConfig
    except ImportError:
        print(
            "[OpenClaw] openclaw-sdk not installed.\n"
            "           Run: pip install openclaw-sdk",
            flush=True,
        )
        return

    import asyncio

    ws_url  = os.environ.get("OPENCLAW_GATEWAY_WS_URL", "ws://localhost:18789")
    api_key = os.environ.get("OPENCLAW_API_KEY", "")

    async def _main() -> None:
        global _gateway_ok
        try:
            from openclaw_sdk import ClientConfig
            from openclaw_sdk.gateways import LocalGateway

            config = ClientConfig(
                gateway_ws_url=ws_url,
                api_key=api_key,
                timeout=300,
            )
            client = OpenClawClient(config=config)
            await client.connect()
            _gateway_ok = True
            print("[OpenClaw] Connected to gateway.", flush=True)
            # Hold connection open — SDK handles inbound message routing
            await asyncio.sleep(float("inf"))

        except Exception as exc:
            _gateway_ok = False
            print(f"[OpenClaw] Gateway connection failed: {exc}", flush=True)

    loop = asyncio.new_event_loop()
    loop.run_until_complete(_main())
