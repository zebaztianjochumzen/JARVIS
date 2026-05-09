resource "aws_secretsmanager_secret" "anthropic_api_key" {
  name        = "jarvis/${var.environment}/anthropic-api-key"
  description = "Anthropic API key for JARVIS AI brain"

  tags = { Name = "${var.project_name}-${var.environment}-anthropic-key" }
}

resource "aws_secretsmanager_secret" "elevenlabs_api_key" {
  name        = "jarvis/${var.environment}/elevenlabs-api-key"
  description = "ElevenLabs API key for JARVIS text-to-speech"

  tags = { Name = "${var.project_name}-${var.environment}-elevenlabs-key" }
}

resource "aws_secretsmanager_secret" "spotify_client_id" {
  name        = "jarvis/${var.environment}/spotify-client-id"
  description = "Spotify Web API client ID for JARVIS music integration"

  tags = { Name = "${var.project_name}-${var.environment}-spotify-client-id" }
}

resource "aws_secretsmanager_secret" "spotify_client_secret" {
  name        = "jarvis/${var.environment}/spotify-client-secret"
  description = "Spotify Web API client secret for JARVIS music integration"

  tags = { Name = "${var.project_name}-${var.environment}-spotify-client-secret" }
}

resource "aws_secretsmanager_secret" "spotify_refresh_token" {
  name        = "jarvis/${var.environment}/spotify-refresh-token"
  description = "Spotify OAuth refresh token — obtained once via scripts/spotify_auth.py"

  tags = { Name = "${var.project_name}-${var.environment}-spotify-refresh-token" }
}
