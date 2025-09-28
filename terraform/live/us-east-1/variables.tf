variable "project_name" {
  description = "The name of the project."
  type        = string
}

variable "environment" {
  description = "The deployment environment (e.g., dev, prod)."
  type        = string
}

variable "vpc_cidr_block" {
  description = "The CIDR block for the VPC."
  type        = string
}

variable "private_subnet_cidrs" {
  description = "A list of CIDR blocks for the private subnets."
  type        = list(string)
}

# live/us-east-1/variables.tf

variable "public_subnet_cidrs" {
  description = "A list of CIDR blocks for the public subnets."
  type        = list(string)
}

variable "ssh_ingress_cidr" {
  description = "CIDR blocks allowed for SSH access."
  type        = list(string)
}

variable "db_password" {
  description = "The master password for the database cluster."
  type        = string
  sensitive   = true
}

variable "key_name" {
  description = "The name of the EC2 key pair for SSH access."
  type        = string
}

