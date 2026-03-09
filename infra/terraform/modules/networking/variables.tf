variable "environment" {
  description = "Environment name"
  type        = string
}

variable "vpc_cidr" {
  description = "VPC CIDR"
  type        = string
  default     = "10.20.0.0/16"
}

variable "private_subnet_cidr_a" {
  description = "Private subnet A CIDR"
  type        = string
  default     = "10.20.1.0/24"
}

variable "private_subnet_cidr_b" {
  description = "Private subnet B CIDR"
  type        = string
  default     = "10.20.2.0/24"
}

variable "az_a" {
  description = "Availability zone A"
  type        = string
}

variable "az_b" {
  description = "Availability zone B"
  type        = string
}
