"""Telegram bot — gives JARVIS a Telegram channel for reach and proactive messaging.

The bot runs in a daemon thread so the FastAPI server stays unblocked.
Each Telegram message creates a full agent response (same Claude model,
same memory, same tools as the HUD). The first chat_id that contacts the
bot is stored so JARVIS can also send proactive messages (price alerts,
briefings, etc.) via send_message().

Setup:
  1. Talk to @BotFather on Telegram → /newbot → copy the token
  2. Set TELEGRAM_BOT_TOKEN=<token> in .env
  3. Send /start to your new bot to register your chat_id

The proactive send_message() tool lets Claude push messages to Telegram:
  "Send a price alert to Telegram."
"""

import os
import threading
from typing import Optional

_bot           = None
_chat_id: Optional[int] = None
_started       = False
_agent_factory = None   # callable → Agent (to avoid circular import at module load)


# ── Public API ────────────────────────────────────────────────────────────────

def start(agent_factory) -> None:
    """Start the Telegram polling loop in a daemon thread.

    agent_factory is a zero-arg callable that returns a new Agent instance.
    """
    global _started, _agent_factory
    token = os.environ.get("TELEGRAM_BOT_TOKEN", "").strip()
    if not token or _started:
        if not token:
            print("[Telegram] TELEGRAM_BOT_TOKEN not set — bot disabled.", flush=True)
        return

    _started       = True
    _agent_factory = agent_factory

    t = threading.Thread(target=_run, args=(token,), daemon=True, name="telegram-bot")
    t.start()
    print("[Telegram] Bot thread started.", flush=True)


def send_message(text: str) -> str:
    """Send a proactive message to the stored Telegram chat. Used as a JARVIS tool."""
    if _bot is None:
        return "Telegram bot is not running."
    if _chat_id is None:
        return "No Telegram chat registered yet. Send /start to the bot first."
    try:
        _bot.send_message(_chat_id, text)
        return f"Telegram message sent to chat {_chat_id}."
    except Exception as exc:
        return f"Telegram send failed: {exc}"


def get_chat_id() -> Optional[int]:
    return _chat_id


# ── Internal ──────────────────────────────────────────────────────────────────

def _is_owner(user_id: int) -> bool:
    """Return True only if this user_id matches the authorised owner.

    Priority:
      1. TELEGRAM_OWNER_ID env var — explicit numeric ID (most secure)
      2. The stored _chat_id from the first /start command (legacy fallback)
    """
    owner_env = os.environ.get("TELEGRAM_OWNER_ID", "").strip()
    if owner_env:
        try:
            return int(owner_env) == user_id
        except ValueError:
            pass
    # Fallback: accept whoever sent /start first (existing behaviour)
    return _chat_id is None or user_id == _chat_id


def _run(token: str) -> None:
    global _bot
    try:
        import telebot
    except ImportError:
        print("[Telegram] pyTelegramBotAPI not installed — bot disabled.", flush=True)
        return

    bot   = telebot.TeleBot(token, threaded=False)
    _bot  = bot
    agent = _agent_factory()

    @bot.message_handler(commands=["start", "hello"])
    def handle_start(message):
        global _chat_id
        if not _is_owner(message.from_user.id):
            bot.reply_to(message, "Access denied.")
            print(f"[Telegram] Rejected /start from user {message.from_user.id}", flush=True)
            return
        _chat_id = message.chat.id
        _store_chat_id(_chat_id)
        bot.reply_to(message, "JARVIS online. How can I assist you?")

    @bot.message_handler(func=lambda m: True, content_types=["text"])
    def handle_text(message):
        global _chat_id
        if not _is_owner(message.from_user.id):
            bot.reply_to(message, "Access denied.")
            print(f"[Telegram] Rejected message from user {message.from_user.id}", flush=True)
            return

        if _chat_id is None:
            _chat_id = message.chat.id
            _store_chat_id(_chat_id)

        bot.send_chat_action(message.chat.id, "typing")
        try:
            response = agent.ask(message.text or "")
            # Telegram has a 4096-char message limit
            for i in range(0, len(response), 4096):
                bot.reply_to(message, response[i:i + 4096])
        except Exception as exc:
            bot.reply_to(message, f"Error: {exc}")

    # Drop any active long-poll session from a previous (possibly force-killed) run.
    try:
        bot.get_updates(offset=-1, timeout=1, long_polling_timeout=1)
    except Exception:
        pass

    print("[Telegram] Polling for messages…", flush=True)
    try:
        bot.infinity_polling(timeout=20, long_polling_timeout=20)
    except Exception as exc:
        print(f"[Telegram] Polling error: {exc}", flush=True)


def _store_chat_id(chat_id: int) -> None:
    """Persist the chat_id to a small file so it survives restarts."""
    try:
        from pathlib import Path
        p = Path.home() / ".jarvis" / "telegram_chat_id"
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_text(str(chat_id))
    except Exception:
        pass


def _load_chat_id() -> Optional[int]:
    try:
        from pathlib import Path
        p = Path.home() / ".jarvis" / "telegram_chat_id"
        if p.exists():
            return int(p.read_text().strip())
    except Exception:
        pass
    return None


# Restore saved chat_id on module import so proactive sends work after restarts
_chat_id = _load_chat_id()
