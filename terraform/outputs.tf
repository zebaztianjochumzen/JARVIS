output "instance_id" {
  value = aws_instance.main.id
}

output "instance_public_ip" {
  value = aws_instance.main.public_ip
}

output "vpc_id" {
  value = aws_vpc.main.id
}

output "instance_public_ip" {
  value = aws_instance.main.public_ip
}

output "vpc_id" {
  value = aws_vpc.main.id
}

# ── Secret ARNs (use these to populate values via CLI or Console) ──────────────

output "anthropic_secret_arn" {
  description = "Populate: aws secretsmanager put-secret-value --secret-id <arn> --secret-string 'sk-ant-...'"
  value       = aws_secretsmanager_secret.anthropic_api_key.arn
}

output "telegram_secret_arn" {
  description = "Populate: aws secretsmanager put-secret-value --secret-id <arn> --secret-string '<bot-token>'"
  value       = aws_secretsmanager_secret.telegram_bot_token.arn
}

output "google_credentials_arn" {
  description = "Populate: aws secretsmanager put-secret-value --secret-id <arn> --secret-string file://credentials.json"
  value       = aws_secretsmanager_secret.google_oauth_credentials.arn
}

output "google_calendar_token_arn" {
  description = "Written automatically by JARVIS after first OAuth consent"
  value       = aws_secretsmanager_secret.google_calendar_token.arn
}

output "google_gmail_token_arn" {
  description = "Written automatically by JARVIS after first OAuth consent"
  value       = aws_secretsmanager_secret.google_gmail_token.arn
}

output "elevenlabs_secret_arn" {
  description = "Populate: aws secretsmanager put-secret-value --secret-id <arn> --secret-string '<key>'"
  value       = aws_secretsmanager_secret.elevenlabs_api_key.arn
}

output "spotify_client_id_arn" {
  value = aws_secretsmanager_secret.spotify_client_id.arn
}

output "spotify_client_secret_arn" {
  value = aws_secretsmanager_secret.spotify_client_secret.arn
}

output "spotify_refresh_token_arn" {
  description = "Populate after running scripts/spotify_auth.py"
  value       = aws_secretsmanager_secret.spotify_refresh_token.arn
}

# ── Convenience: all secret names (copy-paste for CLI) ────────────────────────

output "secret_names" {
  description = "All secret paths in Secrets Manager"
  value = {
    anthropic         = aws_secretsmanager_secret.anthropic_api_key.name
    telegram          = aws_secretsmanager_secret.telegram_bot_token.name
    google_creds      = aws_secretsmanager_secret.google_oauth_credentials.name
    google_cal_token  = aws_secretsmanager_secret.google_calendar_token.name
    google_gmail_token = aws_secretsmanager_secret.google_gmail_token.name
    elevenlabs        = aws_secretsmanager_secret.elevenlabs_api_key.name
    spotify_id        = aws_secretsmanager_secret.spotify_client_id.name
    spotify_secret    = aws_secretsmanager_secret.spotify_client_secret.name
    spotify_token     = aws_secretsmanager_secret.spotify_refresh_token.name
  }
}
