"""Shared Google OAuth helper — builds credentials.json from two AWS secrets.

Uses a fixed redirect port (8085) so the URI can be registered in Google Cloud Console:
  Authorized redirect URIs → http://localhost:8085/
"""

import json
import os
import tempfile
from pathlib import Path

REPO_ROOT = Path(__file__).parent.parent.parent


def get_credentials_path() -> Path:
    """Return a path to a valid credentials.json file.

    Resolution order:
      1. credentials.json in the JARVIS root (local dev)
      2. GOOGLE_CLIENT_ID + GOOGLE_CLIENT_SECRET env vars (AWS Secrets Manager)
    """
    local = REPO_ROOT / 'credentials.json'
    if local.exists():
        return local

    client_id     = os.environ.get('GOOGLE_CLIENT_ID', '').strip()
    client_secret = os.environ.get('GOOGLE_CLIENT_SECRET', '').strip()

    if client_id and client_secret:
        payload = {
            "installed": {
                "client_id":                   client_id,
                "client_secret":               client_secret,
                "redirect_uris":               ["http://localhost"],
                "auth_uri":                    "https://accounts.google.com/o/oauth2/auth",
                "token_uri":                   "https://oauth2.googleapis.com/token",
                "auth_provider_x509_cert_url": "https://www.googleapis.com/oauth2/v1/certs",
            }
        }
        tmp = Path(tempfile.gettempdir()) / 'jarvis_google_credentials.json'
        tmp.write_text(json.dumps(payload))
        return tmp

    raise FileNotFoundError(
        "Google OAuth not configured. Either place credentials.json in the JARVIS root, "
        "or set GOOGLE_CLIENT_ID and GOOGLE_CLIENT_SECRET in AWS Secrets Manager."
    )
