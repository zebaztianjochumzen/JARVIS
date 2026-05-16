# ── Frontend ───────────────────────────────────────────────────────────────────

resource "aws_secretsmanager_secret" "mapbox_token" {
  name                    = "jarvis/${var.environment}/mapbox-token"
  description             = "Mapbox public token for the JARVIS globe/tactical map"
  recovery_window_in_days = 0

  tags = { Name = "${var.project_name}-${var.environment}-mapbox-token" }
}

# ── Core AI ────────────────────────────────────────────────────────────────────

resource "aws_secretsmanager_secret" "anthropic_api_key" {
  name                    = "jarvis/${var.environment}/anthropic-api-key"
  description             = "Anthropic API key for JARVIS AI brain (Claude Sonnet 4.6)"
  recovery_window_in_days = 0

  tags = { Name = "${var.project_name}-${var.environment}-anthropic-key" }
}

# ── Voice ──────────────────────────────────────────────────────────────────────

resource "aws_secretsmanager_secret" "elevenlabs_api_key" {
  name                    = "jarvis/${var.environment}/elevenlabs-api-key"
  description             = "ElevenLabs API key for JARVIS text-to-speech (alternative to edge-tts)"
  recovery_window_in_days = 0

  tags = { Name = "${var.project_name}-${var.environment}-elevenlabs-key" }
}

# ── Music ──────────────────────────────────────────────────────────────────────

resource "aws_secretsmanager_secret" "spotify_client_id" {
  name                    = "jarvis/${var.environment}/spotify-client-id"
  description             = "Spotify Web API client ID for JARVIS music integration"
  recovery_window_in_days = 0

  tags = { Name = "${var.project_name}-${var.environment}-spotify-client-id" }
}

resource "aws_secretsmanager_secret" "spotify_client_secret" {
  name                    = "jarvis/${var.environment}/spotify-client-secret"
  description             = "Spotify Web API client secret for JARVIS music integration"
  recovery_window_in_days = 0

  tags = { Name = "${var.project_name}-${var.environment}-spotify-client-secret" }
}

resource "aws_secretsmanager_secret" "spotify_refresh_token" {
  name                    = "jarvis/${var.environment}/spotify-refresh-token"
  description             = "Spotify OAuth refresh token — obtained once via scripts/spotify_auth.py"
  recovery_window_in_days = 0

  tags = { Name = "${var.project_name}-${var.environment}-spotify-refresh-token" }
}

# ── Reach & Integration (Phase C) ─────────────────────────────────────────────

resource "aws_secretsmanager_secret" "telegram_bot_token" {
  name                    = "jarvis/${var.environment}/telegram-bot-token"
  description             = "Telegram Bot token from @BotFather — enables JARVIS Telegram channel"
  recovery_window_in_days = 0

  tags = { Name = "${var.project_name}-${var.environment}-telegram-bot-token" }
}

resource "aws_secretsmanager_secret" "telegram_owner_id" {
  name                    = "jarvis/${var.environment}/telegram-owner-id"
  description             = "Telegram numeric user ID of the authorised owner — rejects all other senders"
  recovery_window_in_days = 0

  tags = { Name = "${var.project_name}-${var.environment}-telegram-owner-id" }
}

# ── OpenClaw: Multi-platform messaging gateway ────────────────────────────────

resource "aws_secretsmanager_secret" "openclaw_api_key" {
  name                    = "jarvis/${var.environment}/openclaw-api-key"
  description             = "OpenClaw gateway bearer token (gateway.secret in openclaw config)"
  recovery_window_in_days = 0

  tags = { Name = "${var.project_name}-${var.environment}-openclaw-api-key" }
}

resource "aws_secretsmanager_secret" "openclaw_gateway_ws_url" {
  name                    = "jarvis/${var.environment}/openclaw-gateway-ws-url"
  description             = "WebSocket URL of the running OpenClaw gateway (ws://host:18789)"
  recovery_window_in_days = 0

  tags = { Name = "${var.project_name}-${var.environment}-openclaw-gateway-ws-url" }
}

resource "aws_secretsmanager_secret" "openclaw_admin_sessions" {
  name                    = "jarvis/${var.environment}/openclaw-admin-sessions"
  description             = "Comma-separated OpenClaw session IDs with full operator access"
  recovery_window_in_days = 0

  tags = { Name = "${var.project_name}-${var.environment}-openclaw-admin-sessions" }
}

resource "aws_secretsmanager_secret" "discord_bot_token" {
  name                    = "jarvis/${var.environment}/discord-bot-token"
  description             = "Discord bot token — optional OpenClaw channel"
  recovery_window_in_days = 0

  tags = { Name = "${var.project_name}-${var.environment}-discord-bot-token" }
}

resource "aws_secretsmanager_secret" "slack_bot_token" {
  name                    = "jarvis/${var.environment}/slack-bot-token"
  description             = "Slack bot OAuth token — optional OpenClaw channel"
  recovery_window_in_days = 0

  tags = { Name = "${var.project_name}-${var.environment}-slack-bot-token" }
}

# ── Google APIs (Calendar + Gmail) ────────────────────────────────────────────
#
# Store the full JSON content of credentials.json downloaded from Google Cloud Console.
# After `terraform apply`, populate via:
#   aws secretsmanager put-secret-value \
#     --secret-id jarvis/<env>/google-oauth-credentials \
#     --secret-string file://credentials.json
#
resource "aws_secretsmanager_secret" "google_oauth_credentials" {
  name                    = "jarvis/${var.environment}/google-oauth-credentials"
  description             = "Google OAuth2 credentials JSON (Desktop app) — used for Calendar and Gmail"
  recovery_window_in_days = 0

  tags = { Name = "${var.project_name}-${var.environment}-google-oauth-credentials" }
}

resource "aws_secretsmanager_secret" "google_calendar_token" {
  name                    = "jarvis/${var.environment}/google-calendar-token"
  description             = "Google Calendar OAuth token JSON — written by JARVIS after first auth"
  recovery_window_in_days = 0

  tags = { Name = "${var.project_name}-${var.environment}-google-calendar-token" }
}

resource "aws_secretsmanager_secret" "google_gmail_token" {
  name                    = "jarvis/${var.environment}/google-gmail-token"
  description             = "Google Gmail OAuth token JSON — written by JARVIS after first auth"
  recovery_window_in_days = 0

  tags = { Name = "${var.project_name}-${var.environment}-google-gmail-token" }
}
