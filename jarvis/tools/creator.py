"""AI creation tools — documents, HTML pages, emails, translation."""
import subprocess
from pathlib import Path

_DESKTOP = Path.home() / "Desktop"

_EXT_MAP = {
    "txt": ".txt", "text": ".txt",
    "md": ".md", "markdown": ".md",
    "html": ".html", "htm": ".html",
    "css": ".css",
    "js": ".js", "javascript": ".js",
    "py": ".py", "python": ".py",
    "code": ".txt",
}


def create_document(filename: str, content: str, file_type: str = "txt", agent=None) -> str:
    """Write content to a file on the Desktop and open it."""
    ext = _EXT_MAP.get(file_type.lower(), f".{file_type}")
    if not filename.endswith(ext):
        filename = filename + ext
    path = _DESKTOP / filename
    try:
        path.write_text(content, encoding="utf-8")
        subprocess.run(["open", str(path)], check=False)
        return f"Created and opened {filename} on your Desktop."
    except Exception as e:
        return f"create_document failed: {e}"


def draft_email(to: str, subject: str, body: str, agent=None) -> str:
    """Open Apple Mail with a pre-filled draft."""
    body_escaped = body.replace('"', '\\"').replace("\n", "\\n")
    script = f'''tell application "Mail"
        set newMsg to make new outgoing message with properties {{subject:"{subject}", content:"{body_escaped}"}}
        tell newMsg to make new to recipient with properties {{address:"{to}"}}
        activate
    end tell'''
    try:
        subprocess.run(["osascript", "-e", script], check=True)
        return f"Opened Mail draft to {to}: '{subject}'"
    except Exception as e:
        return f"draft_email failed: {e}"


def translate(text: str, target_language: str, agent=None) -> str:
    """Translate text to a target language using Claude."""
    import anthropic
    try:
        msg = anthropic.Anthropic().messages.create(
            model="claude-haiku-4-5-20251001",
            max_tokens=1000,
            messages=[{
                "role": "user",
                "content": (
                    f"Translate the following text to {target_language}. "
                    f"Return only the translation, nothing else.\n\n{text}"
                ),
            }],
        )
        return msg.content[0].text
    except Exception as e:
        return f"Translation failed: {e}"


def detect_language(text: str, agent=None) -> str:
    """Detect the language of a piece of text."""
    import anthropic
    try:
        msg = anthropic.Anthropic().messages.create(
            model="claude-haiku-4-5-20251001",
            max_tokens=50,
            messages=[{
                "role": "user",
                "content": (
                    f"Detect the language of this text and reply with ONLY the language name in English "
                    f"(e.g. 'Swedish', 'Spanish', 'French'). Text: {text}"
                ),
            }],
        )
        return msg.content[0].text.strip()
    except Exception as e:
        return f"Language detection failed: {e}"


def generate_html(description: str, filename: str = "jarvis_page", agent=None) -> str:
    """Generate a complete HTML page from a description, save to Desktop, and open it."""
    import anthropic
    try:
        msg = anthropic.Anthropic().messages.create(
            model="claude-haiku-4-5-20251001",
            max_tokens=3000,
            messages=[{
                "role": "user",
                "content": (
                    f"Generate a complete, self-contained HTML page for: {description}. "
                    f"Include inline CSS for clean, modern styling. "
                    f"Return ONLY the raw HTML code, no markdown fences, no explanation."
                ),
            }],
        )
        html = msg.content[0].text.strip()
        if html.startswith("```"):
            lines = html.split("\n")
            html = "\n".join(lines[1:])
        if html.endswith("```"):
            html = html[:-3].rstrip()

        if not filename.endswith(".html"):
            filename += ".html"
        path = _DESKTOP / filename
        path.write_text(html, encoding="utf-8")
        subprocess.run(["open", str(path)], check=False)
        return f"Generated and opened {filename} on your Desktop."
    except Exception as e:
        return f"generate_html failed: {e}"


def write_code(description: str, filename: str, language: str = "python", agent=None) -> str:
    """Generate code from a description, save to Desktop, and open it."""
    import anthropic
    ext = _EXT_MAP.get(language.lower(), f".{language}")
    if not filename.endswith(ext):
        filename += ext
    try:
        msg = anthropic.Anthropic().messages.create(
            model="claude-haiku-4-5-20251001",
            max_tokens=3000,
            messages=[{
                "role": "user",
                "content": (
                    f"Write {language} code for: {description}. "
                    f"Return ONLY the raw code, no markdown fences, no explanation."
                ),
            }],
        )
        code = msg.content[0].text.strip()
        if code.startswith("```"):
            lines = code.split("\n")
            code = "\n".join(lines[1:])
        if code.endswith("```"):
            code = code[:-3].rstrip()

        path = _DESKTOP / filename
        path.write_text(code, encoding="utf-8")
        subprocess.run(["open", str(path)], check=False)
        return f"Generated {filename} and opened it on your Desktop."
    except Exception as e:
        return f"write_code failed: {e}"
