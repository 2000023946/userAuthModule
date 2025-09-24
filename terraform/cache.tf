resource "aws_elasticache_cluster" "tf_cache" {
    cluster_id           = "cluster-example"
    engine               = "redis"
    node_type            = "cache.m4.large"
    num_cache_nodes      = 1
    port                 = var.cache_port

    engine_version       = "7.1"                # CHANGED to a modern, supported version
    parameter_group_name = "default.redis7"       # CHANGED to match the new version

    #two lines to add the communication
    subnet_group_name = aws_elasticache_subnet_group.default.name
    security_group_ids = [aws_security_group.cache_sg.id]
}


# 3. Define the variable for the database password
variable "cache_port" {
  description = "PORT for cache"
  type        = number
  sensitive   = true # Hides the password from Terraform output
  default = 6379
}
