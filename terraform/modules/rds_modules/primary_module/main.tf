locals {
  name_prefix        = "${var.project_name}-${var.environment}"
  global_cluster_id  = "${local.name_prefix}-global-db"
}

# 1. Create the Global Database container first.
resource "aws_rds_global_cluster" "main" {
  global_cluster_identifier = local.global_cluster_id
  engine                    = "aurora-postgresql"
  engine_version            = "16.2"
}

# 2. Create the DB Subnet Group in the primary region.
resource "aws_db_subnet_group" "main" {
  name       = "${local.name_prefix}-primary-subnet-group"
  subnet_ids = var.private_subnet_ids
}

# 3. Create the PRIMARY cluster and place it inside the global container.
resource "aws_rds_cluster" "primary" {
  # This makes it part of the global database
  global_cluster_identifier = aws_rds_global_cluster.main.id

  cluster_identifier       = "${local.name_prefix}-primary-cluster"
  engine                   = aws_rds_global_cluster.main.engine
  engine_version           = aws_rds_global_cluster.main.engine_version
  database_name            = var.db_name
  master_username          = var.db_username
  master_password          = var.db_password
  db_subnet_group_name     = aws_db_subnet_group.main.name
  
  # This line has been corrected
  vpc_security_group_ids   = var.rds_security_group_ids 
  
  skip_final_snapshot      = true
}

# 4. Create the writer instance for the primary cluster.
resource "aws_rds_cluster_instance" "writer" {
  cluster_identifier = aws_rds_cluster.primary.id
  identifier         = "${local.name_prefix}-primary-writer"
  instance_class     = var.instance_class
  engine             = aws_rds_cluster.primary.engine
  engine_version     = aws_rds_cluster.primary.engine_version
}

# --- Add this new resource at the end of the file ---

# 5. Create one or more read-replica instances for the primary cluster.
resource "aws_rds_cluster_instance" "reader" {
  # This creates as many readers as you specify in the variable
  count = var.reader_instance_count

  cluster_identifier = aws_rds_cluster.primary.id
  identifier         = "${local.name_prefix}-primary-reader-${count.index}"
  instance_class     = var.instance_class
  engine             = aws_rds_cluster.primary.engine
  engine_version     = aws_rds_cluster.primary.engine_version
}
