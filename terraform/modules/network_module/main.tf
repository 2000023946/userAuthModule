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

# =============================================================================
# NETWORKING FOR PUBLIC SUBNETS
# =============================================================================

# An Internet Gateway is required for resources in public subnets to reach the internet.
resource "aws_internet_gateway" "main" {
  vpc_id = aws_vpc.main.id
  tags   = { Name = "${local.name_prefix}-igw" }
}

# Create a public subnet for each CIDR block provided.
resource "aws_subnet" "public" {
  for_each                = toset(var.public_subnet_cidrs)
  vpc_id                  = aws_vpc.main.id
  cidr_block              = each.key
  availability_zone       = data.aws_availability_zones.available.names[index(var.public_subnet_cidrs, each.key)]
  map_public_ip_on_launch = true # Instances launched here get a public IP.

  tags = {
    Name = "${local.name_prefix}-public-subnet-${index(var.public_subnet_cidrs, each.key)}"
  }
}

# A route table tells the public subnets how to reach the Internet Gateway.
resource "aws_route_table" "public" {
  vpc_id = aws_vpc.main.id

  route {
    cidr_block = "0.0.0.0/0"
    gateway_id = aws_internet_gateway.main.id
  }

  tags = { Name = "${local.name_prefix}-public-rt" }
}

# Associate the route table with our public subnets.
resource "aws_route_table_association" "public" {
  for_each       = aws_subnet.public
  subnet_id      = each.value.id
  route_table_id = aws_route_table.public.id
}

# =============================================================================
# NETWORKING FOR PRIVATE SUBNETS
# =============================================================================

# Create a private subnet for each CIDR block provided.
resource "aws_subnet" "private" {
  for_each          = toset(var.private_subnet_cidrs)
  vpc_id            = aws_vpc.main.id
  cidr_block        = each.key
  availability_zone = data.aws_availability_zones.available.names[index(var.private_subnet_cidrs, each.key)]

  tags = {
    Name = "${local.name_prefix}-private-subnet-${index(var.private_subnet_cidrs, each.key)}"
  }
}

# =============================================================================
# SECURITY GROUPS
# =============================================================================

# NEW: Security group for the public-facing Load Balancer
resource "aws_security_group" "lb_sg" {
  name        = "${local.name_prefix}-lb-sg"
  description = "Allow HTTP inbound traffic to the load balancer"
  vpc_id      = aws_vpc.main.id

  ingress {
    from_port   = 80
    to_port     = 80
    protocol    = "tcp"
    cidr_blocks = ["0.0.0.0/0"] # Allow traffic from anywhere on the internet
  }

  egress {
    from_port   = 0
    to_port     = 0
    protocol    = "-1"
    cidr_blocks = ["0.0.0.0/0"]
  }
  tags = { Name = "${local.name_prefix}-lb-sg" }
}

# Security group for the application servers
resource "aws_security_group" "app_sg" {
  name        = "${local.name_prefix}-app-sg"
  description = "Allow traffic from the LB and SSH"
  vpc_id      = aws_vpc.main.id

  # --- CRITICAL SECURITY IMPROVEMENT ---
  # Only allow web traffic from the load balancer, not the entire internet.
  ingress {
    from_port       = 80
    to_port         = 80
    protocol        = "tcp"
    security_groups = [aws_security_group.lb_sg.id]
  }
  
  ingress {
    from_port   = 22
    to_port     = 22
    protocol    = "tcp"
    cidr_blocks = var.ssh_ingress_cidr
  }
  
  egress {
    from_port   = 0
    to_port     = 0
    protocol    = "-1"
    cidr_blocks = ["0.0.0.0/0"]
  }
  tags = { Name = "${local.name_prefix}-app-sg" }
}

# Security group for the RDS database
resource "aws_security_group" "rds_sg" {
  name        = "${local.name_prefix}-rds-sg"
  description = "Allow inbound traffic from the app server to Postgres"
  vpc_id      = aws_vpc.main.id
  
  ingress {
    from_port       = 5432
    to_port         = 5432
    protocol        = "tcp"
    security_groups = [aws_security_group.app_sg.id]
  }
  tags = { Name = "${local.name_prefix}-rds-sg" }
}

# Security group for the ElastiCache cluster
resource "aws_security_group" "cache_sg" {
  name        = "${local.name_prefix}-cache-sg"
  description = "Allows inbound traffic from the app server to Redis"
  vpc_id      = aws_vpc.main.id

  ingress {
    from_port       = 6379
    to_port         = 6379
    protocol        = "tcp"
    security_groups = [aws_security_group.app_sg.id]
  }
  tags = { Name = "${local.name_prefix}-cache-sg" }
}