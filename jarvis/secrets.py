"""Secret resolution — AWS Secrets Manager with .env fallback for local dev.

Resolution order for every secret:
  1. Environment variable (set in .env for local dev, or already in os.environ)
  2. AWS Secrets Manager (used in production via IAM role or ~/.aws/credentials)

Call load_all() once at server startup to pull every configured secret into
os.environ so all downstream libraries (anthropic, telebot, etc.) find them
automatically without needing to know about Secrets Manager.
"""

import json
import logging
import os

logger = logging.getLogger(__name__)

AWS_REGION  = os.getenv("AWS_REGION", "eu-north-1")
JARVIS_ENV  = os.getenv("JARVIS_ENV", "dev")

# Maps logical name → (Secrets Manager path template, env-var fallback name)
_SECRET_MAP: dict[str, tuple[str, str]] = {
    # Core AI
    "ANTHROPIC_API_KEY":       ("jarvis/{env}/anthropic-api-key",       "ANTHROPIC_API_KEY"),
    # Voice
    "ELEVENLABS_API_KEY":      ("jarvis/{env}/elevenlabs-api-key",       "ELEVENLABS_API_KEY"),
    # Music
    "SPOTIFY_CLIENT_ID":       ("jarvis/{env}/spotify-client-id",        "SPOTIFY_CLIENT_ID"),
    "SPOTIFY_CLIENT_SECRET":   ("jarvis/{env}/spotify-client-secret",    "SPOTIFY_CLIENT_SECRET"),
    "SPOTIFY_REFRESH_TOKEN":   ("jarvis/{env}/spotify-refresh-token",    "SPOTIFY_REFRESH_TOKEN"),
    # Reach (Phase C)
    "TELEGRAM_BOT_TOKEN":      ("jarvis/{env}/telegram-bot-token",       "TELEGRAM_BOT_TOKEN"),
    "TELEGRAM_OWNER_ID":         ("jarvis/{env}/telegram-owner-id",         "TELEGRAM_OWNER_ID"),
    "DISCORD_BOT_TOKEN":         ("jarvis/{env}/discord-bot-token",         "DISCORD_BOT_TOKEN"),
    "SLACK_BOT_TOKEN":           ("jarvis/{env}/slack-bot-token",           "SLACK_BOT_TOKEN"),
    # Google OAuth client (two separate secrets)
    "GOOGLE_CLIENT_ID":        ("jarvis/{env}/google-client-id",          "GOOGLE_CLIENT_ID"),
    "GOOGLE_CLIENT_SECRET":    ("jarvis/{env}/google-client-secret",      "GOOGLE_CLIENT_SECRET"),
    "GOOGLE_CALENDAR_TOKEN":   ("jarvis/{env}/google-calendar-token",    "GOOGLE_CALENDAR_TOKEN"),
    "GOOGLE_GMAIL_TOKEN":      ("jarvis/{env}/google-gmail-token",       "GOOGLE_GMAIL_TOKEN"),
    "GOOGLE_API_KEY":          ("jarvis/{env}/google-api-key",           "GOOGLE_API_KEY"),
    # Google Drive — token stored separately (auto-generated on first use)
    "GOOGLE_DRIVE_TOKEN":      ("jarvis/{env}/google-drive-token",       "GOOGLE_DRIVE_TOKEN"),
}

# In-memory cache — avoids repeated network calls within one process lifetime
_cache: dict[str, str] = {}

# Secrets that must be present for JARVIS to function; others are optional
_REQUIRED = {"ANTHROPIC_API_KEY"}


def get_secret(name: str, environment: str = JARVIS_ENV) -> str:
    """Return a secret value, raising RuntimeError if not found anywhere.

    Checks the in-memory cache first, then env var, then AWS Secrets Manager.
    """
    if name in _cache:
        return _cache[name]

    if name not in _SECRET_MAP:
        raise KeyError(f"Unknown secret '{name}'. Add it to _SECRET_MAP in secrets.py.")

    secret_path, env_var = _SECRET_MAP[name]

    # 1. Environment variable (covers .env loaded by python-dotenv)
    value = os.getenv(env_var, "").strip()
    if value:
        _cache[name] = value
        return value

    # 2. AWS Secrets Manager
    try:
        import boto3
        path   = secret_path.format(env=environment)
        client = boto3.client("secretsmanager", region_name=AWS_REGION)
        resp   = client.get_secret_value(SecretId=path)
        raw    = resp["SecretString"].strip()

        # If the secret is stored as a JSON object {"key": "value"}, unwrap it
        if raw.startswith("{"):
            try:
                data = json.loads(raw)
                # Return full JSON string for compound secrets (Google tokens, credentials)
                if name in ("GOOGLE_CREDENTIALS", "GOOGLE_CALENDAR_TOKEN", "GOOGLE_GMAIL_TOKEN", "GOOGLE_DRIVE_TOKEN"):
                    value = raw
                else:
                    value = next(iter(data.values()))
            except json.JSONDecodeError:
                value = raw
        else:
            value = raw

        value = value.strip().strip('"\'').strip()
        _cache[name] = value
        return value

    except ImportError:
        logger.debug("boto3 not installed — skipping AWS Secrets Manager")
    except Exception as exc:
        logger.debug("Secrets Manager lookup failed for '%s': %s", name, exc)

    raise RuntimeError(
        f"Secret '{name}' not found.\n"
        f"  Local dev:  set {env_var} in .env\n"
        f"  Production: populate jarvis/{environment}/{name.lower().replace('_','-')} "
        f"in AWS Secrets Manager"
    )


def get_secret_optional(name: str, environment: str = JARVIS_ENV) -> str:
    """Like get_secret() but returns '' instead of raising if not found."""
    try:
        return get_secret(name, environment)
    except (RuntimeError, KeyError):
        return ""


def load_all(environment: str = JARVIS_ENV) -> None:
    """Load every configured secret into os.environ at server startup.

    Required secrets raise RuntimeError if missing.
    Optional secrets are silently skipped if not configured.
    """
    loaded, skipped, failed = [], [], []

    for name in _SECRET_MAP:
        env_var = _SECRET_MAP[name][1]
        required = name in _REQUIRED
        try:
            value = get_secret(name, environment)
            os.environ[env_var] = value
            loaded.append(name)
        except RuntimeError:
            if required:
                failed.append(name)
            else:
                skipped.append(name)

    if loaded:
        logger.info("Secrets loaded: %s", ", ".join(loaded))
    if skipped:
        logger.debug("Secrets not configured (optional): %s", ", ".join(skipped))
    if failed:
        raise RuntimeError(
            f"Required secret(s) not found: {', '.join(failed)}\n"
            "Set the corresponding env vars in .env or populate them in AWS Secrets Manager."
        )


def put_secret(name: str, value: str, environment: str = JARVIS_ENV) -> None:
    """Write or update a secret value in AWS Secrets Manager.

    Used for secrets that rotate automatically (e.g. Google OAuth tokens).
    Falls back silently if boto3 is not available.
    """
    if name not in _SECRET_MAP:
        raise KeyError(f"Unknown secret '{name}'.")

    secret_path = _SECRET_MAP[name][0].format(env=environment)
    _cache[name] = value  # update local cache immediately

    try:
        import boto3
        client = boto3.client("secretsmanager", region_name=AWS_REGION)
        client.put_secret_value(SecretId=secret_path, SecretString=value)
        logger.debug("Secret '%s' updated in Secrets Manager.", name)
    except ImportError:
        logger.debug("boto3 not installed — skipping Secrets Manager write for '%s'", name)
    except Exception as exc:
        logger.warning("Could not update secret '%s' in Secrets Manager: %s", name, exc)
