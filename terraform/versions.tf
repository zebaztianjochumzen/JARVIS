terraform {
  required_version = ">= 1.5.0"

  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = "~> 5.0"
    }
  }

  # Run bootstrap/ first to create this bucket and table, then `terraform init`.
  # The `key` is supplied dynamically by the deploy workflow per environment.
  backend "s3" {
    bucket         = "jarvis-terraform-state"
    region         = "us-east-1"
    dynamodb_table = "jarvis-terraform-locks"
    encrypt        = true
  }
}
