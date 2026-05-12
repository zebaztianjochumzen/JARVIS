"""Information tools — web search, news, weather, stocks."""

import requests as _req

_HEADERS = {"User-Agent": "Mozilla/5.0 (compatible; JARVIS/1.0)"}


def web_search(query: str, num_results: int = 5, agent=None) -> str:
    try:
        from duckduckgo_search import DDGS
        results = []
        with DDGS() as ddgs:
            for r in ddgs.text(query, max_results=num_results):
                results.append(f"• {r['title']}\n  {r['href']}\n  {r['body']}")
        return "\n\n".join(results) if results else "No results found."
    except ImportError:
        return "web_search requires: pip install duckduckgo-search"
    except Exception as e:
        return f"Search failed: {e}"


def get_news(topic: str = "", num_articles: int = 6, agent=None) -> str:
    import feedparser
    FEEDS = [
        ("SVT Nyheter",     "https://www.svt.se/nyheter/rss.xml"),
        ("Aftonbladet",     "https://rss.aftonbladet.se/rss2/small/pages/sections/senastenytt/"),
        ("Dagens industri", "https://www.di.se/rss"),
    ]
    articles = []
    for source, url in FEEDS:
        try:
            resp = _req.get(url, headers=_HEADERS, timeout=8, verify=False)
            feed = feedparser.parse(resp.content)
            for entry in feed.entries[:8]:
                title   = entry.get("title", "")
                summary = entry.get("summary", "")
                if topic and topic.lower() not in (title + summary).lower():
                    continue
                articles.append(f"[{source}] {title}")
        except Exception:
            continue
    if not articles:
        return f"No news found{' for: ' + topic if topic else ''}."
    return "\n".join(articles[:num_articles])


def get_weather(city: str = "Stockholm", agent=None) -> str:
    try:
        r = _req.get(f"https://wttr.in/{city}?format=j1", headers=_HEADERS, timeout=6, verify=False)
        w = r.json()
        cc = w["current_condition"][0]
        forecast = []
        for day in w["weather"][:5]:
            desc  = day["hourly"][4]["weatherDesc"][0]["value"]
            hi, lo = day["maxtempC"], day["mintempC"]
            forecast.append(f"  {day['date']}: {desc}, {lo}–{hi}°C")
        return (
            f"Weather in {city}:\n"
            f"  {cc['temp_C']}°C (feels {cc['FeelsLikeC']}°C)  "
            f"{cc['weatherDesc'][0]['value']}\n"
            f"  Humidity {cc['humidity']}%  Wind {cc['windspeedKmph']} km/h\n\n"
            f"5-day forecast:\n" + "\n".join(forecast)
        )
    except Exception as e:
        return f"Weather fetch failed for {city}: {e}"


def get_stock_price(ticker: str, agent=None) -> str:
    try:
        import yfinance as yf
        info  = yf.Ticker(ticker.upper()).fast_info
        price = info.last_price
        prev  = info.previous_close
        pct   = (price - prev) / prev * 100
        arrow = "▲" if pct >= 0 else "▼"
        return f"{ticker.upper()}: ${price:.2f}  {arrow} {pct:+.2f}%"
    except Exception as e:
        return f"Could not fetch {ticker}: {e}"


def get_market_summary(agent=None) -> str:
    try:
        import yfinance as yf
        indices = [("SPY","S&P 500"), ("QQQ","NASDAQ"), ("DIA","Dow Jones"), ("^VIX","VIX")]
        lines   = []
        for sym, name in indices:
            try:
                info  = yf.Ticker(sym).fast_info
                price = info.last_price
                pct   = (price - info.previous_close) / info.previous_close * 100
                arrow = "▲" if pct >= 0 else "▼"
                lines.append(f"  {name} ({sym}): ${price:.2f}  {arrow} {pct:+.2f}%")
            except Exception:
                continue
        return "Market summary:\n" + "\n".join(lines)
    except Exception as e:
        return f"Market summary failed: {e}"
