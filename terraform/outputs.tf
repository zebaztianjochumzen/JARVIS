output "instance_id" {
  value = aws_instance.main.id
}

output "instance_public_ip" {
  value = aws_instance.main.public_ip
}

output "vpc_id" {
  value = aws_vpc.main.id
}

output "anthropic_secret_arn" {
  description = "ARN of the Anthropic API key secret — populate value in AWS Console or CLI"
  value       = aws_secretsmanager_secret.anthropic_api_key.arn
}

output "elevenlabs_secret_arn" {
  description = "ARN of the ElevenLabs API key secret — populate value in AWS Console or CLI"
  value       = aws_secretsmanager_secret.elevenlabs_api_key.arn
}
