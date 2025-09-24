# --- Update subnet groups to use BOTH private subnets ---

resource "aws_db_subnet_group" "default" {
  name       = "main-db-subnet-group"
  subnet_ids = [aws_subnet.private_a.id, aws_subnet.private_b.id]

  tags = {
    Name = "My DB subnet group"
  }
}

resource "aws_elasticache_subnet_group" "default" {
  name       = "main-cache-subnet-group"
  subnet_ids = [aws_subnet.private_a.id, aws_subnet.private_b.id]

  tags = {
    Name = "My ElastiCache subnet group"
  }
}