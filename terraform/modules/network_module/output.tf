output "vpc_id" {
  description = "The ID of the VPC."
  value       = aws_vpc.main.id
}

output "public_subnet_ids" {
  description = "List of public subnet IDs."
  # Correct syntax for a resource created with for_each
  value       = values(aws_subnet.public)[*].id
}

output "private_subnet_ids" {
  description = "List of private subnet IDs."
  # Correct syntax for a resource created with for_each
  value       = values(aws_subnet.private)[*].id
}

output "load_balancer_sg_id" {
  description = "The ID of the load balancer's security group."
  value       = aws_security_group.lb_sg.id
}

output "app_server_sg_id" {
  description = "The ID of the app server's security group."
  value       = aws_security_group.app_sg.id
}

output "rds_sg_id" {
  description = "The ID of the RDS security group."
  # FIX: Your resource name is "rds_sg", not "rds"
  value       = aws_security_group.rds_sg.id
}

output "cache_sg_id" {
  description = "The ID of the ElastiCache security group."
  # FIX: Your resource name is "cache_sg", not "cache"
  value       = aws_security_group.cache_sg.id
}