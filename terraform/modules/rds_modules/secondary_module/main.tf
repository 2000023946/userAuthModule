locals {
  name_prefix = "${var.project_name}-${var.environment}"
}

# 1. Create a DB Subnet Group in the SECONDARY region.
resource "aws_db_subnet_group" "secondary" {
  name       = "${local.name_prefix}-secondary-subnet-group"
  subnet_ids = var.private_subnet_ids
}

# 2. Create the SECONDARY cluster and add it to the global database.
# Notice there is no username/password. It gets all that from replication.
resource "aws_rds_cluster" "secondary" {
  # This is the magic line that makes it a replica of the primary.
  global_cluster_identifier = var.global_cluster_identifier

  cluster_identifier      = "${local.name_prefix}-secondary-cluster"
  engine                  = "aurora-postgresql" # Must match primary
  engine_version          = "16.2"              # Must match primary
  db_subnet_group_name    = aws_db_subnet_group.secondary.name
  vpc_security_group_ids  = var.rds_security_group_ids
  skip_final_snapshot     = true
}

# 3. Create a read-only instance for the secondary cluster.
resource "aws_rds_cluster_instance" "reader" {
  cluster_identifier = aws_rds_cluster.secondary.id
  identifier         = "${local.name_prefix}-secondary-reader"
  instance_class     = var.instance_class
  engine             = aws_rds_cluster.secondary.engine
  engine_version     = aws_rds_cluster.secondary.engine_version
}