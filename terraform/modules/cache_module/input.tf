# /modules/elasticache-redis/variables.tf

# -----------------------------------------------------------------------------
# Naming & Tagging Configuration
# -----------------------------------------------------------------------------

variable "project_name" {
  description = "The name of the project this cache belongs to. Used for naming and tagging."
  type        = string
  # Example: "my-web-app"
}

variable "environment" {
  description = "The deployment environment (e.g., 'dev', 'prod'). Used in resource names and tags."
  type        = string
  # Example: "prod"
}

# -----------------------------------------------------------------------------
# Network Configuration
# -----------------------------------------------------------------------------

variable "private_subnet_ids" {
  description = "A list of private subnet IDs where the cache nodes can be created."
  type        = list(string)
}

variable "cache_security_group_ids" {
  description = "A list of VPC Security Group IDs to associate with the cache. Should allow ingress from the application's security group on the Redis port."
  type        = list(string)
}

# -----------------------------------------------------------------------------
# Cache Cluster Configuration
# -----------------------------------------------------------------------------

variable "instance_type" {
  description = "The instance type for the Redis cache nodes."
  type        = string
  default     = "cache.t3.small"
}

variable "node_count" {
  description = "The number of cache nodes in the cluster. For a simple setup, 1 is sufficient."
  type        = number
  default     = 1
}

variable "engine_version" {
  description = "The version number of the Redis engine to use."
  type        = string
  default     = "7.1"
}

variable "cache_port" {
  description = "The network port on which the Redis server will listen."
  type        = number
  default     = 6379
}