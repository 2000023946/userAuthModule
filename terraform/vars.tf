# This file declares the input variables for your configuration,
# allowing you to pass in sensitive values securely.

variable "db_password" {
  description = "The password for the RDS database"
  type        = string
  sensitive   = true # Hides the password from Terraform output
  default = "1234"
}

variable "cache_port" {
  description = "The port for the Redis cache"
  type        = number
  default     = 6379
}
