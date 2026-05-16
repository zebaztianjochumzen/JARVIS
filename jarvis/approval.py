"""Approval queue — human-in-the-loop checkpoints for dangerous JARVIS tool calls.

When Claude calls a tool in DANGEROUS_TOOLS, execution is paused and an
approval request is broadcast to:
  1. The HUD via WebSocket (shows an approval modal in the browser)
  2. Telegram (user sees a yes/no prompt on mobile)

The agent thread blocks for up to APPROVAL_TIMEOUT_SECONDS waiting for a
decision. If no decision arrives, the call is denied (safe default).

Usage (automatic — wired into execute_tool in jarvis/tools/__init__.py):
  from jarvis.approval import needs_approval, request_approval
  if needs_approval(tool_name):
      approved = request_approval(tool_name, tool_input)
      if not approved:
          return "Cancelled: approval denied or timed out."

Adding a new tool to the dangerous list:
  DANGEROUS_TOOLS.add("my_new_tool")
"""

import threading
import time
import uuid
from typing import Any, Optional

APPROVAL_TIMEOUT_SECONDS = 60

# Tools that require explicit user approval before execution
DANGEROUS_TOOLS: set[str] = {
    "run_shell",
    "delete_file",
    "write_file",
    "move_file",
    "delete_calendar_event",
    "browser_execute_js",
    "run_tests",
}

# Pending approvals: approval_id → {"tool", "input", "event", "decision"}
_pending: dict[str, dict] = {}
_lock    = threading.Lock()

# Registered broadcast callbacks (added by api/main.py)
_broadcast_callbacks: list = []


# ── Public API ────────────────────────────────────────────────────────────────

def needs_approval(tool_name: str) -> bool:
    return tool_name in DANGEROUS_TOOLS


def request_approval(tool_name: str, tool_input: dict) -> bool:
    """Block the calling thread until the user approves or the timeout expires.

    Returns True (approved) or False (denied / timed out).
    """
    approval_id = str(uuid.uuid4())[:8]
    event       = threading.Event()

    entry = {
        "id":       approval_id,
        "tool":     tool_name,
        "input":    tool_input,
        "event":    event,
        "decision": None,       # set to True/False by resolve()
        "ts":       time.strftime("%H:%M:%S"),
    }

    with _lock:
        _pending[approval_id] = entry

    _broadcast_approval_request(approval_id, tool_name, tool_input)

    granted = event.wait(timeout=APPROVAL_TIMEOUT_SECONDS)

    with _lock:
        decision = _pending.pop(approval_id, {}).get("decision", False)

    if not granted:
        print(f"[Approval] '{tool_name}' timed out — denied.", flush=True)
        return False

    print(f"[Approval] '{tool_name}' → {'APPROVED' if decision else 'DENIED'}", flush=True)
    return bool(decision)


def resolve(approval_id: str, approved: bool) -> bool:
    """Called by the /api/approve endpoint or a chat channel handler.

    Returns True if the ID was found and resolved, False if already gone.
    """
    with _lock:
        entry = _pending.get(approval_id)
        if not entry:
            return False
        entry["decision"] = approved
        entry["event"].set()
    return True


def list_pending() -> list[dict]:
    """Return pending approvals (sans the threading.Event) for the REST endpoint."""
    with _lock:
        return [
            {"id": v["id"], "tool": v["tool"], "input": v["input"], "ts": v["ts"]}
            for v in _pending.values()
        ]


def register_broadcast(callback) -> None:
    """Register a callable(payload: dict) that broadcasts to connected clients."""
    _broadcast_callbacks.append(callback)


# ── Internal ──────────────────────────────────────────────────────────────────

def _broadcast_approval_request(approval_id: str, tool_name: str, tool_input: dict) -> None:
    payload = {
        "type":        "approval_request",
        "approval_id": approval_id,
        "tool":        tool_name,
        "input":       tool_input,
        "timeout":     APPROVAL_TIMEOUT_SECONDS,
        "message": (
            f"JARVIS wants to run `{tool_name}`. "
            f"Reply 'yes {approval_id}' to approve or 'no {approval_id}' to deny."
        ),
    }
    for cb in _broadcast_callbacks:
        try:
            cb(payload)
        except Exception:
            pass

    print(
        f"[Approval] Waiting for approval: {tool_name} (id={approval_id}, "
        f"timeout={APPROVAL_TIMEOUT_SECONDS}s)",
        flush=True,
    )
