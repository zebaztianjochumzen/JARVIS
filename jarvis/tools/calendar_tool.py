"""Google Calendar tools — read, create, and show calendar events."""

import datetime
from pathlib import Path

SCOPES      = ['https://www.googleapis.com/auth/calendar']
REPO_ROOT   = Path(__file__).parent.parent.parent
CREDS_PATH  = REPO_ROOT / 'credentials.json'
TOKEN_PATH  = REPO_ROOT / 'token.json'
TZ          = 'Europe/Stockholm'


def _service():
    from google.oauth2.credentials import Credentials
    from google_auth_oauthlib.flow import InstalledAppFlow
    from google.auth.transport.requests import Request
    from googleapiclient.discovery import build

    creds = None
    if TOKEN_PATH.exists():
        creds = Credentials.from_authorized_user_file(str(TOKEN_PATH), SCOPES)

    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            if not CREDS_PATH.exists():
                raise FileNotFoundError(
                    "Google Calendar not configured. "
                    "Add credentials.json to the JARVIS root directory. "
                    "Download it from Google Cloud Console → APIs & Services → Credentials."
                )
            flow = InstalledAppFlow.from_client_secrets_file(str(CREDS_PATH), SCOPES)
            creds = flow.run_local_server(port=0)
        TOKEN_PATH.write_text(creds.to_json())

    return build('calendar', 'v3', credentials=creds)


def _fmt_event(e: dict) -> dict:
    """Normalise a Google Calendar event into a simple dict."""
    start_raw = e['start'].get('dateTime', e['start'].get('date', ''))
    end_raw   = e['end'].get('dateTime',   e['end'].get('date',   ''))
    all_day   = 'T' not in start_raw

    def _parse(raw):
        if not raw:
            return None
        try:
            return datetime.datetime.fromisoformat(raw.replace('Z', '+00:00'))
        except Exception:
            return None

    start_dt = _parse(start_raw)
    end_dt   = _parse(end_raw)

    return {
        'id':          e.get('id', ''),
        'title':       e.get('summary', 'Untitled'),
        'start':       start_raw,
        'end':         end_raw,
        'start_dt':    start_dt,
        'all_day':     all_day,
        'location':    e.get('location', ''),
        'description': e.get('description', ''),
        'meet_url':    e.get('hangoutLink', ''),
        'color':       e.get('colorId', ''),
    }


def get_calendar_events(days_ahead: int = 1, max_results: int = 15, agent=None) -> str:
    """Fetch upcoming events from Google Calendar and return a spoken summary."""
    try:
        svc = _service()
        now = datetime.datetime.utcnow()
        end = now + datetime.timedelta(days=max(days_ahead, 1))

        result = svc.events().list(
            calendarId='primary',
            timeMin=now.isoformat() + 'Z',
            timeMax=end.isoformat() + 'Z',
            maxResults=max_results,
            singleEvents=True,
            orderBy='startTime',
        ).execute()

        events = [_fmt_event(e) for e in result.get('items', [])]
        if not events:
            period = "today" if days_ahead <= 1 else f"the next {days_ahead} days"
            return f"Nothing on the calendar for {period}."

        lines = []
        for ev in events:
            if ev['all_day']:
                lines.append(f"All day: {ev['title']}")
            else:
                dt = ev['start_dt']
                time_str = dt.strftime('%H:%M') if dt else ev['start']
                lines.append(f"{time_str} — {ev['title']}"
                             + (f" @ {ev['location']}" if ev['location'] else ''))
        return "\n".join(lines)

    except FileNotFoundError as e:
        return str(e)
    except Exception as e:
        return f"Calendar error: {e}"


def create_calendar_event(
    title: str,
    start_time: str,
    end_time: str,
    description: str = '',
    location: str = '',
    agent=None,
) -> str:
    """Create a new event in Google Calendar. Times must be ISO 8601."""
    try:
        svc = _service()
        body = {
            'summary':     title,
            'description': description,
            'location':    location,
            'start': {'dateTime': start_time, 'timeZone': TZ},
            'end':   {'dateTime': end_time,   'timeZone': TZ},
        }
        ev = svc.events().insert(calendarId='primary', body=body).execute()
        dt = datetime.datetime.fromisoformat(start_time.replace('Z', '+00:00'))
        return f"Event created: '{title}' on {dt.strftime('%A %d %b at %H:%M')}."
    except Exception as e:
        return f"Failed to create event: {e}"


def delete_calendar_event(event_id: str, agent=None) -> str:
    """Delete a calendar event by its ID."""
    try:
        _service().events().delete(calendarId='primary', eventId=event_id).execute()
        return f"Event {event_id} deleted."
    except Exception as e:
        return f"Failed to delete event: {e}"


def show_calendar(days_ahead: int = 1, agent=None) -> str:
    """Navigate the HUD to the calendar panel and return today's events for spoken delivery."""
    if agent is not None:
        agent.pending_actions.append({'type': 'switch_tab', 'tab': 'calendar'})
    return get_calendar_events(days_ahead=days_ahead)
