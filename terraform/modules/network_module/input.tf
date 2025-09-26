# modules/network/variables.tf

variable "project_name" {
  description = "The name of the project, used for naming resources."
  type        = string
}

variable "environment" {
  description = "The deployment environment (e.g., dev, prod)."
  type        = string
}

variable "vpc_cidr_block" {
  description = "The CIDR block for the VPC."
  type        = string
  default     = "10.0.0.0/16"
}

variable "private_subnet_cidrs" {
  description = "A list of CIDR blocks for the private subnets."
  type        = list(string)
  # Example: ["10.0.2.0/24", "10.0.3.0/24"]
}

variable "ssh_ingress_cidr" {
  description = "CIDR blocks allowed for SSH access to the app server."
  type        = list(string)
  default     = ["0.0.0.0/0"] # WARNING: Should be locked down to your IP.
}

# --- Add this new variable ---

variable "public_subnet_cidrs" {
  description = "A list of CIDR blocks for the public subnets."
  type        = list(string)
  # Example: ["10.0.0.0/24", "10.0.1.0/24"]
}