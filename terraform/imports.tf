# One-time import blocks — bring manually-created secrets under Terraform state.
# These are idempotent: once a resource is in state the import block is a no-op.
# Safe to leave in permanently; remove after first successful apply if preferred.

import {
  to = aws_secretsmanager_secret.telegram_owner_id
  id = "jarvis/${var.environment}/telegram-owner-id"
}

import {
  to = aws_secretsmanager_secret.openclaw_api_key
  id = "jarvis/${var.environment}/openclaw-api-key"
}

import {
  to = aws_secretsmanager_secret.openclaw_gateway_ws_url
  id = "jarvis/${var.environment}/openclaw-gateway-ws-url"
}

import {
  to = aws_secretsmanager_secret.openclaw_admin_sessions
  id = "jarvis/${var.environment}/openclaw-admin-sessions"
}

import {
  to = aws_secretsmanager_secret.discord_bot_token
  id = "jarvis/${var.environment}/discord-bot-token"
}

import {
  to = aws_secretsmanager_secret.slack_bot_token
  id = "jarvis/${var.environment}/slack-bot-token"
}
