variable "name_prefix" {
  description = "A prefix to be added to the names of all resources."
  type        = string
  default     = "main"
}

variable "vpc_id" {
  description = "The ID of the VPC where resources will be deployed."
  type        = string
}

variable "public_subnet_ids" {
  description = "A list of public subnet IDs for the load balancer and EC2 instance."
  type        = list(string)
}

variable "load_balancer_sg_id" {
  description = "The ID of the security group for the Application Load Balancer."
  type        = string
}

variable "app_server_sg_id" {
  description = "The ID of the security group for the application server."
  type        = string
}

variable "instance_type" {
  description = "The EC2 instance type for the app server."
  type        = string
  default     = "t3.micro"
}

variable "key_name" {
  description = "The name of the EC2 key pair for SSH access."
  type        = string
}

variable "docker_image" {
  description = "The Docker image to run on the app server."
  type        = string
  default     = "2000023946/userauthmodule:latest"
}

variable "private_subnet_ids" {
  description = "A list of private subnet IDs for the application servers."
  type        = list(string)
}


// --- Database Variables ---
variable "writer_db_host" {
  description = "The endpoint for the writer database."
  type        = string
}

variable "reader_db_host" {
  description = "The endpoint for the reader database."
  type        = string
}

variable "database_name" {
  description = "The name of the database."
  type        = string
}

variable "database_user" {
  description = "The username for the database."
  type        = string
}

variable "db_password" {
  description = "The password for the database."
  type        = string
  sensitive   = true
}

variable "database_port" {
  description = "The port for the database."
  type        = number
}

// --- Optional Cache Variables ---
variable "redis_host" {
  description = "The endpoint for the Redis cache."
  type        = string
  default     = null
}

variable "redis_port" {
  description = "The port for the Redis cache."
  type        = number
  default     = null
}
