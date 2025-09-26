output "vpc_id" {
    description = "The ID of the created VPC."
    value       = module.network.vpc_id
}

output "public_subnet_ids" {
  description = "A list of the public subnet IDs from the network module."
  value       = module.network.public_subnet_ids
}

output "load_balancer_sg_id" {
  description = "The ID of the security group for the load balancer."
  value       = module.network.load_balancer_sg_id
}

output "app_server_sg_id" {
  description = "The ID of the security group for the application servers."
  value       = module.network.app_server_sg_id
}

output "private_subnet_ids" {
  description = "A list of the private subnet IDs from the network module."
  value       = module.network.private_subnet_ids
}

# --- Add this new output ---
output "cache_sg_id" {
  description = "The ID of the security group for the ElastiCache cluster."
  value       = module.network.aws_security_group.cache_sg.id
}

output "rds_sg_id" {
  description = "The ID of the security group for the ElastiCache cluster."
  value       = module.network.aws_security_group.rds_sg.id
}




