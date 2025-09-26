output "global_cluster_identifier" {
  description = "The ID of the global database container, needed by secondary clusters."
  value       = aws_rds_global_cluster.main.id
}

output "primary_cluster_writer_endpoint" {
  description = "The endpoint for the writer instance in the primary region."
  value       = aws_rds_cluster.primary.endpoint
}

output "reader_endpoint" {
  description = "The connection endpoint for the read-only replica instances."
  value       = aws_rds_cluster.primary.reader_endpoint
}