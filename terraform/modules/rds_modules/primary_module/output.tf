output "writer_endpoint" {
  description = "The connection endpoint for the writer instance."
  value       = aws_rds_cluster.primary.endpoint
}

output "reader_endpoint" {
  description = "The connection endpoint for the read-only instances."
  value       = aws_rds_cluster.primary.reader_endpoint
}

output "database_name" {
  description = "The name of the database."
  value       = aws_rds_cluster.primary.database_name
}

output "database_user" {
  description = "The master username for the database."
  value       = aws_rds_cluster.primary.master_username
}

output "database_port" {
  description = "The port the database is listening on."
  value       = aws_rds_cluster.primary.port
}

output "global_cluster_id" {
  description = "The unique identifier for the Aurora Global Cluster."
  value       = aws_rds_global_cluster.main.id
}