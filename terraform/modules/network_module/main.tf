# modules/network/main.tf

# Use a data source to get the available AZs in the current region.
data "aws_availability_zones" "available" {
  state = "available"
}

# Use locals for consistent naming.
locals {
  name_prefix = "${var.project_name}-${var.environment}"
}

resource "aws_vpc" "main" {
  cidr_block = var.vpc_cidr_block
  tags = {
    Name = "${local.name_prefix}-vpc"
  }
}

# Create a private subnet for each CIDR block provided in the variable.
# It automatically places them in different Availability Zones.
resource "aws_subnet" "private" {
  # for_each creates a subnet for each item in the var.private_subnet_cidrs list.
  for_each          = toset(var.private_subnet_cidrs)
  vpc_id            = aws_vpc.main.id
  cidr_block        = each.key
  availability_zone = data.aws_availability_zones.available.names[index(var.private_subnet_cidrs, each.key)]

  tags = {
    Name = "${local.name_prefix}-private-subnet-${index(var.private_subnet_cidrs, each.key)}"
  }
}

resource "aws_security_group" "app_sg" {
  name        = "${local.name_prefix}-app-sg"
  description = "Allow web and SSH traffic"
  vpc_id      = aws_vpc.main.id

  ingress {
    from_port   = 80
    to_port     = 80
    protocol    = "tcp"
    cidr_blocks = ["0.0.0.0/0"] # Typically from a Load Balancer
  }
  ingress {
    from_port   = 22
    to_port     = 22
    protocol    = "tcp"
    cidr_blocks = var.ssh_ingress_cidr # Use the variable here!
  }
  egress {
    from_port   = 0
    to_port     = 0
    protocol    = "-1"
    cidr_blocks = ["0.0.0.0/0"]
  }
  tags = { Name = "${local.name_prefix}-app-sg" }
}

resource "aws_security_group" "rds_sg" {
  name            = "${local.name_prefix}-rds-sg"
  description     = "Allow inbound traffic from the app server to Postgres"
  vpc_id          = aws_vpc.main.id
  ingress {
    from_port       = 5432
    to_port         = 5432
    protocol        = "tcp"
    security_groups = [aws_security_group.app_sg.id]
  }
  tags = { Name = "${local.name_prefix}-rds-sg" }
}


# --- Add this new resource ---
resource "aws_security_group" "cache_sg" {
  name        = "${local.name_prefix}-cache-sg"
  description = "Allows inbound traffic to the ElastiCache cluster"
  vpc_id      = aws_vpc.main.id

  # Ingress rule: Allow the app servers to connect to Redis on port 6379
  ingress {
    from_port       = 6379
    to_port         = 6379
    protocol        = "tcp"
    security_groups = [aws_security_group.app_sg.id] # Assumes your app server SG is named 'app_sg'
  }

  tags = {
    Name = "${local.name_prefix}-cache-sg"
  }
}