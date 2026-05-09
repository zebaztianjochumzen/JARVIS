"""System tools — timer, app launcher, shell, screenshot, clipboard."""

import os
import subprocess
import threading

SHELL_ALLOWLIST = {
    "ls", "pwd", "echo", "date", "whoami", "uname", "hostname",
    "df", "du", "ps", "uptime", "top",
    "cat", "head", "tail", "wc", "grep", "sort", "uniq",
    "find", "which", "env", "printenv",
    "ping", "curl", "wget",
    "python3", "node",
}


def set_timer(duration_seconds: int, label: str = "Timer", agent=None) -> str:
    def _ring():
        import time
        time.sleep(duration_seconds)
        subprocess.run([
            "osascript", "-e",
            f'display notification "Time\'s up: {label}" with title "JARVIS" sound name "Glass"',
        ], check=False)

    threading.Thread(target=_ring, daemon=True).start()
    m, s = divmod(duration_seconds, 60)
    h, m = divmod(m, 60)
    parts = [f"{h}h" if h else "", f"{m}m" if m else "", f"{s}s" if s else ""]
    return f"Timer set — {label}: {' '.join(p for p in parts if p)}"


def open_app(app_name: str, agent=None) -> str:
    try:
        r = subprocess.run(["open", "-a", app_name], capture_output=True, text=True)
        return f"Opened {app_name}." if r.returncode == 0 else f"Could not open '{app_name}': {r.stderr.strip()}"
    except Exception as e:
        return f"open_app failed: {e}"


def run_shell(command: str, agent=None) -> str:
    cmd_name = command.strip().split()[0]
    if cmd_name not in SHELL_ALLOWLIST:
        return (
            f"'{cmd_name}' is not on the allowlist.\n"
            f"Allowed: {', '.join(sorted(SHELL_ALLOWLIST))}"
        )
    try:
        result = subprocess.run(
            command, shell=True, capture_output=True, text=True, timeout=15,
        )
        output = (result.stdout or result.stderr or "").strip()
        return output[:2000] or "(no output)"
    except subprocess.TimeoutExpired:
        return "Command timed out after 15 s."
    except Exception as e:
        return f"Shell error: {e}"


def take_screenshot(agent=None) -> str:
    """Capture the screen and describe it with Claude Vision."""
    import base64
    import anthropic

    path = "/tmp/jarvis_screenshot.png"
    try:
        subprocess.run(["screencapture", "-x", path], check=True, timeout=10)
    except Exception as e:
        return f"Screenshot capture failed: {e}"

    try:
        with open(path, "rb") as f:
            img_b64 = base64.b64encode(f.read()).decode()
        msg = anthropic.Anthropic().messages.create(
            model="claude-haiku-4-5-20251001",
            max_tokens=400,
            messages=[{
                "role": "user",
                "content": [
                    {"type": "image", "source": {"type": "base64", "media_type": "image/png", "data": img_b64}},
                    {"type": "text",  "text": "Describe what is on this computer screen concisely. Mention open apps, windows, and visible content."},
                ],
            }],
        )
        return msg.content[0].text
    except Exception as e:
        return f"Vision analysis failed: {e}"


def read_clipboard(agent=None) -> str:
    try:
        result = subprocess.run(["pbpaste"], capture_output=True, text=True)
        content = result.stdout
        return f"Clipboard:\n{content[:2000]}" if content else "Clipboard is empty."
    except Exception as e:
        return f"Clipboard read failed: {e}"


def write_clipboard(text: str, agent=None) -> str:
    try:
        subprocess.run(["pbcopy"], input=text.encode(), check=True)
        preview = text[:80] + ("…" if len(text) > 80 else "")
        return f"Copied to clipboard: {preview}"
    except Exception as e:
        return f"Clipboard write failed: {e}"
