"""FastAPI WebSocket gateway — bridges the browser to the JARVIS agent."""

import os
import sys
import json
import asyncio

from dotenv import load_dotenv
from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse, JSONResponse, Response

load_dotenv(dotenv_path=os.path.join(os.path.dirname(__file__), '..', '.env'))
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from jarvis.secrets import get_secret

api_key = get_secret("ANTHROPIC_API_KEY")
os.environ["ANTHROPIC_API_KEY"] = api_key

from jarvis.agent import Agent  # noqa: E402

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


# ── Morning briefing scheduler ─────────────────────────────────────────────────

_briefing_clients: list = []

def _morning_briefing_loop():
    """Background thread: fires a morning briefing at a configurable hour."""
    import time as _time
    BRIEFING_HOUR = int(os.environ.get("BRIEFING_HOUR", "8"))

    fired_today = False
    while True:
        now = _time.localtime()
        if now.tm_hour == BRIEFING_HOUR and now.tm_min == 0 and not fired_today:
            fired_today = True
            payload = json.dumps({"type": "morning_briefing"})
            for q in list(_briefing_clients):
                try:
                    q.put_nowait(payload)
                except Exception:
                    pass
        if now.tm_hour != BRIEFING_HOUR:
            fired_today = False
        _time.sleep(30)

import threading as _threading
_threading.Thread(target=_morning_briefing_loop, daemon=True).start()


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
    briefing_q: _queue.Queue = _queue.Queue()
    _briefing_clients.append(briefing_q)

    async def _watch_briefing():
        """Push morning briefing trigger to agent when the scheduler fires."""
        while True:
            await asyncio.sleep(15)
            try:
                briefing_q.get_nowait()
                briefing_msg = (
                    "Good morning. Please give me the morning briefing: "
                    "check today's calendar, get the weather, and pull the top news headlines. "
                    "Keep it concise and spoken-friendly."
                )
                nonlocal cur_task
                if cur_task and not cur_task.done():
                    agent.cancel(); cur_task.cancel()
                cur_task = asyncio.create_task(run_agent(briefing_msg))
            except _queue.Empty:
                pass

    asyncio.create_task(_watch_briefing())

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
        if briefing_q in _briefing_clients:
            _briefing_clients.remove(briefing_q)
