output "vpc_id" {
  value = module.networking.vpc_id
}

output "aurora_endpoint" {
  value = module.database.aurora_endpoint
}

output "redis_endpoint" {
  value = module.database.redis_endpoint
}

output "ecs_cluster_name" {
  value = module.compute.ecs_cluster_name
}
