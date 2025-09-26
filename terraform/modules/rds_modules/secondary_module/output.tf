output "secondary_cluster_reader_endpoint" {
  description = "The endpoint for read-only traffic in the secondary region."
  value       = aws_rds_cluster.secondary.reader_endpoint
}