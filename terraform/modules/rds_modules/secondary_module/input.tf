# /modules/aurora-global-secondary/variables.tf
#
# Input variables for the secondary (read-replica) Aurora Global Database cluster.
# This module creates a read-only replica cluster in a new region and attaches
# it to an existing global database container.

# -----------------------------------------------------------------------------
# Global Cluster Configuration
# -----------------------------------------------------------------------------

variable "global_cluster_identifier" {
  description = "The unique identifier of the existing Aurora Global Database to which this secondary cluster will be attached. This value must be the output from the primary cluster module."
  type        = string
  # Example: "my-app-prod-global-db"
}

# -----------------------------------------------------------------------------
# Naming & Tagging Configuration
# -----------------------------------------------------------------------------

variable "project_name" {
  description = "The name for the project. This should match the primary cluster's project name for consistency in resource naming and tags."
  type        = string
  # Example: "my-web-app"
}

variable "environment" {
  description = "The deployment environment for this secondary cluster. This is often used to denote its purpose, such as 'dr' for disaster recovery or 'eu-replica'."
  type        = string
  # Example: "dr"
}

# -----------------------------------------------------------------------------
# Network Configuration (for the Secondary Region)
# -----------------------------------------------------------------------------

variable "private_subnet_ids" {
  description = "A list of private subnet IDs located in the secondary region. The database instances will be deployed into these subnets. For high availability, provide subnets from at least two different Availability Zones."
  type        = list(string)
}

variable "rds_security_group_ids" {
  description = "A list of VPC Security Group IDs from the secondary region's VPC to associate with this replica cluster. It should allow appropriate ingress traffic (e.g., from the app servers in the secondary region)."
  type        = list(string)
}

# -----------------------------------------------------------------------------
# Instance Configuration
# -----------------------------------------------------------------------------

variable "instance_class" {
  description = "The instance class that determines the CPU and memory of the read replica instances in this secondary cluster."
  type        = string
  default     = "db.r6g.large"
  # Example: "db.r6g.large", "db.t3.medium"
}