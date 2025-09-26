# /modules/aurora-global-primary/variables.tf
#
# Input variables for the primary Aurora Global Database cluster module.
# This module is responsible for creating the global container, the primary
# writable cluster, and its writer instance.

# -----------------------------------------------------------------------------
# Naming & Tagging Configuration
# -----------------------------------------------------------------------------

variable "project_name" {
  description = "A name for the project to which this database belongs. Used as a prefix for naming and tagging all resources."
  type        = string
  # Example: "my-web-app"
}

variable "environment" {
  description = "The deployment environment for this database. Used in resource names and tags."
  type        = string
  # Example: "dev", "stg", "prod"
}

# -----------------------------------------------------------------------------
# Network Configuration
# -----------------------------------------------------------------------------

variable "private_subnet_ids" {
  description = "A list of private subnet IDs where the database instances can be deployed. Must contain subnets from at least two different Availability Zones for high availability."
  type        = list(string)
}

variable "rds_security_group_ids" {
  description = "A list of VPC Security Group IDs to associate with the cluster. Should allow ingress from the application's security group on the PostgreSQL port (5432)."
  type        = list(string)
}

# -----------------------------------------------------------------------------
# Database Configuration
# -----------------------------------------------------------------------------

variable "db_name" {
  description = "The name of the initial database to be created when the cluster is provisioned."
  type        = string
  default     = "appdb"
}

variable "db_username" {
  description = "The master username for the database cluster."
  type        = string
  default     = "admin"
}

variable "db_password" {
  description = "The master password for the database cluster. WARNING: This should be passed in securely (e.g., from a secrets manager), not hardcoded in configuration files."
  type        = string
  sensitive   = true # Prevents the password from being displayed in Terraform output.

  validation {
    # Enforces a minimum password length for security.
    condition     = length(var.db_password) >= 16
    error_message = "The database password must be at least 16 characters long."
  }
}

# -----------------------------------------------------------------------------
# Instance Configuration
# -----------------------------------------------------------------------------

variable "instance_class" {
  description = "The instance class that determines the CPU and memory of the database writer instance."
  type        = string
  default     = "db.r6g.large"
  # Example: "db.r6g.large", "db.t3.medium"
}

variable "reader_instance_count" {
  description = "The number of read-replica instances to create in the primary cluster."
  type        = number
  default     = 0 # Default to zero readers
}
