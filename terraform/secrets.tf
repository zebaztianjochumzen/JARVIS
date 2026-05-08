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
