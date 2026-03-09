variable "aws_region" {
  description = "AWS region for dev deployment"
  type        = string
  default     = "ap-south-1"
}

variable "db_master_password" {
  description = "Aurora master password for dev"
  type        = string
  sensitive   = true
}
