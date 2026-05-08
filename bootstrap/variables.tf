variable "aws_region" {
  description = "AWS region for state resources"
  type        = string
  default     = "eu-north-1"
}

variable "state_bucket_name" {
  description = "Name for the S3 bucket that stores Terraform state"
  type        = string
  default     = "jarvis-tf-state-eun1"
}
