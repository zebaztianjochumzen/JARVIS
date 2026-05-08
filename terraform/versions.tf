terraform {
  required_version = ">= 1.5.0"

  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = "~> 5.0"
    }
  }

  # Run bootstrap/ first to create this bucket, then `terraform init`.
  # The `key` is supplied dynamically by the deploy workflow per environment.
  backend "s3" {
    bucket       = "jarvis-tf-state-eun1"
    region       = "eu-north-1"
    use_lockfile = true
    encrypt      = true
  }
}
