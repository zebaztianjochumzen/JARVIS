#!/usr/bin/env python3
"""
One-time Spotify OAuth setup.

Run:  python scripts/spotify_auth.py

1. Creates a Spotify app at https://developer.spotify.com/dashboard
2. Add http://localhost:8888/callback as a Redirect URI in the app settings
3. Run this script — it opens a browser, you log in, it captures the token
4. Copy the printed values into .env or AWS Secrets Manager
"""

import sys
import os
import base64
import webbrowser
import threading
from http.server import HTTPServer, BaseHTTPRequestHandler
from urllib.parse import urlencode, parse_qs, urlparse

import requests

SCOPES = (
    "user-read-currently-playing "
    "user-read-playback-state "
    "user-modify-playback-state"
)
REDIRECT_URI = "http://127.0.0.1:8888/callback"

_code_received = threading.Event()
_auth_code: str | None = None


class _CallbackHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        global _auth_code
        params = parse_qs(urlparse(self.path).query)
        if "code" in params:
            _auth_code = params["code"][0]
            self.send_response(200)
            self.send_header("Content-Type", "text/html")
            self.end_headers()
            self.wfile.write(
                b"<html><body style='font-family:monospace;background:#070b14;color:#4fc3f7;"
                b"display:flex;align-items:center;justify-content:center;height:100vh'>"
                b"<h2>Authorization complete. You may close this tab.</h2></body></html>"
            )
        else:
            self.send_response(400)
            self.end_headers()
            self.wfile.write(b"Authorization denied or error.")
        _code_received.set()

    def log_message(self, *_):
        pass


def main():
    client_id = (
        os.getenv("SPOTIFY_CLIENT_ID")
        or input("Spotify Client ID: ").strip()
    )
    client_secret = (
        os.getenv("SPOTIFY_CLIENT_SECRET")
        or input("Spotify Client Secret: ").strip()
    )

    auth_url = "https://accounts.spotify.com/authorize?" + urlencode({
        "client_id":     client_id,
        "response_type": "code",
        "redirect_uri":  REDIRECT_URI,
        "scope":         SCOPES,
    })

    server = HTTPServer(("localhost", 8888), _CallbackHandler)
    t = threading.Thread(target=lambda: server.serve_forever(), daemon=True)
    t.start()

    print("\nOpening browser for Spotify authorization...")
    webbrowser.open(auth_url)
    print("Waiting for callback on http://localhost:8888/callback ...")

    if not _code_received.wait(timeout=120):
        print("Timed out waiting for authorization.")
        sys.exit(1)
    server.shutdown()

    if not _auth_code:
        print("No authorization code received.")
        sys.exit(1)

    creds = base64.b64encode(f"{client_id}:{client_secret}".encode()).decode()
    r = requests.post(
        "https://accounts.spotify.com/api/token",
        headers={"Authorization": f"Basic {creds}"},
        data={
            "grant_type":   "authorization_code",
            "code":         _auth_code,
            "redirect_uri": REDIRECT_URI,
        },
        timeout=10,
    )
    r.raise_for_status()
    tokens        = r.json()
    refresh_token = tokens["refresh_token"]

    env = os.getenv("JARVIS_ENV", "dev")

    print(f"""
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
  Authorization complete!
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

Add to .env (local dev):

  SPOTIFY_CLIENT_ID={client_id}
  SPOTIFY_CLIENT_SECRET={client_secret}
  SPOTIFY_REFRESH_TOKEN={refresh_token}

Or store in AWS Secrets Manager:

  aws secretsmanager put-secret-value \\
    --secret-id jarvis/{env}/spotify-client-id \\
    --secret-string '{client_id}'

  aws secretsmanager put-secret-value \\
    --secret-id jarvis/{env}/spotify-client-secret \\
    --secret-string '{client_secret}'

  aws secretsmanager put-secret-value \\
    --secret-id jarvis/{env}/spotify-refresh-token \\
    --secret-string '{refresh_token}'
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
""")


if __name__ == "__main__":
    main()
