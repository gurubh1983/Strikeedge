terraform {
  required_version = ">= 1.6.0"
}

provider "aws" {
  region = var.aws_region
}

module "networking" {
  source      = "../../modules/networking"
  environment = "staging"
  az_a        = "${var.aws_region}a"
  az_b        = "${var.aws_region}b"
}

module "database" {
  source             = "../../modules/database"
  environment        = "staging"
  vpc_id             = module.networking.vpc_id
  private_subnet_ids = module.networking.private_subnet_ids
  db_master_password = var.db_master_password
}

module "compute" {
  source             = "../../modules/compute"
  environment        = "staging"
  vpc_id             = module.networking.vpc_id
  private_subnet_ids = module.networking.private_subnet_ids
}
