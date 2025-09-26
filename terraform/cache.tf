# This file defines the ElastiCache for Redis cluster.

# A subnet group is required, listing the private subnets the cache can use.
resource "aws_elasticache_subnet_group" "default" {
  name       = "main-cache-subnet-group"
  subnet_ids = [aws_subnet.private_a.id, aws_subnet.private_b.id]
  tags = {
    Name = "My Cache Subnet Group"
  }
}

# The ElastiCache cluster resource.
resource "aws_elasticache_cluster" "tf_cache" {
  cluster_id           = "app-cache-cluster"
  engine               = "redis"
  node_type            = "cache.t3.small" # Not Free Tier, but small
  num_cache_nodes      = 1
  engine_version       = "7.1" # Use a modern, supported version
  parameter_group_name = "default.redis7"
  port                 = var.cache_port

  subnet_group_name  = aws_elasticache_subnet_group.default.name
  security_group_ids = [aws_security_group.cache_sg.id]
}
