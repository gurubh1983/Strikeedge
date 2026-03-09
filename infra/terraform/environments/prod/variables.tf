variable "aws_region" {
  description = "AWS region for prod deployment"
  type        = string
  default     = "ap-south-1"
}

variable "db_master_password" {
  description = "Aurora master password for prod"
  type        = string
  sensitive   = true
}
