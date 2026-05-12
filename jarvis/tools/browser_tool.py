"""Playwright browser automation tools — gives JARVIS full computer-use web control.

A single Playwright Chromium instance is shared across all tool calls (lazy-started
on first use). A threading lock ensures operations are serialised.

Tools exposed to Claude:
  browser_navigate      → go to a URL, return page title + visible text excerpt
  browser_extract_text  → dump all readable text from the current page
  browser_click         → click an element by visible text or CSS selector
  browser_fill          → type into an input/textarea
  browser_screenshot    → screenshot the current page, describe it with Claude Vision
  browser_execute_js    → run arbitrary JavaScript and return the result
"""

import base64
import os
import threading
from typing import Optional

# ── Singleton browser state ───────────────────────────────────────────────────
_lock       = threading.Lock()
_playwright = None
_browser    = None
_page       = None


def _get_page():
    """Return the shared page, starting the browser if needed."""
    global _playwright, _browser, _page

    if _page is not None and not _page.is_closed():
        return _page

    from playwright.sync_api import sync_playwright

    if _playwright is None:
        _playwright = sync_playwright().start()

    headless = os.environ.get("BROWSER_HEADLESS", "1") not in ("0", "false", "no")
    _browser  = _playwright.chromium.launch(headless=headless)
    ctx       = _browser.new_context(
        viewport={"width": 1280, "height": 800},
        user_agent=(
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
            "AppleWebKit/537.36 (KHTML, like Gecko) "
            "Chrome/120.0.0.0 Safari/537.36"
        ),
    )
    _page = ctx.new_page()
    return _page


def _truncate(text: str, limit: int = 3000) -> str:
    if len(text) <= limit:
        return text
    return text[:limit] + f"\n…[{len(text) - limit} chars truncated]"


# ── Tools ─────────────────────────────────────────────────────────────────────

def browser_navigate(url: str, agent=None) -> str:
    """Navigate to a URL and return the page title plus a text excerpt."""
    if not url.startswith(("http://", "https://")):
        url = "https://" + url

    with _lock:
        page = _get_page()
        try:
            page.goto(url, wait_until="domcontentloaded", timeout=20_000)
            title = page.title()
            # Grab visible body text (strip scripts/styles via innerText)
            text = page.evaluate("() => document.body?.innerText || ''")
            return f"Navigated to: {title}\nURL: {page.url}\n\n{_truncate(text, 2000)}"
        except Exception as exc:
            return f"Navigation failed: {exc}"


def browser_extract_text(agent=None) -> str:
    """Extract all visible text from the currently loaded page."""
    with _lock:
        page = _get_page()
        try:
            text = page.evaluate("() => document.body?.innerText || ''")
            return _truncate(text, 4000) or "(page has no visible text)"
        except Exception as exc:
            return f"Text extraction failed: {exc}"


def browser_click(target: str, agent=None) -> str:
    """Click an element by visible text content or CSS selector.

    Try visible text first; fall back to treating target as a CSS selector.
    """
    with _lock:
        page = _get_page()
        try:
            # Try exact text match first
            locator = page.get_by_text(target, exact=True)
            if locator.count() > 0:
                locator.first.click(timeout=5_000)
                return f"Clicked element with text: '{target}'"
        except Exception:
            pass

        try:
            # Fall back to CSS/ARIA selector
            page.click(target, timeout=8_000)
            return f"Clicked selector: '{target}'"
        except Exception as exc:
            return f"Click failed — could not find '{target}': {exc}"


def browser_fill(selector: str, value: str, agent=None) -> str:
    """Fill an input, textarea, or contenteditable element."""
    with _lock:
        page = _get_page()
        try:
            page.fill(selector, value, timeout=8_000)
            return f"Filled '{selector}' with: {value[:80]}"
        except Exception as exc:
            return f"Fill failed for '{selector}': {exc}"


def browser_screenshot(agent=None) -> str:
    """Screenshot the current page and describe it using Claude Vision."""
    with _lock:
        page = _get_page()
        try:
            img_bytes = page.screenshot(full_page=False)
        except Exception as exc:
            return f"Screenshot failed: {exc}"

    # Describe with Claude Vision
    try:
        import anthropic
        client   = anthropic.Anthropic()
        b64_img  = base64.standard_b64encode(img_bytes).decode()
        response = client.messages.create(
            model="claude-sonnet-4-6",
            max_tokens=512,
            messages=[{
                "role": "user",
                "content": [
                    {
                        "type":   "image",
                        "source": {"type": "base64", "media_type": "image/png", "data": b64_img},
                    },
                    {"type": "text", "text": "Describe the key content and layout of this web page screenshot concisely."},
                ],
            }],
        )
        return response.content[0].text
    except Exception as exc:
        return f"Screenshot taken but vision analysis failed: {exc}"


def browser_execute_js(code: str, agent=None) -> str:
    """Execute JavaScript in the current page and return the result."""
    with _lock:
        page = _get_page()
        try:
            result = page.evaluate(code)
            return str(result)[:2000] if result is not None else "(returned null)"
        except Exception as exc:
            return f"JavaScript error: {exc}"
