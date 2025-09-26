# This file creates a single, highly-available Aurora database cluster in one region.
# This represents the foundational "library" from our analogy.

# --- Database Network Configuration ---
# This subnet group tells the Aurora cluster which private subnets its
# "Worker Instances" are allowed to be placed in. It must span at least two AZs.
resource "aws_db_subnet_group" "east_1" {
  provider   = aws.us_east_1 # Provider is only needed in multi-region setups
  name       = "main-db-subnet-group"
  subnet_ids = [aws_subnet.private_a.id, aws_subnet.private_b.id] # Assumes these subnets exist
  tags = {
    Name = "My DB Subnet Group"
  }
}


# --- The "Shared Storage" and Regional Compute Cluster (The Library) ---
# This is the core resource. It creates the magical, central filing system
# (the shared storage volume) that is replicated 6 times across 3 AZs.
# It also acts as the "Branch Office" that manages the worker instances.
resource "aws_rds_cluster" "main" {
  provider                 = aws.us_east_1
  cluster_identifier       = "app-primary-cluster"
  engine                   = "aurora-postgresql"
  engine_version           = "16.2"
  database_name            = "userauthdb"
  master_username          = "admin"
  master_password          = var.db_password
  db_subnet_group_name     = aws_db_subnet_group.east_1.name
  vpc_security_group_ids   = [aws_security_group.rds_sg.id] # Assumes this SG exists
  skip_final_snapshot      = true
  # Note: Aurora is not part of the AWS Free Tier.
}

# --- The "Worker Instance" (The Librarian) ---
# A cluster needs at least one worker to be useful. This resource creates the
# actual server with CPU and RAM that connects to the Shared Storage Volume
# to execute queries. We link it to the cluster with 'cluster_identifier'.
resource "aws_rds_cluster_instance" "main" {
  provider           = aws.us_east_1
  cluster_identifier = aws_rds_cluster.main.id
  instance_class     = "db.t3.medium"
  engine             = aws_rds_cluster.main.engine
  engine_version     = aws_rds_cluster.main.engine_version
}


# --- The "Replica Worker Instance" (The Read-Only Librarian) ---
# This is a second instance added to the SAME cluster. It automatically becomes
# a read replica. It connects to the same shared storage but can only perform
# read operations. The cluster's READER endpoint will now load balance
# read requests between this instance and the primary "main" instance.
resource "aws_rds_cluster_instance" "replica" {
  provider           = aws.us_east_1
  cluster_identifier = aws_rds_cluster.main.id
  instance_class     = "db.t3.medium"
  engine             = aws_rds_cluster.main.engine
  engine_version     = aws_rds_cluster.main.engine_version
}


