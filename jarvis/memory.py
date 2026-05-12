"""SQLite-backed persistent memory for JARVIS.

Phase B additions:
  - fact_embeddings table  → semantic (vector) search via fastembed + cosine similarity
  - context_summaries table → stores compressed conversation summaries
  - Obsidian vault sync     → each fact is mirrored as a markdown note
"""

import json
import os
import sqlite3
from datetime import datetime
from pathlib import Path
from typing import Optional


def _db_path() -> Path:
    custom = os.getenv("JARVIS_MEMORY_PATH")
    if custom:
        return Path(custom)
    path = Path.home() / ".jarvis" / "memory.db"
    path.parent.mkdir(parents=True, exist_ok=True)
    return path


# ── Cosine similarity (numpy is always available via ultralytics) ─────────────

def _cosine(a: list[float], b: list[float]) -> float:
    import math
    dot = sum(x * y for x, y in zip(a, b))
    na  = math.sqrt(sum(x * x for x in a))
    nb  = math.sqrt(sum(x * x for x in b))
    if na == 0 or nb == 0:
        return 0.0
    return dot / (na * nb)


class Memory:
    def __init__(self) -> None:
        self._conn = sqlite3.connect(str(_db_path()), check_same_thread=False)
        self._conn.row_factory = sqlite3.Row
        self._init_schema()
        self._embed_model = None   # lazy-loaded fastembed model

    def _init_schema(self) -> None:
        self._conn.executescript("""
            CREATE TABLE IF NOT EXISTS facts (
                key        TEXT PRIMARY KEY,
                value      TEXT NOT NULL,
                updated_at TEXT NOT NULL
            );
            CREATE TABLE IF NOT EXISTS messages (
                id         INTEGER PRIMARY KEY AUTOINCREMENT,
                role       TEXT NOT NULL,
                content    TEXT NOT NULL,
                created_at TEXT NOT NULL
            );
            CREATE TABLE IF NOT EXISTS fact_embeddings (
                key       TEXT PRIMARY KEY,
                embedding TEXT NOT NULL
            );
            CREATE TABLE IF NOT EXISTS context_summaries (
                id         INTEGER PRIMARY KEY AUTOINCREMENT,
                summary    TEXT NOT NULL,
                created_at TEXT NOT NULL
            );
        """)
        self._conn.commit()

    # ── Embedding ─────────────────────────────────────────────────────────────

    def _embed(self, text: str) -> list[float]:
        """Embed text via fastembed (ONNX, no PyTorch required).
        Returns empty list if fastembed is not installed."""
        try:
            from fastembed import TextEmbedding
            if self._embed_model is None:
                self._embed_model = TextEmbedding()
                print("[Memory] fastembed model loaded for semantic search", flush=True)
            vecs = list(self._embed_model.embed([text]))
            return [float(x) for x in vecs[0]]
        except ImportError:
            return []
        except Exception:
            return []

    def _upsert_embedding(self, key: str, text: str) -> None:
        vec = self._embed(text)
        if not vec:
            return
        self._conn.execute(
            "INSERT INTO fact_embeddings (key, embedding) VALUES (?, ?)"
            " ON CONFLICT(key) DO UPDATE SET embedding=excluded.embedding",
            (key, json.dumps(vec)),
        )
        self._conn.commit()

    def _remove_embedding(self, key: str) -> None:
        self._conn.execute("DELETE FROM fact_embeddings WHERE key = ?", (key,))
        self._conn.commit()

    # ── Facts ─────────────────────────────────────────────────────────────────

    def set_fact(self, key: str, value: str) -> None:
        key  = key.lower().strip()
        now  = datetime.utcnow().isoformat()
        self._conn.execute(
            "INSERT INTO facts (key, value, updated_at) VALUES (?, ?, ?)"
            " ON CONFLICT(key) DO UPDATE SET value=excluded.value, updated_at=excluded.updated_at",
            (key, value.strip(), now),
        )
        self._conn.commit()
        # Async-safe: embed + Obsidian sync (both gracefully no-op on failure)
        self._upsert_embedding(key, f"{key}: {value}")
        try:
            from jarvis import obsidian
            obsidian.write_fact(key, value)
        except Exception:
            pass

    def get_fact(self, key: str) -> Optional[str]:
        row = self._conn.execute(
            "SELECT value FROM facts WHERE key = ?", (key.lower().strip(),)
        ).fetchone()
        return row["value"] if row else None

    def delete_fact(self, key: str) -> None:
        key = key.lower().strip()
        self._conn.execute("DELETE FROM facts WHERE key = ?", (key,))
        self._conn.commit()
        self._remove_embedding(key)
        try:
            from jarvis import obsidian
            obsidian.delete_fact(key)
        except Exception:
            pass

    def get_all_facts(self) -> dict[str, str]:
        rows = self._conn.execute("SELECT key, value FROM facts ORDER BY key").fetchall()
        return {row["key"]: row["value"] for row in rows}

    # ── Semantic search ───────────────────────────────────────────────────────

    def semantic_search(self, query: str, n: int = 5) -> list[tuple[str, str, float]]:
        """Return the top-n facts most semantically similar to query.

        Returns a list of (key, value, score) sorted by descending similarity.
        Falls back to substring match if embeddings are unavailable.
        """
        query_vec = self._embed(query)

        if query_vec:
            rows = self._conn.execute(
                "SELECT key, embedding FROM fact_embeddings"
            ).fetchall()

            scored: list[tuple[str, str, float]] = []
            for row in rows:
                try:
                    emb   = json.loads(row["embedding"])
                    score = _cosine(query_vec, emb)
                    val   = self.get_fact(row["key"])
                    if val is not None:
                        scored.append((row["key"], val, score))
                except Exception:
                    continue

            scored.sort(key=lambda x: x[2], reverse=True)
            return scored[:n]

        # Fallback: substring match
        q = query.lower()
        results = []
        for key, value in self.get_all_facts().items():
            if q in key or q in value.lower():
                results.append((key, value, 1.0))
        return results[:n]

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

    def count_messages(self) -> int:
        return self._conn.execute("SELECT COUNT(*) FROM messages").fetchone()[0]

    def clear_history(self) -> None:
        self._conn.execute("DELETE FROM messages")
        self._conn.commit()

    # ── Context compression ───────────────────────────────────────────────────

    def should_compress(self, threshold: int = 30) -> bool:
        """True when stored messages exceed the compression threshold."""
        return self.count_messages() > threshold

    def get_messages_for_compression(self, keep_recent: int = 15) -> list[dict]:
        """Return the oldest messages that should be summarised and pruned.

        Returns a list of dicts with keys: id, role, content.
        """
        total = self.count_messages()
        prune_count = max(0, total - keep_recent)
        if prune_count == 0:
            return []

        rows = self._conn.execute(
            "SELECT id, role, content FROM messages ORDER BY id ASC LIMIT ?",
            (prune_count,),
        ).fetchall()
        return [{"id": r["id"], "role": r["role"], "content": r["content"]} for r in rows]

    def store_context_summary(self, summary: str, pruned_ids: list[int]) -> None:
        """Persist a context summary and delete the pruned messages."""
        now = datetime.utcnow().isoformat()
        self._conn.execute(
            "INSERT INTO context_summaries (summary, created_at) VALUES (?, ?)",
            (summary, now),
        )
        if pruned_ids:
            placeholders = ",".join("?" * len(pruned_ids))
            self._conn.execute(
                f"DELETE FROM messages WHERE id IN ({placeholders})", pruned_ids
            )
        self._conn.commit()

        try:
            from jarvis import obsidian
            obsidian.write_context_summary(summary)
        except Exception:
            pass

    def get_context_summary(self) -> Optional[str]:
        """Return the most recent context compression summary, or None."""
        row = self._conn.execute(
            "SELECT summary FROM context_summaries ORDER BY id DESC LIMIT 1"
        ).fetchone()
        return row["summary"] if row else None

    def get_messages_with_context(self, limit: int = 20) -> list[dict[str, str]]:
        """Build the full message list: [context summary msg] + recent messages.

        This is what the agent should pass to Claude instead of bare
        get_recent_messages().
        """
        recent  = self.get_recent_messages(limit)
        summary = self.get_context_summary()
        if not summary:
            return recent

        context_msg = {
            "role":    "user",
            "content": f"[Context from earlier in our conversation: {summary}]",
        }
        # Insert summary before first real message so it anchors the history
        return [context_msg] + recent
