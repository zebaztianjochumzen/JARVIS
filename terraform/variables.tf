variable "aws_region" {
  description = "AWS region to deploy resources into"
  type        = string
  default     = "eu-north-1"
}

variable "project_name" {
  description = "Project name used to namespace resources"
  type        = string
  default     = "jarvis"
}

variable "environment" {
  description = "Deployment environment (dev, staging, production)"
  type        = string
}

variable "instance_type" {
  description = "EC2 instance type"
  type        = string
  default     = "t3.micro"
}
