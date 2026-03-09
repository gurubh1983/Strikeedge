variable "aws_region" {
  description = "AWS region for preprod deployment"
  type        = string
  default     = "ap-south-1"
}

variable "db_master_password" {
  description = "Aurora master password for preprod"
  type        = string
  sensitive   = true
}
