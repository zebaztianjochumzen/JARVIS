# ── IAM role for EC2 ──────────────────────────────────────────────────────────

resource "aws_iam_role" "ec2" {
  name = "${var.project_name}-${var.environment}-ec2-role"

  assume_role_policy = jsonencode({
    Version = "2012-10-17"
    Statement = [{
      Effect    = "Allow"
      Principal = { Service = "ec2.amazonaws.com" }
      Action    = "sts:AssumeRole"
    }]
  })

  tags = { Name = "${var.project_name}-${var.environment}-ec2-role" }
}

# ── Policy: read JARVIS secrets from Secrets Manager ─────────────────────────

resource "aws_iam_role_policy" "read_secrets" {
  name = "read-jarvis-secrets"
  role = aws_iam_role.ec2.id

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [{
      Effect = "Allow"
      Action = [
        "secretsmanager:GetSecretValue",
        "secretsmanager:DescribeSecret",
        "secretsmanager:PutSecretValue",   # needed for Google token rotation
      ]
      Resource = [
        # Core AI
        aws_secretsmanager_secret.anthropic_api_key.arn,
        # Voice
        aws_secretsmanager_secret.elevenlabs_api_key.arn,
        # Music
        aws_secretsmanager_secret.spotify_client_id.arn,
        aws_secretsmanager_secret.spotify_client_secret.arn,
        aws_secretsmanager_secret.spotify_refresh_token.arn,
        # Reach & Integration (Phase C)
        aws_secretsmanager_secret.telegram_bot_token.arn,
        aws_secretsmanager_secret.telegram_owner_id.arn,
        # OpenClaw: Multi-platform messaging gateway
        aws_secretsmanager_secret.openclaw_api_key.arn,
        aws_secretsmanager_secret.openclaw_gateway_ws_url.arn,
        aws_secretsmanager_secret.openclaw_admin_sessions.arn,
        aws_secretsmanager_secret.discord_bot_token.arn,
        aws_secretsmanager_secret.slack_bot_token.arn,
        # Google APIs
        aws_secretsmanager_secret.google_oauth_credentials.arn,
        aws_secretsmanager_secret.google_calendar_token.arn,
        aws_secretsmanager_secret.google_gmail_token.arn,
      ]
    }]
  })
}

# ── Instance profile (attaches the role to EC2) ───────────────────────────────

resource "aws_iam_instance_profile" "ec2" {
  name = "${var.project_name}-${var.environment}-ec2-profile"
  role = aws_iam_role.ec2.name
}
