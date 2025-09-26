# modules/network/outputs.tf

output "vpc_id" {
  description = "The ID of the created VPC."
  value       = aws_vpc.main.id
}

output "private_subnet_ids" {
  description = "A list of the private subnet IDs."
  value       = [for s in aws_subnet.private : s.id]
}

output "app_sg_id" {
  description = "The ID of the application security group."
  value       = aws_security_group.app_sg.id
}

output "rds_sg_id" {
  description = "The ID of the database security group."
  value       = aws_security_group.rds_sg.id
}

# --- Add this new output ---
output "cache_sg_id" {
  description = "The ID of the security group for the ElastiCache cluster."
  value       = aws_security_group.cache_sg.id
}
