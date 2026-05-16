"""Heartbeat scheduler — dynamic, file-driven replacement for the hardcoded scheduler.

Reads HEARTBEAT.md from the repo root every `interval_minutes` minutes.
Edit that file to add, remove, or change scheduled tasks — no code changes
or server restarts needed.

Cron expressions are standard 5-field format:
  minute  hour  day-of-month  month  day-of-week
  0       8     *             *      *           → 08:00 every day
  */30    9-17  *             *      1-5         → every 30 min, weekdays 9–17

Tasks are broadcast to the same WebSocket queue used by the existing
scheduler.py so the WebSocket handler picks them up automatically.

Falls back gracefully if HEARTBEAT.md is missing or has parse errors
(the existing scheduler.py tasks continue to run independently).
"""

import os
import re
import threading
import time
from datetime import datetime
from pathlib import Path
from typing import Any, Optional

HEARTBEAT_PATH = Path(__file__).parent.parent / "HEARTBEAT.md"

_clients: list  = []   # shared with scheduler.add_client / remove_client
_lock           = threading.Lock()
_started        = False
_last_fired: dict[str, str] = {}   # task_id → "YYYY-MM-DD HH:MM" of last fire


# ── Public API ────────────────────────────────────────────────────────────────

def start(client_list: list, client_lock: threading.Lock) -> None:
    """Start the heartbeat loop in a daemon thread.

    Shares the same client_list and lock as scheduler.py so broadcasts
    reach all connected WebSocket sessions.
    """
    global _started, _clients, _lock
    if _started:
        return
    _started = True
    _clients = client_list
    _lock    = client_lock

    t = threading.Thread(target=_loop, daemon=True, name="heartbeat")
    t.start()
    print("[Heartbeat] Started — watching HEARTBEAT.md", flush=True)


def reload() -> str:
    """Force re-parse of HEARTBEAT.md (used by the /api/heartbeat/reload endpoint)."""
    tasks = _parse_heartbeat()
    if tasks is None:
        return "HEARTBEAT.md not found or has parse errors."
    return f"Loaded {len(tasks)} task(s): {', '.join(t['id'] for t in tasks)}"


# ── Internal ──────────────────────────────────────────────────────────────────

def _broadcast(payload: dict) -> None:
    import queue
    with _lock:
        targets = list(_clients)
    for q in targets:
        try:
            q.put_nowait(payload)
        except Exception:
            pass


def _loop() -> None:
    while True:
        try:
            _tick()
        except Exception as exc:
            print(f"[Heartbeat] Tick error: {exc}", flush=True)
        time.sleep(60)   # check every minute for cron matches


def _tick() -> None:
    tasks = _parse_heartbeat()
    if not tasks:
        return

    now = datetime.now()

    for task in tasks:
        if not task.get("enabled", True):
            continue

        cron = task.get("cron", "")
        if not _cron_matches(cron, now):
            continue

        # Deduplicate: only fire once per minute window
        fire_key = now.strftime("%Y-%m-%d %H:%M")
        if _last_fired.get(task["id"]) == fire_key:
            continue

        _last_fired[task["id"]] = fire_key
        prompt = task.get("prompt", "").strip()
        if not prompt:
            continue

        _broadcast({
            "type":    "scheduled_task",
            "task":    task["id"],
            "message": prompt,
        })
        print(f"[Heartbeat] Fired: {task['id']} at {fire_key}", flush=True)


def _parse_heartbeat() -> Optional[list[dict]]:
    """Parse HEARTBEAT.md and return a list of task dicts."""
    if not HEARTBEAT_PATH.exists():
        return None

    try:
        content = HEARTBEAT_PATH.read_text(encoding="utf-8")
    except Exception:
        return None

    # Extract the YAML block inside the ```yaml ... ``` fence
    match = re.search(r"```yaml\s*(.*?)```", content, re.DOTALL)
    if not match:
        return None

    yaml_block = match.group(1).strip()

    try:
        import yaml  # PyYAML
        data  = yaml.safe_load(yaml_block)
        tasks = data.get("tasks", []) if isinstance(data, dict) else []
        return tasks if isinstance(tasks, list) else []
    except ImportError:
        # Fallback: minimal parser for the simple format used in HEARTBEAT.md
        return _minimal_yaml_parse(yaml_block)
    except Exception as exc:
        print(f"[Heartbeat] YAML parse error: {exc}", flush=True)
        return None


def _minimal_yaml_parse(yaml_text: str) -> list[dict]:
    """Ultra-minimal YAML list parser — avoids requiring PyYAML."""
    tasks: list[dict] = []
    current: dict[str, Any] = {}

    for line in yaml_text.splitlines():
        stripped = line.strip()

        if stripped.startswith("- id:"):
            if current.get("id"):
                tasks.append(current)
            current = {"id": stripped.split(":", 1)[1].strip()}

        elif stripped.startswith("enabled:"):
            val = stripped.split(":", 1)[1].strip().lower()
            current["enabled"] = val not in ("false", "no", "0")

        elif stripped.startswith("cron:"):
            current["cron"] = stripped.split(":", 1)[1].strip().strip('"')

        elif stripped.startswith("prompt:"):
            rest = stripped.split(":", 1)[1].strip().lstrip(">").strip()
            current["prompt"] = rest

    if current.get("id"):
        tasks.append(current)

    return tasks


def _cron_matches(expr: str, now: datetime) -> bool:
    """Check whether a 5-field cron expression matches the given datetime."""
    try:
        parts = expr.strip().split()
        if len(parts) != 5:
            return False

        minute, hour, dom, month, dow = parts

        def _field(spec: str, value: int, lo: int, hi: int) -> bool:
            if spec == "*":
                return True
            if spec.startswith("*/"):
                step = int(spec[2:])
                return value % step == 0
            if "-" in spec and "/" not in spec:
                a, b = spec.split("-")
                return int(a) <= value <= int(b)
            if "-" in spec and "/" in spec:
                rng, step = spec.split("/")
                a, b = rng.split("-")
                return int(a) <= value <= int(b) and (value - int(a)) % int(step) == 0
            return value == int(spec)

        return (
            _field(minute, now.minute,    0, 59)
            and _field(hour,   now.hour,   0, 23)
            and _field(dom,    now.day,    1, 31)
            and _field(month,  now.month,  1, 12)
            and _field(dow,    now.weekday(), 0, 6)
        )
    except Exception:
        return False
