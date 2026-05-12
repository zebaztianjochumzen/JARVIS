"""Autonomous background task scheduler for JARVIS.

Daemon threads push task-trigger events to registered queues so the
WebSocket handler can dispatch them to the agent — same mechanism as
the morning briefing that previously lived in api/main.py.

Tasks:
  morning_briefing  — spoken brief at BRIEFING_HOUR (default 08:00)
  price_alert       — notify when a watched stock moves > PRICE_ALERT_PCT %
  email_digest      — optional hourly unread-email nudge

Usage (from api/main.py):
    from jarvis import scheduler
    scheduler.start()
    scheduler.add_client(queue)      # per WebSocket connection
    scheduler.remove_client(queue)   # on disconnect
"""

import os
import queue
import threading
import time
from datetime import datetime
from typing import List

_clients: List[queue.Queue] = []
_lock    = threading.Lock()
_started = False


# ── Client registry ───────────────────────────────────────────────────────────

def add_client(q: queue.Queue) -> None:
    with _lock:
        if q not in _clients:
            _clients.append(q)


def remove_client(q: queue.Queue) -> None:
    with _lock:
        if q in _clients:
            _clients.remove(q)


def _broadcast(payload: dict) -> None:
    with _lock:
        targets = list(_clients)
    for q in targets:
        try:
            q.put_nowait(payload)
        except Exception:
            pass


# ── Boot ──────────────────────────────────────────────────────────────────────

def start() -> None:
    """Start all background task threads (idempotent)."""
    global _started
    if _started:
        return
    _started = True

    threading.Thread(target=_morning_brief_loop, daemon=True, name="sched-brief").start()
    threading.Thread(target=_stock_alert_loop,   daemon=True, name="sched-stocks").start()

    email_digest = os.environ.get("EMAIL_DIGEST_ENABLED", "0").strip().lower()
    if email_digest in ("1", "true", "yes"):
        threading.Thread(target=_email_digest_loop, daemon=True, name="sched-email").start()

    print("[Scheduler] Background tasks started", flush=True)


# ── Task: morning briefing ────────────────────────────────────────────────────

def _morning_brief_loop() -> None:
    HOUR = int(os.environ.get("BRIEFING_HOUR", "8"))
    fired_today = False

    while True:
        now = datetime.now()
        if now.hour == HOUR and now.minute < 5 and not fired_today:
            fired_today = True
            _broadcast({
                "type":    "scheduled_task",
                "task":    "morning_briefing",
                "message": (
                    "Good morning. Please deliver the morning briefing: "
                    "check today's calendar, current weather, top news headlines, "
                    "and market summary. Keep it concise and spoken-friendly."
                ),
            })
            print(f"[Scheduler] Morning briefing fired at {now.strftime('%H:%M')}", flush=True)

        if now.hour != HOUR:
            fired_today = False

        time.sleep(30)


# ── Task: stock price alerts ──────────────────────────────────────────────────

_ALERT_TICKERS   = [t.strip() for t in os.environ.get("ALERT_TICKERS", "AAPL,NVDA,BTC-USD").split(",") if t.strip()]
_ALERT_PCT       = float(os.environ.get("PRICE_ALERT_PCT", "2.5"))
_last_prices: dict[str, float] = {}


def _stock_alert_loop() -> None:
    time.sleep(60)  # give the server a moment to settle
    while True:
        try:
            import yfinance as yf
            tickers = _ALERT_TICKERS
            if not tickers:
                time.sleep(300)
                continue

            data = yf.download(
                tickers if len(tickers) > 1 else tickers[0],
                period="1d", interval="5m",
                group_by="ticker", auto_adjust=True, progress=False,
            )

            for ticker in tickers:
                try:
                    closes = (
                        data["Close"]
                        if len(tickers) == 1
                        else data[ticker]["Close"]
                    )
                    closes = closes.dropna()
                    if closes.empty:
                        continue

                    price = float(closes.iloc[-1])
                    prev  = _last_prices.get(ticker)

                    if prev is not None and prev > 0:
                        pct = (price - prev) / prev * 100
                        if abs(pct) >= _ALERT_PCT:
                            direction = "up" if pct > 0 else "down"
                            _broadcast({
                                "type":    "scheduled_task",
                                "task":    "price_alert",
                                "message": (
                                    f"{ticker} has moved {direction} {abs(pct):.1f}% "
                                    f"to ${price:.2f}. "
                                    "Give me a brief one-sentence spoken alert about this."
                                ),
                            })
                            print(f"[Scheduler] Price alert: {ticker} {direction} {abs(pct):.1f}%", flush=True)

                    _last_prices[ticker] = price

                except Exception:
                    continue

        except Exception:
            pass

        time.sleep(300)  # check every 5 minutes


# ── Task: email digest (optional) ─────────────────────────────────────────────

def _email_digest_loop() -> None:
    time.sleep(120)
    CHECK_INTERVAL = int(os.environ.get("EMAIL_DIGEST_INTERVAL_MIN", "60")) * 60

    while True:
        time.sleep(CHECK_INTERVAL)
        _broadcast({
            "type":    "scheduled_task",
            "task":    "email_digest",
            "message": (
                "Check my Gmail inbox for any unread emails that need attention. "
                "If there are important or urgent emails, give me a brief spoken summary. "
                "If the inbox is clear, say nothing."
            ),
        })
        print("[Scheduler] Email digest nudge sent", flush=True)
