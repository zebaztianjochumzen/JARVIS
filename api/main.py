"""FastAPI WebSocket gateway — bridges the browser to the JARVIS agent."""

import os
import sys
import json
import asyncio

from dotenv import load_dotenv
from fastapi import FastAPI, WebSocket, WebSocketDisconnect, UploadFile, File, Form
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse, JSONResponse, Response

# Load .env only if present — in production all secrets come from AWS Secrets Manager
load_dotenv(dotenv_path=os.path.join(os.path.dirname(__file__), '..', '.env'), override=False)
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from jarvis import secrets as _secrets
from jarvis import runtime_settings as _rs

_secrets.load_all(environment=os.environ.get("JARVIS_ENV", "dev"))

from jarvis.agent import Agent  # noqa: E402

# ── Boot autonomous task scheduler ────────────────────────────────────────────
from jarvis import scheduler as _scheduler
_scheduler.start()

# ── Boot MCP client (external tool servers) ───────────────────────────────────
try:
    from jarvis import mcp_client as _mcp_client
    _mcp_client.start()
except Exception as _mcpe:
    print(f"[JARVIS] MCP client skipped: {_mcpe}", flush=True)
    _mcp_client = None  # type: ignore

# ── Boot Telegram bot ─────────────────────────────────────────────────────────
try:
    from jarvis import telegram_bot as _telegram_bot
    _telegram_bot.start(lambda: Agent())
except Exception as _tge:
    print(f"[JARVIS] Telegram bot skipped: {_tge}", flush=True)
    _telegram_bot = None  # type: ignore

# ── Register approval broadcast with WebSocket clients ────────────────────────
try:
    from jarvis import approval as _approval
    # Broadcast callback registered after app starts (see websocket handler below)
except Exception:
    _approval = None  # type: ignore

# ── Boot wake-word background listener ────────────────────────────────────────
try:
    from jarvis.voice import wakeword as _wakeword
    _wakeword.start()
except Exception as _wwe:
    print(f"[JARVIS] Wake-word listener skipped: {_wwe}", flush=True)
    _wakeword = None  # type: ignore

app = FastAPI()

# ── Mount vision server (camera + gesture) on /vision ─────────────────────────
try:
    from vision.server import app as _vision_app
    app.mount("/vision", _vision_app)
    print("[JARVIS] Vision server mounted at /vision", flush=True)
except Exception as _ve:
    print(f"[JARVIS] Vision server not available: {_ve}", flush=True)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)



# ── Calendar endpoint ──────────────────────────────────────────────────────────

@app.get("/api/calendar")
async def get_calendar(days: int = 1):
    import datetime as _dt
    try:
        from jarvis.tools.calendar_tool import _service, _fmt_event
        svc = _service()
        now = _dt.datetime.utcnow()
        end = now + _dt.timedelta(days=max(days, 1))
        result = svc.events().list(
            calendarId='primary',
            timeMin=now.isoformat() + 'Z',
            timeMax=end.isoformat() + 'Z',
            maxResults=30,
            singleEvents=True,
            orderBy='startTime',
        ).execute()
        events = [_fmt_event(e) for e in result.get('items', [])]
        # Remove non-serialisable datetime objects before JSON response
        for ev in events:
            ev.pop('start_dt', None)
        return {'events': events, 'days': days}
    except FileNotFoundError:
        return {'events': [], 'error': 'credentials_missing', 'days': days}
    except Exception as e:
        return {'events': [], 'error': str(e), 'days': days}


# ── System status endpoint ────────────────────────────────────────────────────

@app.get("/api/status")
async def get_system_status():
    """Live health check of every JARVIS subsystem. Safe to poll frequently."""
    result: dict = {}

    # Claude API
    try:
        import anthropic as _ant
        _ant.Anthropic()  # validates key format without making a network call
        result["claude"] = {"ok": True, "model": "claude-sonnet-4-6"}
    except Exception as e:
        result["claude"] = {"ok": False, "error": str(e)[:80]}

    # Telegram bot
    try:
        from jarvis import telegram_bot as _tg
        chat_id = _tg.get_chat_id()
        result["telegram"] = {
            "ok":      _tg._bot is not None,
            "running": _tg._started,
            "chat_id": chat_id,
            "configured": bool(os.environ.get("TELEGRAM_BOT_TOKEN", "").strip()),
        }
    except Exception as e:
        result["telegram"] = {"ok": False, "running": False, "error": str(e)[:80]}

    # MCP servers
    try:
        from jarvis import mcp_client as _mcp
        servers = _mcp.get_server_status()
        result["mcp"] = {
            "ok":         _mcp._started,
            "servers":    servers,
            "tool_count": len(_mcp.get_mcp_tools()),
        }
    except Exception:
        result["mcp"] = {"ok": False, "servers": [], "tool_count": 0}

    # Wake word listener
    try:
        from jarvis.voice import wakeword as _ww
        result["wakeword"] = {"ok": True, "running": _ww._started}
    except Exception:
        result["wakeword"] = {"ok": False, "running": False}

    # Obsidian vault
    try:
        from jarvis.obsidian import vault_status as _vs
        summary = _vs()
        configured = bool(os.environ.get("OBSIDIAN_VAULT_PATH", "").strip())
        result["obsidian"] = {
            "ok":         configured and "error" not in summary.lower(),
            "configured": configured,
            "summary":    summary,
        }
    except Exception as e:
        result["obsidian"] = {"ok": False, "configured": False, "summary": str(e)[:80]}

    # Autonomous scheduler + heartbeat
    try:
        from jarvis import scheduler as _sch
        from jarvis import heartbeat as _hb
        result["scheduler"] = {
            "ok":               True,
            "running":          _sch._started,
            "heartbeat_active": _hb._started,
            "heartbeat_file":   str(_hb.HEARTBEAT_PATH),
        }
    except Exception:
        result["scheduler"] = {"ok": False, "running": False}

    # Memory database
    try:
        import sqlite3
        from pathlib import Path as _Path
        db = _Path.home() / ".jarvis" / "memory.db"
        if db.exists():
            with sqlite3.connect(str(db)) as conn:
                facts = conn.execute("SELECT COUNT(*) FROM facts").fetchone()[0]
                msgs  = conn.execute("SELECT COUNT(*) FROM messages").fetchone()[0]
            result["memory"] = {"ok": True, "facts": facts, "messages": msgs}
        else:
            result["memory"] = {"ok": True, "facts": 0, "messages": 0, "note": "db not initialised yet"}
    except Exception as e:
        result["memory"] = {"ok": False, "error": str(e)[:80]}

    # Whisper STT (check if model is loaded in-process)
    try:
        from jarvis.voice import stt as _stt
        result["whisper"] = {
            "ok":     True,
            "loaded": _stt._model is not None,
            "model":  _rs.get("whisper_model", "base"),
        }
    except Exception:
        result["whisper"] = {"ok": False, "loaded": False, "model": "unknown"}

    return result


# ── Runtime settings endpoints ────────────────────────────────────────────────

@app.get("/api/settings")
async def get_settings():
    return _rs.get_all()


@app.post("/api/settings")
async def update_settings(body: dict):
    updated = _rs.update(body)
    return {"ok": True, "settings": updated}


# ── Memories endpoint ─────────────────────────────────────────────────────────

@app.get("/api/memories")
async def get_memories():
    """Return all stored facts plus Obsidian vault status."""
    from jarvis.memory import Memory
    from jarvis.obsidian import vault_status
    mem   = Memory()
    facts = mem.get_all_facts()
    ctx   = mem.get_context_summary()
    return {
        "facts":          [{"key": k, "value": v} for k, v in facts.items()],
        "context_summary": ctx,
        "fact_count":     len(facts),
        "obsidian":       vault_status(),
    }


# ── System vitals SSE ─────────────────────────────────────────────────────────

@app.get("/api/vitals")
async def vitals_stream():
    """Server-Sent Events stream of live system metrics (1 Hz).

    Payload: { cpu, ram, net_sent_bytes, net_recv_bytes }
    The frontend computes KB/s from successive net_* values.
    """
    try:
        import psutil as _psutil
        _psutil.cpu_percent()  # prime the counter (first call always returns 0)
    except ImportError:
        async def _no_psutil():
            yield 'data: {"error":"psutil not installed"}\n\n'
        return StreamingResponse(_no_psutil(), media_type="text/event-stream")

    async def generate():
        import psutil as _ps
        while True:
            try:
                cpu = _ps.cpu_percent(interval=None)
                mem = _ps.virtual_memory()
                net = _ps.net_io_counters()
                payload = json.dumps({
                    "cpu":           round(cpu, 1),
                    "ram":           round(mem.percent, 1),
                    "net_sent_bytes": net.bytes_sent,
                    "net_recv_bytes": net.bytes_recv,
                })
                yield f"data: {payload}\n\n"
            except Exception:
                pass
            await asyncio.sleep(1)

    return StreamingResponse(
        generate(),
        media_type="text/event-stream",
        headers={
            "Cache-Control":               "no-cache",
            "X-Accel-Buffering":           "no",
            "Access-Control-Allow-Origin": "*",
        },
    )


# ── Approval endpoints ────────────────────────────────────────────────────────

@app.get("/api/approvals")
async def list_approvals():
    """List all pending approval requests."""
    try:
        from jarvis.approval import list_pending
        return {"pending": list_pending()}
    except Exception as exc:
        return {"pending": [], "error": str(exc)}


@app.post("/api/approve")
async def approve_tool(body: dict):
    """Approve or deny a pending tool call.

    Body: { "approval_id": "abc12345", "approved": true }
    """
    approval_id = body.get("approval_id", "").strip()
    approved    = bool(body.get("approved", False))
    if not approval_id:
        return JSONResponse({"error": "approval_id required"}, status_code=400)
    try:
        from jarvis.approval import resolve
        found = resolve(approval_id, approved)
        if not found:
            return JSONResponse({"error": "approval_id not found or already resolved"}, status_code=404)
        return {"ok": True, "approved": approved}
    except Exception as exc:
        return JSONResponse({"error": str(exc)}, status_code=500)


# ── Heartbeat endpoints ───────────────────────────────────────────────────────

@app.get("/api/heartbeat/reload")
async def heartbeat_reload():
    """Force HEARTBEAT.md to be re-parsed without restarting."""
    try:
        from jarvis.heartbeat import reload
        result = reload()
        return {"ok": True, "result": result}
    except Exception as exc:
        return JSONResponse({"error": str(exc)}, status_code=500)


# ── Telegram send endpoint ────────────────────────────────────────────────────

@app.post("/api/telegram/send")
async def telegram_send(body: dict):
    """Send a message to the registered Telegram chat."""
    text = body.get("text", "").strip()
    if not text:
        return JSONResponse({"error": "no text"}, status_code=400)
    try:
        from jarvis import telegram_bot
        result = telegram_bot.send_message(text)
        return {"result": result}
    except Exception as exc:
        return JSONResponse({"error": str(exc)}, status_code=500)


# ── Browser proxy ─────────────────────────────────────────────────────────────

@app.get("/api/browse")
async def browse_proxy(url: str):
    """Proxy a URL, stripping X-Frame-Options so it can render in the HUD iframe."""
    import httpx
    from urllib.parse import urlparse

    parsed   = urlparse(url)
    base_url = f"{parsed.scheme}://{parsed.netloc}"

    try:
        async with httpx.AsyncClient(follow_redirects=True, timeout=12) as client:
            resp = await client.get(url, headers={
                "User-Agent": (
                    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
                    "AppleWebKit/537.36 (KHTML, like Gecko) "
                    "Chrome/120.0.0.0 Safari/537.36"
                )
            })

        content_type = resp.headers.get("content-type", "text/html")

        if "text/html" in content_type:
            html = resp.text
            # Inject <base> so relative URLs resolve correctly
            base_tag = f'<base href="{base_url}/">'
            lower = html.lower()
            if "<head>" in lower:
                idx  = lower.index("<head>") + 6
                html = html[:idx] + base_tag + html[idx:]
            else:
                html = base_tag + html
            body = html.encode("utf-8", errors="replace")
        else:
            body = resp.content

        return Response(
            content=body,
            media_type=content_type,
            headers={
                "X-Frame-Options": "ALLOWALL",
                "Content-Security-Policy": "",
                "Access-Control-Allow-Origin": "*",
            },
        )

    except Exception as exc:
        error_html = f"""<!DOCTYPE html>
<html><head><style>
  body{{background:#070b14;color:#4fc3f7;font-family:'Share Tech Mono',monospace;
       display:flex;flex-direction:column;align-items:center;justify-content:center;height:100vh;gap:16px;margin:0}}
  h2{{letter-spacing:6px;font-size:14px;opacity:.7}}p{{font-size:11px;opacity:.4}}
</style></head><body>
  <h2>COULD NOT LOAD</h2><p>{exc}</p>
</body></html>"""
        return Response(content=error_html.encode(), media_type="text/html")


# ── Stocks endpoint ────────────────────────────────────────────────────────────

WATCHLIST = [
    ("SPY",  "S&P 500"),
    ("QQQ",  "NASDAQ"),
    ("AAPL", "Apple"),
    ("NVDA", "NVIDIA"),
    ("TSLA", "Tesla"),
    ("MSFT", "Microsoft"),
    ("GOOGL","Alphabet"),
    ("AMZN", "Amazon"),
    ("META", "Meta"),
    ("BTC-USD", "Bitcoin"),
]

@app.get("/api/stocks")
async def get_stocks():
    import yfinance as yf

    tickers = [t for t, _ in WATCHLIST]
    names   = {t: n for t, n in WATCHLIST}

    data = yf.download(
        tickers,
        period="2d",
        interval="1d",
        group_by="ticker",
        auto_adjust=True,
        progress=False,
    )

    results = []
    for ticker in tickers:
        try:
            if len(tickers) == 1:
                closes = data["Close"]
            else:
                closes = data[ticker]["Close"]

            closes = closes.dropna()
            if len(closes) < 2:
                continue

            prev  = float(closes.iloc[-2])
            price = float(closes.iloc[-1])
            change     = price - prev
            change_pct = (change / prev) * 100

            results.append({
                "ticker":     ticker,
                "name":       names[ticker],
                "price":      round(price, 2),
                "change":     round(change, 2),
                "change_pct": round(change_pct, 2),
            })
        except Exception:
            continue

    return {"stocks": results}


# ── News endpoint ─────────────────────────────────────────────────────────────

NEWS_FEEDS = [
    ("SVT Nyheter",      "https://www.svt.se/nyheter/rss.xml"),
    ("Aftonbladet",      "https://rss.aftonbladet.se/rss2/small/pages/sections/senastenytt/"),
    ("Dagens industri",  "https://www.di.se/rss"),
]

@app.get("/api/news")
async def get_news():
    import feedparser
    import requests
    import time

    HEADERS = {"User-Agent": "Mozilla/5.0 (compatible; JARVIS/1.0)"}

    articles = []
    for source, url in NEWS_FEEDS:
        try:
            resp = requests.get(url, headers=HEADERS, timeout=8, verify=False)
            feed = feedparser.parse(resp.content)
            for entry in feed.entries[:6]:
                pub = entry.get("published_parsed") or entry.get("updated_parsed")
                articles.append({
                    "source":    source,
                    "title":     entry.get("title", ""),
                    "summary":   entry.get("summary", ""),
                    "link":      entry.get("link", ""),
                    "published": time.mktime(pub) if pub else 0,
                    "image":     (
                        entry.get("media_thumbnail", [{}])[0].get("url") or
                        entry.get("media_content",   [{}])[0].get("url") or
                        None
                    ),
                })
        except Exception:
            continue

    articles.sort(key=lambda a: a["published"], reverse=True)
    return {"articles": articles[:30]}


# ── Briefing endpoint ─────────────────────────────────────────────────────────

@app.get("/api/briefing")
async def get_briefing():
    import requests as req
    HEADERS = {"User-Agent": "Mozilla/5.0 (compatible; JARVIS/1.0)"}
    weather = {}
    try:
        r = req.get("https://wttr.in/Stockholm?format=j1", headers=HEADERS, timeout=6, verify=False)
        w = r.json()
        cc = w["current_condition"][0]
        weather = {
            "city":        "Stockholm",
            "temp_c":      cc["temp_C"],
            "feels_like":  cc["FeelsLikeC"],
            "humidity":    cc["humidity"],
            "wind_kmh":    cc["windspeedKmph"],
            "description": cc["weatherDesc"][0]["value"],
        }
    except Exception:
        pass
    return {"weather": weather}


# ── Spotify endpoints ─────────────────────────────────────────────────────────

@app.get("/api/spotify/now-playing")
async def spotify_now_playing():
    try:
        from jarvis.tools.spotify_client import now_playing
        track = now_playing()
        return {"track": track}
    except Exception as e:
        return {"track": None, "error": str(e)}


@app.post("/api/spotify/control")
async def spotify_control(body: dict):
    action = body.get("action", "")
    query  = body.get("query", "")
    try:
        from jarvis.tools.spotify_client import control, search_and_play
        if action == "search" and query:
            result = search_and_play(query)
        else:
            result = control(action)
        return {"result": result}
    except Exception as e:
        return {"result": None, "error": str(e)}


# ── TTS endpoint ──────────────────────────────────────────────────────────────

TTS_VOICE = "en-US-GuyNeural"  # free Microsoft neural voice via edge-tts

@app.post("/api/tts")
async def text_to_speech(body: dict):
    import edge_tts
    import io

    text = body.get("text", "").strip()
    if not text:
        return JSONResponse({"error": "no text"}, status_code=400)

    voice = body.get("voice", TTS_VOICE)

    async def _generate():
        communicate = edge_tts.Communicate(text, voice)
        async for chunk in communicate.stream():
            if chunk["type"] == "audio":
                yield chunk["data"]

    return StreamingResponse(
        _generate(),
        media_type="audio/mpeg",
        headers={"Cache-Control": "no-cache"},
    )


# ── Whisper transcription endpoint ────────────────────────────────────────────

@app.post("/api/transcribe")
async def transcribe_audio(
    audio: UploadFile = File(...),
    format: str = Form(default="webm"),
):
    """Accept an audio blob from the browser and return a Whisper transcript.

    The frontend sends the raw MediaRecorder output (webm/opus by default).
    Returns {"transcript": "..."} or {"error": "..."}.
    """
    try:
        from jarvis.voice.stt import transcribe_bytes
        audio_bytes = await audio.read()
        if not audio_bytes:
            return JSONResponse({"error": "empty audio"}, status_code=400)

        transcript = await asyncio.get_event_loop().run_in_executor(
            None, lambda: transcribe_bytes(audio_bytes, audio_format=format)
        )
        return {"transcript": transcript}
    except ImportError:
        return JSONResponse(
            {"error": "faster-whisper not installed. Run: pip install faster-whisper"},
            status_code=503,
        )
    except Exception as exc:
        return JSONResponse({"error": str(exc)}, status_code=500)


# ── Wake-word WebSocket ────────────────────────────────────────────────────────

@app.websocket("/ws/wakeword")
async def wakeword_ws(websocket: WebSocket):
    """Push 'wake_word_detected' events to the browser when the backend hears 'Hey JARVIS'."""
    await websocket.accept()

    import queue as _queue
    ww_queue: _queue.Queue = _queue.Queue()

    if _wakeword is not None:
        _wakeword.add_listener(ww_queue)

    try:
        while True:
            # Poll the queue every 100 ms; send keep-alive ping every 30 s
            await asyncio.sleep(0.1)
            try:
                event = ww_queue.get_nowait()
                await websocket.send_text(json.dumps(event))
            except _queue.Empty:
                pass
    except (WebSocketDisconnect, Exception):
        pass
    finally:
        if _wakeword is not None:
            _wakeword.remove_listener(ww_queue)


# ── WebSocket chat ─────────────────────────────────────────────────────────────

@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    await websocket.accept()
    agent    = Agent()
    loop     = asyncio.get_event_loop()
    cur_task: asyncio.Task | None = None

    async def run_agent(user_message: str):
        def on_token(text: str):
            if agent._cancelled:
                return
            asyncio.run_coroutine_threadsafe(
                websocket.send_text(json.dumps({"type": "token", "text": text})), loop,
            )

        def on_action(action: dict):
            if agent._cancelled:
                return
            asyncio.run_coroutine_threadsafe(
                websocket.send_text(json.dumps(action)), loop,
            )

        try:
            await loop.run_in_executor(
                None, lambda: agent.ask(user_message, stream_callback=on_token, action_callback=on_action)
            )
            if not agent._cancelled:
                for action in agent.pending_actions:
                    await websocket.send_text(json.dumps(action))
                await websocket.send_text(json.dumps({"type": "done"}))
        except asyncio.CancelledError:
            pass
        except Exception as exc:
            await websocket.send_text(json.dumps({"type": "error", "message": str(exc)}))
        finally:
            agent.pending_actions.clear()

    import queue as _queue
    sched_q: _queue.Queue = _queue.Queue()
    _scheduler.add_client(sched_q)

    # Register this WebSocket connection as an approval broadcast target
    approval_q: _queue.Queue = _queue.Queue()
    if _approval is not None:
        def _approval_broadcast(payload: dict):
            try:
                approval_q.put_nowait(payload)
            except Exception:
                pass
        _approval.register_broadcast(_approval_broadcast)

    async def _watch_scheduler():
        """Dispatch scheduled tasks and forward approval requests to the HUD."""
        while True:
            await asyncio.sleep(5)
            # Forward approval requests to the browser
            try:
                approval_event = approval_q.get_nowait()
                await websocket.send_text(json.dumps(approval_event))
            except _queue.Empty:
                pass
            except Exception:
                pass
            # Dispatch heartbeat / scheduler tasks to the agent
            try:
                event = sched_q.get_nowait()
                task_msg = event.get("message", "")
                if not task_msg:
                    continue
                nonlocal cur_task
                if cur_task and not cur_task.done():
                    agent.cancel(); cur_task.cancel()
                cur_task = asyncio.create_task(run_agent(task_msg))
            except _queue.Empty:
                pass

    asyncio.create_task(_watch_scheduler())

    try:
        while True:
            raw  = await websocket.receive_text()
            data = json.loads(raw)

            # ── Interrupt signal from frontend ──────────────────────────────
            if data.get("type") == "interrupt":
                agent.cancel()
                if cur_task and not cur_task.done():
                    cur_task.cancel()
                continue

            user_message = data.get("message", "").strip()
            if not user_message:
                continue

            # Cancel any in-flight response before starting a new one
            if cur_task and not cur_task.done():
                agent.cancel()
                cur_task.cancel()
                try:
                    await cur_task
                except (asyncio.CancelledError, Exception):
                    pass

            cur_task = asyncio.create_task(run_agent(user_message))

    except WebSocketDisconnect:
        pass
    finally:
        _scheduler.remove_client(sched_q)
