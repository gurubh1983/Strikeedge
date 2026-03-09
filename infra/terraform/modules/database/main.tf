resource "aws_security_group" "db" {
  name        = "strikeedge-${var.environment}-db-sg"
  description = "DB access security group"
  vpc_id      = var.vpc_id
}

resource "aws_security_group" "redis" {
  name        = "strikeedge-${var.environment}-redis-sg"
  description = "Redis access security group"
  vpc_id      = var.vpc_id
}

resource "aws_db_subnet_group" "main" {
  name       = "strikeedge-${var.environment}-db-subnets"
  subnet_ids = var.private_subnet_ids
}

resource "aws_rds_cluster" "aurora" {
  cluster_identifier      = "strikeedge-${var.environment}-aurora"
  engine                  = "aurora-postgresql"
  engine_mode             = "provisioned"
  engine_version          = "15.4"
  database_name           = var.db_name
  master_username         = var.db_master_username
  master_password         = var.db_master_password
  db_subnet_group_name    = aws_db_subnet_group.main.name
  vpc_security_group_ids  = [aws_security_group.db.id]
  storage_encrypted       = true
  backup_retention_period = 7
  skip_final_snapshot     = true
}

resource "aws_rds_cluster_instance" "writer" {
  identifier         = "strikeedge-${var.environment}-aurora-writer"
  cluster_identifier = aws_rds_cluster.aurora.id
  instance_class     = "db.serverless"
  engine             = aws_rds_cluster.aurora.engine
  engine_version     = aws_rds_cluster.aurora.engine_version
}

resource "aws_elasticache_subnet_group" "main" {
  name       = "strikeedge-${var.environment}-redis-subnets"
  subnet_ids = var.private_subnet_ids
}

resource "aws_elasticache_cluster" "redis" {
  cluster_id           = "strikeedge-${var.environment}-redis"
  engine               = "redis"
  node_type            = var.redis_node_type
  num_cache_nodes      = 1
  parameter_group_name = "default.redis7"
  subnet_group_name    = aws_elasticache_subnet_group.main.name
  security_group_ids   = [aws_security_group.redis.id]
}
