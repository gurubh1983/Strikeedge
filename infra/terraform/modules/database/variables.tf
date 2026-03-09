variable "environment" {
  type = string
}

variable "vpc_id" {
  type = string
}

variable "private_subnet_ids" {
  type = list(string)
}

variable "db_name" {
  type    = string
  default = "strikeedge"
}

variable "db_master_username" {
  type    = string
  default = "strikeedge_admin"
}

variable "db_master_password" {
  type      = string
  sensitive = true
}

variable "redis_node_type" {
  type    = string
  default = "cache.t4g.small"
}
