# One-time import blocks — bring manually-created secrets under Terraform state.
# These are idempotent: once a resource is in state the import block is a no-op.

import {
  to = aws_secretsmanager_secret.telegram_bot_token
  id = "jarvis/${var.environment}/telegram-bot-token"
}

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

# discord_bot_token and slack_bot_token were not pre-created — Terraform will create them.
