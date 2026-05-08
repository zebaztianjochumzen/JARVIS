"""Basic Phase 1 tools — time, notes, memory read/write."""

from datetime import datetime
from pathlib import Path


def get_current_time() -> str:
    now = datetime.now()
    return now.strftime("%A, %d %B %Y — %H:%M:%S")


def save_note(content: str) -> str:
    notes_path = Path.home() / ".jarvis" / "notes.md"
    notes_path.parent.mkdir(parents=True, exist_ok=True)
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M")
    with open(notes_path, "a") as f:
        f.write(f"\n## {timestamp}\n{content}\n")
    return f"Note saved to {notes_path}"


def remember_this(key: str, value: str, memory: object) -> str:
    memory.set_fact(key, value)  # type: ignore[attr-defined]
    return f"Stored: {key} = {value}"


def recall_fact(key: str, memory: object) -> str:
    value = memory.get_fact(key)  # type: ignore[attr-defined]
    return value if value is not None else f"No fact found for '{key}'"


def forget_fact(key: str, memory: object) -> str:
    memory.delete_fact(key)  # type: ignore[attr-defined]
    return f"Forgotten: {key}"
