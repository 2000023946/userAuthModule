variable "project_name" {
  type        = string
  description = "The name of the project."
}

variable "environment" {
  type        = string
  description = "The deployment environment (e.g., prod, dev)."
}

variable "db_password" {
  type        = string
  description = "Password for the database."
  sensitive   = true
}

variable "key_name" {
  type        = string
  description = "Name of the EC2 key pair for SSH access."
}