output "ecs_cluster_name" {
  value = aws_ecs_cluster.main.name
}

output "api_security_group_id" {
  value = aws_security_group.api.id
}
