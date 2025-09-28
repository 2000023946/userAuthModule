# -----------------------------------------------------------------------------
# GLOBAL & PROJECT SETTINGS
# -----------------------------------------------------------------------------

variable "project_name" {
  description = "A unique name for the project, used as a prefix for all resources."
  type        = string
}

variable "environment" {
  description = "The deployment environment (e.g., dev, staging, prod)."
  type        = string
}

# -----------------------------------------------------------------------------
# PRIMARY REGION CONFIGURATION
# -----------------------------------------------------------------------------

variable "primary_aws_region" {
  description = "The primary AWS region where the main application and writer database will be deployed."
  type        = string
}

# -----------------------------------------------------------------------------
# SECONDARY REGION (DISASTER RECOVERY) CONFIGURATION
# -----------------------------------------------------------------------------

variable "secondary_aws_region" {
  description = "The secondary AWS region for the read-replica database and disaster recovery resources."
  type        = string
}

# -----------------------------------------------------------------------------
# NETWORKING VARIABLES
# -----------------------------------------------------------------------------

variable "vpc_cidr_block" {
  description = "The overall IP address range for the VPCs in both regions."
  type        = string
}

variable "public_subnet_cidrs" {
  description = "A list of CIDR blocks for public subnets."
  type        = list(string)
}

variable "private_subnet_cidrs" {
  description = "A list of CIDR blocks for private subnets."
  type        = list(string)
}

variable "my_ip" {
  description = "Your personal IP address for secure SSH access to servers."
  type        = string
}

# -----------------------------------------------------------------------------
# DATABASE VARIABLES
# -----------------------------------------------------------------------------

variable "db_name" {
  description = "The name for the initial database to be created."
  type        = string
}

variable "db_username" {
  description = "The master username for the database."
  type        = string
}

variable "db_password" {
  description = "The master password for the database. Must be at least 16 characters."
  type        = string
  sensitive   = true
}

variable "primary_db_instance_class" {
  description = "The instance class for the primary database writer instance."
  type        = string
}

variable "secondary_db_instance_class" {
  description = "The instance class for the secondary read-replica database instance."
  type        = string
}

variable "db_reader_instance_count" {
  description = "The number of read-replica instances to create in the primary region."
  type        = number
}

# -----------------------------------------------------------------------------
# APPLICATION SERVER VARIABLES
# -----------------------------------------------------------------------------

variable "docker_image" {
  description = "The Docker image to pull from Docker Hub for the application."
  type        = string
}

variable "app_server_instance_type" {
  description = "The EC2 instance type for the application servers."
  type        = string
}

variable "ec2_key_pair_name" {
  description = "The name of an EC2 key pair that already exists in the primary AWS region for SSH access."
  type        = string
}

