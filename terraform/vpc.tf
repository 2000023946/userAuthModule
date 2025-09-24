# Public Subnet for the EC2 Instance
resource "aws_subnet" "main" {
  vpc_id                  = aws_vpc.main.id
  cidr_block              = "10.0.1.0/24"
  map_public_ip_on_launch = true
  availability_zone       = "us-east-2a" 

  tags = {
    Name = "my-public-subnet"
  }
}


# --- Create two private subnets in different Availability Zones ---

# Private Subnet in AZ "a"
resource "aws_subnet" "private_a" {
  vpc_id            = aws_vpc.main.id
  cidr_block        = "10.0.2.0/24"
  availability_zone = "us-east-2a"

  tags = {
    Name = "my-private-subnet-a"
  }
}

# Private Subnet in AZ "b"
resource "aws_subnet" "private_b" {
  vpc_id            = aws_vpc.main.id
  cidr_block        = "10.0.3.0/24"
  availability_zone = "us-east-2b"

  tags = {
    Name = "my-private-subnet-b"
  }
}

# 1. Define the main VPC (the "house")
resource "aws_vpc" "main" {
  cidr_block = "10.0.0.0/16" # The overall IP address range for your entire network

  tags = {
    Name = "my-vpc"
  }
}

# 2. Define the Security Group (the "firewall")
resource "aws_security_group" "app_sg" {
  name        = "app-sg"
  description = "Allow web and SSH traffic"
  vpc_id      = aws_vpc.main.id # Place the firewall in our main VPC

  ingress {
    from_port   = 80
    to_port     = 80
    protocol    = "tcp"
    cidr_blocks = ["0.0.0.0/0"] # Allow HTTP traffic from anywhere
  }

  ingress {
    from_port   = 22
    to_port     = 22
    protocol    = "tcp"
    cidr_blocks = ["0.0.0.0/0"] # Allow SSH traffic from anywhere (for management)
  }

  egress {
    from_port   = 0
    to_port     = 0
    protocol    = "-1"
    cidr_blocks = ["0.0.0.0/0"] # Allow all outbound traffic
  }

  tags = {
    Name = "app-sg"
  }
}

# 3. Create a dedicated security group (firewall) for the cache 🛡️
resource "aws_security_group" "cache_sg" {
  name        = "cache-sg"
  description = "Allow inbound traffic from the app server"
  vpc_id      = aws_vpc.main.id

  # This rule allows your app server to talk to your cache on the Redis port (6379)
  ingress {
    from_port       = var.cache_port
    to_port         = var.cache_port
    protocol        = "tcp"
    security_groups = [aws_security_group.app_sg.id] # CRUCIAL: Only allows access from your app
  }
}

# 3. Create a dedicated security group (firewall) for the cache 🛡️
resource "aws_security_group" "rds_sg" {
  name        = "rds-sg"
  description = "Allow inbound traffic from the app server"
  vpc_id      = aws_vpc.main.id

  # This rule allows your app server to talk to your DB
  ingress {
    from_port       = var.db_port
    to_port         = var.db_port
    protocol        = "tcp"
    security_groups = [aws_security_group.app_sg.id] # CRUCIAL: Only allows access from your app
  }
}


