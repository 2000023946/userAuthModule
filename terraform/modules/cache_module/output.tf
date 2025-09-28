# /modules/elasticache-redis/outputs.tf

output "cluster_id" {
  description = "The ID of the ElastiCache cluster."
  value       = aws_elasticache_cluster.main.cluster_id
}

output "primary_endpoint_address" {
  description = "The hostname of the primary Redis node. This is the address your application should connect to."
  value       = aws_elasticache_cluster.main.cache_nodes[0].address
}

output "port" {
  description = "The port number on which the Redis cluster is listening."
  value       = aws_elasticache_cluster.main.port
}