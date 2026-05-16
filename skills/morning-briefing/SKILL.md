---
name: morning-briefing
description: Deliver a spoken morning briefing covering calendar, weather, news, and markets
user-invocable: true
---

# Morning Briefing

When the user requests a morning briefing or the heartbeat fires the morning task:

1. Call `show_briefing` to navigate the HUD to the briefing panel
2. Call `get_weather` for Stockholm (or user's location if stored in memory)
3. Call `get_calendar_events` with `days_ahead=1` for today's schedule
4. Call `get_news` for top 4 headlines
5. Call `get_market_summary` for index snapshot

Deliver the result as a single cohesive spoken paragraph — no bullet points,
no headers — as if JARVIS is reading it aloud to the user. Dry British wit
encouraged. Under 90 seconds of spoken content.

Structure (spoken):
  Weather → Calendar → Markets → News → closing remark

## Example invocations
- "Good morning JARVIS"
- "Morning briefing"
- "What's today looking like?"
- Heartbeat task: `morning_briefing`
