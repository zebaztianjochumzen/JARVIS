"""SQLite-backed persistent memory for JARVIS."""

import sqlite3
from datetime import datetime
from pathlib import Path
import os


def _db_path() -> Path:
    custom = os.getenv("JARVIS_MEMORY_PATH")
    if custom:
        return Path(custom)
    path = Path.home() / ".jarvis" / "memory.db"
    path.parent.mkdir(parents=True, exist_ok=True)
    return path


class Memory:
    def __init__(self) -> None:
        self._conn = sqlite3.connect(str(_db_path()), check_same_thread=False)
        self._conn.row_factory = sqlite3.Row
        self._init_schema()

    def _init_schema(self) -> None:
        self._conn.executescript("""
            CREATE TABLE IF NOT EXISTS facts (
                key   TEXT PRIMARY KEY,
                value TEXT NOT NULL,
                updated_at TEXT NOT NULL
            );
            CREATE TABLE IF NOT EXISTS messages (
                id         INTEGER PRIMARY KEY AUTOINCREMENT,
                role       TEXT NOT NULL,
                content    TEXT NOT NULL,
                created_at TEXT NOT NULL
            );
        """)
        self._conn.commit()

    # ── Facts ─────────────────────────────────────────────────────────────────

    def set_fact(self, key: str, value: str) -> None:
        now = datetime.utcnow().isoformat()
        self._conn.execute(
            "INSERT INTO facts (key, value, updated_at) VALUES (?, ?, ?)"
            " ON CONFLICT(key) DO UPDATE SET value=excluded.value, updated_at=excluded.updated_at",
            (key.lower().strip(), value.strip(), now),
        )
        self._conn.commit()

    def get_fact(self, key: str) -> str | None:
        row = self._conn.execute(
            "SELECT value FROM facts WHERE key = ?", (key.lower().strip(),)
        ).fetchone()
        return row["value"] if row else None

    def delete_fact(self, key: str) -> None:
        self._conn.execute("DELETE FROM facts WHERE key = ?", (key.lower().strip(),))
        self._conn.commit()

    def get_all_facts(self) -> dict[str, str]:
        rows = self._conn.execute("SELECT key, value FROM facts ORDER BY key").fetchall()
        return {row["key"]: row["value"] for row in rows}

    # ── Message history ───────────────────────────────────────────────────────

    def append_message(self, role: str, content: str) -> None:
        self._conn.execute(
            "INSERT INTO messages (role, content, created_at) VALUES (?, ?, ?)",
            (role, content, datetime.utcnow().isoformat()),
        )
        self._conn.commit()

    def get_recent_messages(self, limit: int = 20) -> list[dict[str, str]]:
        rows = self._conn.execute(
            "SELECT role, content FROM messages ORDER BY id DESC LIMIT ?", (limit,)
        ).fetchall()
        return [{"role": r["role"], "content": r["content"]} for r in reversed(rows)]

    def clear_history(self) -> None:
        self._conn.execute("DELETE FROM messages")
        self._conn.commit()
