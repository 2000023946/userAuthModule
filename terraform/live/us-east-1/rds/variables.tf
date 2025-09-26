# live/us-east-1/variables.tf

variable "project_name" {
  description = "The overall name of the project."
  type        = string
}

variable "environment" {
  description = "The deployment environment (e.g., dev, staging, prod)."
  type        = string
}

variable "db_password" {
  description = "The master password for the database cluster. Should be managed securely."
  type        = string
  sensitive   = true
}