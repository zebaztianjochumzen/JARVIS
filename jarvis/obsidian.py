"""Obsidian vault sync — mirrors JARVIS memory into a live Obsidian vault.

Set OBSIDIAN_VAULT_PATH in .env to activate. When set, every fact JARVIS
stores or deletes is immediately reflected as a markdown note inside:

    <vault>/JARVIS/Memory/Facts/<key>.md

A live index note at <vault>/JARVIS/Memory/Memory.md lists all facts.
Context summaries land at <vault>/JARVIS/Memory/Context.md.
Daily summaries at <vault>/JARVIS/Memory/Daily/<YYYY-MM-DD>.md.

If the vault path does not exist or is not set, all functions silently
no-op so JARVIS works without Obsidian.
"""

import os
from datetime import datetime
from pathlib import Path
from typing import Optional


# ── Vault helpers ─────────────────────────────────────────────────────────────

def _vault() -> Optional[Path]:
    raw = os.environ.get("OBSIDIAN_VAULT_PATH", "").strip()
    if not raw:
        return None
    p = Path(raw)
    return p if p.exists() else None


def _ensure(path: Path) -> Path:
    path.mkdir(parents=True, exist_ok=True)
    return path


def _safe_key(key: str) -> str:
    """Turn a fact key into a filesystem-safe filename stem."""
    return key.replace("/", "-").replace(":", "-").replace("\\", "-").strip()


# ── Fact notes ────────────────────────────────────────────────────────────────

def write_fact(key: str, value: str) -> bool:
    """Create or update a fact note in the vault. Returns True on success."""
    vault = _vault()
    if not vault:
        return False
    try:
        facts_dir = _ensure(vault / "JARVIS" / "Memory" / "Facts")
        note_path = facts_dir / f"{_safe_key(key)}.md"
        now       = datetime.now()

        # Preserve original created date if note already exists
        created = now.isoformat()
        if note_path.exists():
            for line in note_path.read_text(encoding="utf-8").splitlines():
                if line.startswith("created:"):
                    created = line.split(":", 1)[1].strip()
                    break

        display_key = key.replace("_", " ").title()
        content = (
            f"---\n"
            f"type: fact\n"
            f"key: {key}\n"
            f"created: {created}\n"
            f"updated: {now.isoformat()}\n"
            f"tags: [jarvis, memory, fact]\n"
            f"---\n\n"
            f"# {display_key}\n\n"
            f"> **{value}**\n\n"
            f"*Last updated by JARVIS — {now.strftime('%B %d, %Y at %H:%M')}*\n\n"
            f"[[Memory]] · [[Context]]\n"
        )
        note_path.write_text(content, encoding="utf-8")
        _rebuild_index(vault)
        return True
    except Exception:
        return False


def delete_fact(key: str) -> bool:
    """Remove a fact note from the vault."""
    vault = _vault()
    if not vault:
        return False
    try:
        note_path = vault / "JARVIS" / "Memory" / "Facts" / f"{_safe_key(key)}.md"
        if note_path.exists():
            note_path.unlink()
        _rebuild_index(vault)
        return True
    except Exception:
        return False


# ── Context summary ───────────────────────────────────────────────────────────

def write_context_summary(summary: str) -> bool:
    """Overwrite Context.md with the latest rolling context compression."""
    vault = _vault()
    if not vault:
        return False
    try:
        mem_dir   = _ensure(vault / "JARVIS" / "Memory")
        ctx_path  = mem_dir / "Context.md"
        now       = datetime.now()
        content = (
            f"---\n"
            f"type: context_summary\n"
            f"updated: {now.isoformat()}\n"
            f"tags: [jarvis, context]\n"
            f"---\n\n"
            f"# Current Context\n\n"
            f"*Compressed by JARVIS — {now.strftime('%B %d, %Y at %H:%M')}*\n\n"
            f"{summary}\n\n"
            f"[[Memory]] · [[Facts/]]\n"
        )
        ctx_path.write_text(content, encoding="utf-8")
        return True
    except Exception:
        return False


# ── Daily summary ─────────────────────────────────────────────────────────────

def write_daily_summary(summary: str, date: Optional[datetime] = None) -> bool:
    """Append or create a daily conversation digest note."""
    vault = _vault()
    if not vault:
        return False
    try:
        date      = date or datetime.now()
        daily_dir = _ensure(vault / "JARVIS" / "Memory" / "Daily")
        note_path = daily_dir / f"{date.strftime('%Y-%m-%d')}.md"
        now       = datetime.now()

        header = (
            f"---\n"
            f"type: daily_summary\n"
            f"date: {date.strftime('%Y-%m-%d')}\n"
            f"tags: [jarvis, daily]\n"
            f"---\n\n"
            f"# JARVIS — {date.strftime('%B %d, %Y')}\n\n"
        )

        if note_path.exists():
            existing = note_path.read_text(encoding="utf-8")
            content  = existing.rstrip() + f"\n\n---\n\n*Update {now.strftime('%H:%M')}*\n\n{summary}\n"
        else:
            content = header + f"*{now.strftime('%H:%M')}*\n\n{summary}\n\n[[Memory]] · [[Context]]\n"

        note_path.write_text(content, encoding="utf-8")
        return True
    except Exception:
        return False


# ── Index ─────────────────────────────────────────────────────────────────────

def _rebuild_index(vault: Path) -> None:
    """Regenerate Memory.md — the master index of all fact notes."""
    try:
        facts_dir  = vault / "JARVIS" / "Memory" / "Facts"
        mem_dir    = _ensure(vault / "JARVIS" / "Memory")
        index_path = mem_dir / "Memory.md"
        now        = datetime.now()

        fact_files = sorted(facts_dir.glob("*.md")) if facts_dir.exists() else []
        links      = "\n".join(f"- [[Facts/{f.stem}]]" for f in fact_files)

        content = (
            f"---\n"
            f"type: index\n"
            f"updated: {now.isoformat()}\n"
            f"tags: [jarvis, index]\n"
            f"---\n\n"
            f"# JARVIS Memory\n\n"
            f"*{len(fact_files)} fact(s) · updated {now.strftime('%B %d, %Y at %H:%M')}*\n\n"
            f"## Facts\n\n"
            f"{links or '_No facts stored yet._'}\n\n"
            f"## Navigation\n\n"
            f"- [[Context]] — Rolling context compression\n"
            f"- [[Daily/]] — Day-by-day summaries\n"
        )
        index_path.write_text(content, encoding="utf-8")
    except Exception:
        pass


def vault_status() -> str:
    """Return a short status string for the /api/memories endpoint."""
    vault = _vault()
    if not vault:
        return "Obsidian vault not configured (set OBSIDIAN_VAULT_PATH)"
    facts_dir  = vault / "JARVIS" / "Memory" / "Facts"
    fact_count = len(list(facts_dir.glob("*.md"))) if facts_dir.exists() else 0
    return f"Vault: {vault} · {fact_count} fact note(s)"
