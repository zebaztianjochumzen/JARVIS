"""Google Drive tools — search and read files from the user's Drive.

Uses the same credentials.json as Calendar and Gmail.
Token stored separately in drive_token.json.
"""

from pathlib import Path

DRIVE_SCOPES = ["https://www.googleapis.com/auth/drive.readonly"]
REPO_ROOT    = Path(__file__).parent.parent.parent
CREDS_PATH   = REPO_ROOT / "credentials.json"
DRIVE_TOKEN  = REPO_ROOT / "drive_token.json"


def _service():
    from google.oauth2.credentials import Credentials
    from google_auth_oauthlib.flow import InstalledAppFlow
    from google.auth.transport.requests import Request
    from googleapiclient.discovery import build

    creds = None
    if DRIVE_TOKEN.exists():
        creds = Credentials.from_authorized_user_file(str(DRIVE_TOKEN), DRIVE_SCOPES)

    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            from jarvis.tools.google_auth import get_credentials_path
            flow = InstalledAppFlow.from_client_secrets_file(str(get_credentials_path()), DRIVE_SCOPES)
            creds = flow.run_local_server(port=8085)
        DRIVE_TOKEN.write_text(creds.to_json())

    return build("drive", "v3", credentials=creds)


def search_drive(query: str, max_results: int = 10, agent=None) -> str:
    """Search Google Drive for files matching a name or keyword."""
    try:
        svc = _service()
        # Search both name and full-text content
        q = f"(name contains '{query}' or fullText contains '{query}') and trashed = false"
        result = svc.files().list(
            q=q,
            pageSize=min(max_results, 20),
            fields="files(id, name, mimeType, modifiedTime, webViewLink, size)",
            orderBy="modifiedTime desc",
        ).execute()

        files = result.get("files", [])
        if not files:
            return f"No files found in Drive matching '{query}'."

        type_map = {
            "application/vnd.google-apps.document":     "Doc",
            "application/vnd.google-apps.spreadsheet":  "Sheet",
            "application/vnd.google-apps.presentation": "Slides",
            "application/vnd.google-apps.folder":       "Folder",
            "application/pdf":                          "PDF",
        }

        lines = [f"Found {len(files)} file(s) in Drive for '{query}':"]
        for f in files:
            ftype   = type_map.get(f["mimeType"], f["mimeType"].split("/")[-1])
            modified = f.get("modifiedTime", "")[:10]
            link    = f.get("webViewLink", "")
            lines.append(f"  • [{ftype}] {f['name']} (modified {modified})\n    {link}")

        return "\n".join(lines)

    except FileNotFoundError as e:
        return str(e)
    except Exception as e:
        return f"Drive search failed: {e}"


def read_drive_file(file_id: str, agent=None) -> str:
    """Read the text content of a Google Doc or plain text file from Drive."""
    try:
        svc = _service()

        # Get file metadata to check type
        meta = svc.files().get(fileId=file_id, fields="name,mimeType").execute()
        mime = meta.get("mimeType", "")
        name = meta.get("name", file_id)

        if mime == "application/vnd.google-apps.document":
            # Export Google Doc as plain text
            content = svc.files().export(fileId=file_id, mimeType="text/plain").execute()
            text = content.decode("utf-8") if isinstance(content, bytes) else str(content)
        elif mime.startswith("text/"):
            content = svc.files().get_media(fileId=file_id).execute()
            text = content.decode("utf-8") if isinstance(content, bytes) else str(content)
        else:
            return f"Cannot read '{name}' — only Google Docs and plain text files are supported."

        text = text.strip()
        if len(text) > 4000:
            text = text[:4000] + f"\n…[{len(text) - 4000} chars truncated]"

        return f"Contents of '{name}':\n\n{text}"

    except FileNotFoundError as e:
        return str(e)
    except Exception as e:
        return f"Drive read failed: {e}"


def open_drive_file(file_id: str, agent=None) -> str:
    """Open a Drive file in the JARVIS browser panel."""
    try:
        svc  = _service()
        meta = svc.files().get(fileId=file_id, fields="name,webViewLink").execute()
        link = meta.get("webViewLink", "")
        name = meta.get("name", file_id)
        if not link:
            return f"No web link available for '{name}'."
        if agent is not None:
            agent.pending_actions.append({"type": "show_browser", "url": link})
        return f"Opening '{name}' in the browser."
    except Exception as e:
        return f"Drive open failed: {e}"
