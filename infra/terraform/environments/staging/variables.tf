variable "aws_region" {
  description = "AWS region for staging deployment"
  type        = string
  default     = "ap-south-1"
}

variable "db_master_password" {
  description = "Aurora master password for staging"
  type        = string
  sensitive   = true
}
