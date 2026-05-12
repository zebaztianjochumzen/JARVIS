"""Gmail tools — read inbox, search, and triage emails.

Reuses credentials.json from the JARVIS root (same file as Calendar).
A separate token file (gmail_token.json) is used so the Calendar token
is not invalidated when Gmail is authorised.

Required: Enable the Gmail API in Google Cloud Console for the same
project that issued credentials.json.
"""

from pathlib import Path

GMAIL_SCOPES = ["https://www.googleapis.com/auth/gmail.readonly"]
REPO_ROOT    = Path(__file__).parent.parent.parent
CREDS_PATH   = REPO_ROOT / "credentials.json"
GMAIL_TOKEN  = REPO_ROOT / "gmail_token.json"


def _service():
    from google.oauth2.credentials import Credentials
    from google_auth_oauthlib.flow import InstalledAppFlow
    from google.auth.transport.requests import Request
    from googleapiclient.discovery import build

    creds = None
    if GMAIL_TOKEN.exists():
        creds = Credentials.from_authorized_user_file(str(GMAIL_TOKEN), GMAIL_SCOPES)

    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            if not CREDS_PATH.exists():
                raise FileNotFoundError(
                    "Gmail not configured. Place credentials.json in the JARVIS root "
                    "and enable the Gmail API in Google Cloud Console → APIs & Services."
                )
            flow = InstalledAppFlow.from_client_secrets_file(
                str(CREDS_PATH), GMAIL_SCOPES
            )
            creds = flow.run_local_server(port=0)
        GMAIL_TOKEN.write_text(creds.to_json())

    return build("gmail", "v1", credentials=creds)


def _decode_body(payload: dict) -> str:
    """Extract the plain-text body from a message payload (recursive)."""
    import base64

    if payload.get("mimeType") == "text/plain":
        data = payload.get("body", {}).get("data", "")
        if data:
            return base64.urlsafe_b64decode(data + "==").decode("utf-8", errors="replace")

    for part in payload.get("parts", []):
        text = _decode_body(part)
        if text:
            return text
    return ""


def _fmt(msg: dict, include_body: bool = False) -> dict:
    """Normalise a Gmail API message into a concise dict."""
    headers = {h["name"]: h["value"] for h in msg.get("payload", {}).get("headers", [])}
    out = {
        "id":      msg.get("id", ""),
        "from":    headers.get("From", ""),
        "subject": headers.get("Subject", "(no subject)"),
        "date":    headers.get("Date", ""),
        "snippet": msg.get("snippet", ""),
    }
    if include_body:
        out["body"] = _decode_body(msg.get("payload", {}))[:2000]
    return out


def _fetch_messages(svc, label_ids: list, query: str = "", max_results: int = 10) -> list:
    """Fetch and hydrate messages from the Gmail API."""
    resp = svc.users().messages().list(
        userId="me",
        labelIds=label_ids,
        q=query,
        maxResults=min(max_results, 20),
    ).execute()

    emails = []
    for m in resp.get("messages", []):
        full = svc.users().messages().get(
            userId="me",
            id=m["id"],
            format="metadata",
            metadataHeaders=["From", "Subject", "Date"],
        ).execute()
        emails.append(_fmt(full))
    return emails


# ── Public tool functions ─────────────────────────────────────────────────────

def read_gmail_inbox(max_results: int = 10, unread_only: bool = False, agent=None) -> str:
    """Fetch recent emails from Gmail and return a spoken-friendly summary."""
    try:
        svc = _service()
        q = "is:unread" if unread_only else ""
        emails = _fetch_messages(svc, ["INBOX"], query=q, max_results=max_results)

        if not emails:
            return "Inbox is clear — no " + ("unread " if unread_only else "") + "messages."

        label = "unread " if unread_only else ""
        lines = [f"You have {len(emails)} {label}email(s) in your inbox:"]
        for i, e in enumerate(emails, 1):
            snippet = e["snippet"][:90].strip()
            lines.append(f"{i}. From {e['from']} — {e['subject']}. {snippet}…")

        return "\n".join(lines)

    except FileNotFoundError as err:
        return str(err)
    except Exception as err:
        return f"Gmail error: {err}"


def search_gmail(query: str, max_results: int = 5, agent=None) -> str:
    """Search Gmail with a query string (e.g. 'from:boss subject:invoice is:unread')."""
    try:
        svc = _service()
        emails = _fetch_messages(svc, [], query=query, max_results=max_results)

        if not emails:
            return f"No emails found matching: {query}"

        lines = [f"Found {len(emails)} email(s) for '{query}':"]
        for i, e in enumerate(emails, 1):
            lines.append(f"{i}. From {e['from']} — {e['subject']}. {e['snippet'][:100]}…")

        return "\n".join(lines)

    except FileNotFoundError as err:
        return str(err)
    except Exception as err:
        return f"Gmail search error: {err}"


def gmail_triage(agent=None) -> str:
    """Fetch unread inbox emails and ask Claude to categorise them as URGENT / ACTION / FYI."""
    try:
        svc = _service()
        emails = _fetch_messages(svc, ["INBOX"], query="is:unread", max_results=15)

        if not emails:
            return "No unread emails — inbox is clear."

        lines = [
            f"You have {len(emails)} unread email(s). Here is your inbox for triage:",
            "",
        ]
        for i, e in enumerate(emails, 1):
            lines.append(
                f"{i}. FROM: {e['from']}\n"
                f"   SUBJECT: {e['subject']}\n"
                f"   PREVIEW: {e['snippet'][:140]}"
            )
        lines += [
            "",
            "Please categorise each email as one of:",
            "  URGENT — needs a response today",
            "  ACTION — needs follow-up but not today",
            "  FYI    — informational, no reply needed",
            "Give a one-line summary per email plus the category.",
        ]
        return "\n".join(lines)

    except FileNotFoundError as err:
        return str(err)
    except Exception as err:
        return f"Gmail triage error: {err}"
