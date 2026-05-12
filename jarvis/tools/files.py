"""File system tools — list, find, open, inspect, move, delete files."""
import os
import subprocess
import shutil
import datetime
from pathlib import Path

_SAFE_ROOTS = [Path.home(), Path("/tmp")]

def _safe_path(raw: str) -> Path:
    p = Path(raw).expanduser().resolve()
    if not any(p == r or r in p.parents for r in _SAFE_ROOTS):
        raise PermissionError(f"Path outside safe roots: {p}")
    return p


def list_files(directory: str = "~", pattern: str = "*", agent=None) -> str:
    """List files/folders in a directory, up to 50 entries."""
    try:
        d = _safe_path(directory)
        if not d.exists():
            return f"Directory not found: {d}"
        items = sorted(d.glob(pattern))[:50]
        if not items:
            return f"No items matching '{pattern}' in {d}"
        lines = []
        for item in items:
            if item.is_dir():
                lines.append(f"[DIR]  {item.name}/")
            else:
                size_kb = item.stat().st_size / 1024
                lines.append(f"[FILE] {item.name}  ({size_kb:.1f} KB)")
        return f"{d}:\n" + "\n".join(lines)
    except Exception as e:
        return f"list_files failed: {e}"


def find_file(name: str, search_path: str = "~", agent=None) -> str:
    """Find files by name pattern (glob syntax) under a directory."""
    try:
        base = _safe_path(search_path)
        results = list(base.rglob(name))[:20]
        if not results:
            return f"No files named '{name}' found under {base}"
        return "\n".join(str(r) for r in results)
    except Exception as e:
        return f"find_file failed: {e}"


def open_file(path: str, agent=None) -> str:
    """Open a file or folder with the default macOS application."""
    try:
        p = _safe_path(path)
        if not p.exists():
            return f"File not found: {p}"
        subprocess.run(["open", str(p)], check=True)
        return f"Opened {p.name}."
    except Exception as e:
        return f"open_file failed: {e}"


def get_file_info(path: str, agent=None) -> str:
    """Return metadata for a file: type, size, created, modified."""
    try:
        p = _safe_path(path)
        if not p.exists():
            return f"File not found: {p}"
        stat = p.stat()
        created  = datetime.datetime.fromtimestamp(stat.st_ctime).strftime("%Y-%m-%d %H:%M")
        modified = datetime.datetime.fromtimestamp(stat.st_mtime).strftime("%Y-%m-%d %H:%M")
        size_kb  = stat.st_size / 1024
        kind     = "Directory" if p.is_dir() else (p.suffix.upper().lstrip(".") or "File")
        return f"{p.name}: {kind}, {size_kb:.1f} KB, modified {modified}, created {created}"
    except Exception as e:
        return f"get_file_info failed: {e}"


def move_file(source: str, destination: str, agent=None) -> str:
    """Move or rename a file or folder."""
    try:
        src = _safe_path(source)
        dst = _safe_path(destination)
        if not src.exists():
            return f"Source not found: {src}"
        shutil.move(str(src), str(dst))
        return f"Moved {src.name} → {dst}"
    except Exception as e:
        return f"move_file failed: {e}"


def delete_file(path: str, agent=None) -> str:
    """Move a file to the macOS Trash (safe — recoverable)."""
    try:
        p = _safe_path(path)
        if not p.exists():
            return f"File not found: {p}"
        subprocess.run(
            ["osascript", "-e", f'tell application "Finder" to delete POSIX file "{p}"'],
            check=True,
        )
        return f"Moved {p.name} to Trash."
    except Exception as e:
        return f"delete_file failed: {e}"
