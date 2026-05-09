"""Developer tools — file access, git, tests, codebase search."""

import os
import subprocess
from pathlib import Path

# Root of the JARVIS workspace
WORKSPACE = Path(__file__).parent.parent.parent.resolve()


def _safe_path(rel: str) -> Path:
    full = (WORKSPACE / rel).resolve()
    if not str(full).startswith(str(WORKSPACE)):
        raise ValueError(f"Path outside workspace: {rel}")
    return full


def read_file(path: str, agent=None) -> str:
    try:
        full = _safe_path(path)
        text = full.read_text()
        lines = text.splitlines()
        if len(lines) > 200:
            text = "\n".join(lines[:200]) + f"\n… ({len(lines)-200} more lines)"
        return text or "(empty file)"
    except ValueError as e:
        return str(e)
    except FileNotFoundError:
        return f"File not found: {path}"
    except Exception as e:
        return f"Read error: {e}"


def write_file(path: str, content: str, agent=None) -> str:
    try:
        full = _safe_path(path)
        full.parent.mkdir(parents=True, exist_ok=True)
        full.write_text(content)
        return f"Written: {path} ({len(content)} bytes)"
    except ValueError as e:
        return str(e)
    except Exception as e:
        return f"Write error: {e}"


def git_status(agent=None) -> str:
    def run(cmd):
        return subprocess.run(cmd, capture_output=True, text=True, cwd=WORKSPACE).stdout.strip()

    branch = run(["git", "branch", "--show-current"])
    status = run(["git", "status", "--short"]) or "(clean)"
    log    = run(["git", "log", "--oneline", "-8"])
    return f"Branch: {branch}\n\nStatus:\n{status}\n\nRecent commits:\n{log}"


def run_tests(test_path: str = ".", agent=None) -> str:
    try:
        r = subprocess.run(
            ["python3", "-m", "pytest", test_path, "-v", "--tb=short"],
            capture_output=True, text=True, timeout=60, cwd=WORKSPACE,
        )
        output = (r.stdout + r.stderr).strip()
        return output[:3000] or "(no output)"
    except subprocess.TimeoutExpired:
        return "Tests timed out after 60 s."
    except Exception as e:
        return f"Test runner error: {e}"


def search_codebase(pattern: str, path: str = ".", agent=None) -> str:
    for cmd in (
        ["rg", "--line-number", "--no-heading", pattern, path],
        ["grep", "-rn",  pattern, path],
    ):
        try:
            r = subprocess.run(cmd, capture_output=True, text=True, timeout=15, cwd=WORKSPACE)
            if r.returncode in (0, 1):
                output = r.stdout.strip()
                if not output:
                    return f"No matches for '{pattern}' in {path}."
                lines = output.splitlines()
                if len(lines) > 60:
                    output = "\n".join(lines[:60]) + f"\n… ({len(lines)-60} more)"
                return output
        except FileNotFoundError:
            continue
        except subprocess.TimeoutExpired:
            return "Search timed out."
    return "Search tool not available."
