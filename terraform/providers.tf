provider "aws" {
  region = var.aws_region
  # Credentials read from AWS_ACCESS_KEY_ID and AWS_SECRET_ACCESS_KEY env vars
}
