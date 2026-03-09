resource "aws_ecs_cluster" "main" {
  name = "strikeedge-${var.environment}-ecs"
}

resource "aws_cloudwatch_log_group" "api" {
  name              = "/strikeedge/${var.environment}/api"
  retention_in_days = 30
}

resource "aws_security_group" "api" {
  name        = "strikeedge-${var.environment}-api-sg"
  description = "API runtime security group"
  vpc_id      = var.vpc_id
}
