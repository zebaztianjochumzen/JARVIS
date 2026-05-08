terraform {
  required_version = ">= 1.5.0"

  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = "~> 5.0"
    }
  }

  # Uncomment after running bootstrap/ to create the state bucket and lock table,
  # then run: terraform init -migrate-state
  # backend "s3" {
  #   bucket         = "jarvis-terraform-state"
  #   key            = "terraform.tfstate"
  #   region         = "us-east-1"
  #   dynamodb_table = "jarvis-terraform-locks"
  #   encrypt        = true
  # }
}
