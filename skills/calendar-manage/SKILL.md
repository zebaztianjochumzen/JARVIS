---
name: calendar-manage
description: Full Google Calendar CRUD — view, create, and delete events with spoken confirmation
user-invocable: true
metadata:
  openclaw:
    requires:
      - env: GOOGLE_CREDENTIALS_PATH
---

# Calendar Management

## Viewing events
When asked about schedule, meetings, or what's on:
1. Call `show_calendar` to navigate HUD to calendar panel and fetch today's events
2. Read events aloud in chronological order: "You have {N} events today…"
3. For multi-day queries, call `get_calendar_events` with appropriate `days_ahead`

## Creating events
When asked to add, schedule, or create a meeting:
1. Extract: title, date/time, duration (default 1 hour), location (optional), description (optional)
2. If any required field is missing, ask once — do not guess
3. Call `create_calendar_event` with ISO 8601 times
4. Confirm: "Done, I've added {title} on {date} at {time}."

**Never create an event without all required fields confirmed by the user.**

## Deleting events
When asked to remove or cancel a meeting:
1. Call `get_calendar_events` to find the event and retrieve its ID
2. Confirm with the user: "Are you sure you want to remove {title}?"
3. Only after confirmation: call `delete_calendar_event`
4. Confirm deletion.

This tool requires approval before `delete_calendar_event` is executed.

## Example invocations
- "What's on my calendar today?"
- "Schedule a meeting with Marcus at 14:00 tomorrow"
- "Cancel my 3pm call"
- "What do I have next week?"
