# This file defines the core network infrastructure.

# 1. The Virtual Private Cloud (VPC) - your isolated section of AWS.
resource "aws_vpc" "main" {
  cidr_block = "10.0.0.0/16"
  tags = {
    Name = "my-vpc"
  }
}

# 2. Subnets - the different zones within your VPC.
# Public Subnet for web-facing resources like the EC2 instance.
resource "aws_subnet" "main" {
  vpc_id                  = aws_vpc.main.id
  cidr_block              = "10.0.1.0/24"
  map_public_ip_on_launch = true
  availability_zone       = "us-east-1a" # Specific AZ for placement
  tags = {
    Name = "my-public-subnet"
  }
}

# Private subnets for backend resources like the database and cache.
# We need at least two in different AZs for high availability.
resource "aws_subnet" "private_a" {
  vpc_id            = aws_vpc.main.id
  cidr_block        = "10.0.2.0/24"
  availability_zone = "us-east-1a"
  tags = {
    Name = "my-private-subnet-a"
  }
}

resource "aws_subnet" "private_b" {
  vpc_id            = aws_vpc.main.id
  cidr_block        = "10.0.3.0/24"
  availability_zone = "us-east-1b"
  tags = {
    Name = "my-private-subnet-b"
  }
}

# 3. Security Groups - the virtual firewalls for your resources.
# Firewall for the application server.
resource "aws_security_group" "app_sg" {
  name        = "app-sg"
  description = "Allow web and SSH traffic"
  vpc_id      = aws_vpc.main.id

  ingress {
    from_port   = 80
    to_port     = 80
    protocol    = "tcp"
    cidr_blocks = ["0.0.0.0/0"] # In a real setup, this would be locked down to a load balancer
  }
  ingress {
    from_port   = 22
    to_port     = 22
    protocol    = "tcp"
    cidr_blocks = ["0.0.0.0/0"] # WARNING: Open to the world. Lock this down to your IP address.
  }
  egress {
    from_port   = 0
    to_port     = 0
    protocol    = "-1"
    cidr_blocks = ["0.0.0.0/0"]
  }
}

# Firewall for the Aurora database.
resource "aws_security_group" "rds_sg" {
  name        = "rds-sg"
  description = "Allow inbound traffic from the app server to Postgres"
  vpc_id      = aws_vpc.main.id

  # Only allows connections from the application server security group on the Postgres port.
  ingress {
    from_port       = 5432
    to_port         = 5432
    protocol        = "tcp"
    security_groups = [aws_security_group.app_sg.id]
  }
}

# Firewall for the Redis cache.
resource "aws_security_group" "cache_sg" {
  name        = "cache-sg"
  description = "Allow inbound traffic from the app server to Redis"
  vpc_id      = aws_vpc.main.id

  # Only allows connections from the application server security group on the Redis port.
  ingress {
    from_port       = 6379
    to_port         = 6379
    protocol        = "tcp"
    security_groups = [aws_security_group.app_sg.id]
  }
}
