# /modules/elasticache-redis/main.tf

locals {
  # Create a consistent naming prefix from the input variables.
  name_prefix = "${var.project_name}-${var.environment}"
}

# A subnet group is required, listing the private subnets the cache can use.
resource "aws_elasticache_subnet_group" "default" {
  name       = "${local.name_prefix}-cache-subnet-group"
  subnet_ids = var.private_subnet_ids

  tags = {
    Name = "${local.name_prefix}-cache-subnet-group"
  }
}

# The ElastiCache cluster resource.
resource "aws_elasticache_cluster" "main" {
  cluster_id           = "${local.name_prefix}-cache-cluster"
  engine               = "redis"
  engine_version       = var.engine_version
  node_type            = var.instance_type
  num_cache_nodes      = var.node_count
  port                 = var.cache_port

  # Use a default parameter group compatible with the engine version.
  # For more advanced setups, this could also be an input variable.
  parameter_group_name = "default.redis${split(".", var.engine_version)[0]}"

  # Link the cluster to the network resources.
  subnet_group_name  = aws_elasticache_subnet_group.default.name
  security_group_ids = var.cache_security_group_ids

  tags = {
    Name = "${local.name_prefix}-cache-cluster"
  }
}