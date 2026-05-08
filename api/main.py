"""FastAPI WebSocket gateway — bridges the browser to the JARVIS agent."""

import os
import sys
import json
import asyncio

from dotenv import load_dotenv
from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware

load_dotenv(dotenv_path=os.path.join(os.path.dirname(__file__), '..', '.env'))
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from jarvis.secrets import get_secret

api_key = get_secret("ANTHROPIC_API_KEY")
os.environ["ANTHROPIC_API_KEY"] = api_key

from jarvis.agent import Agent  # noqa: E402

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)


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


# ── WebSocket chat ─────────────────────────────────────────────────────────────

@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    await websocket.accept()
    agent = Agent()

    try:
        while True:
            raw = await websocket.receive_text()
            data = json.loads(raw)
            user_message = data.get("message", "").strip()
            if not user_message:
                continue

            loop = asyncio.get_event_loop()

            def on_token(text: str):
                asyncio.run_coroutine_threadsafe(
                    websocket.send_text(json.dumps({"type": "token", "text": text})),
                    loop,
                )

            try:
                await loop.run_in_executor(
                    None, lambda: agent.ask(user_message, stream_callback=on_token)
                )
                await websocket.send_text(json.dumps({"type": "done"}))
            except Exception as exc:
                await websocket.send_text(json.dumps({"type": "error", "message": str(exc)}))

    except WebSocketDisconnect:
        pass
