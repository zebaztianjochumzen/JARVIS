variable "aws_region" {
  description = "AWS region for state resources"
  type        = string
  default     = "eu-north-1"
}

variable "state_bucket_name" {
  description = "Name for the S3 bucket that stores Terraform state"
  type        = string
  default     = "jarvis-terraform-state"
}

variable "lock_table_name" {
  description = "Name for the DynamoDB table used for state locking"
  type        = string
  default     = "jarvis-terraform-locks"
}
