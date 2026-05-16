---
version: 1
interval_minutes: 30
enabled: true
---

# JARVIS Heartbeat

Edit this file to change what JARVIS proactively monitors — no restarts needed.
The heartbeat loop re-reads this file every `interval_minutes` minutes.

Each task has:
- `cron`: standard 5-field cron expression (minute hour dom month dow)
- `prompt`: the message sent to the JARVIS agent when the task fires
- `enabled`: set to false to disable without deleting

---

## Tasks

```yaml
tasks:

  - id: morning_briefing
    enabled: true
    cron: "0 8 * * *"
    prompt: >
      Good morning. Please deliver the morning briefing: check today's
      calendar events, current weather in Stockholm, top news headlines,
      and a market summary. Keep it concise and spoken-friendly.

  - id: evening_summary
    enabled: true
    cron: "0 20 * * *"
    prompt: >
      Evening wrap-up: summarise what happened in the markets today,
      check if there are any unread urgent emails, and remind me of
      tomorrow's first calendar event. Keep it brief.

  - id: stock_check
    enabled: true
    cron: "*/30 9-17 * * 1-5"
    prompt: >
      Quick market pulse: check AAPL, NVDA, BTC-USD and SPY. If any
      ticker has moved more than 2.5% since market open, give me a
      one-sentence spoken alert. If markets are flat, say nothing.

  - id: email_triage
    enabled: false
    cron: "0 */2 * * *"
    prompt: >
      Check Gmail for unread emails that need attention. Categorise
      as URGENT / ACTION / FYI. If nothing urgent, stay silent.

  - id: weekly_review
    enabled: true
    cron: "0 18 * * 5"
    prompt: >
      It's Friday. Give me a quick week-in-review: top market moves,
      any calendar events from this week worth noting, and a one-line
      weekend weather forecast for Stockholm.
```
