# -----------------------------------------------------------------------------
# GLOBAL & PROJECT SETTINGS
# -----------------------------------------------------------------------------
# These values will be used as prefixes for naming all resources.
project_name = "my-cool-project"
environment  = "dev"
aws_region   = "us-east-1"


# -----------------------------------------------------------------------------
# NETWORKING VALUES
# -----------------------------------------------------------------------------
# You can keep the defaults or customize your IP ranges here.
# vpc_cidr_block       = "10.0.0.0/16"
# public_subnet_cidrs  = ["10.0.0.0/24", "10.0.1.0/24"]
# private_subnet_cidrs = ["10.0.2.0/24", "10.0.3.0/24"]

# ⚠️ IMPORTANT: Replace with your actual public IP address for secure SSH access.
# You can find it by searching "what is my IP" in Google.
my_ip = "54.98.12.34"


# -----------------------------------------------------------------------------
# DATABASE VALUES
# -----------------------------------------------------------------------------
# You can customize the DB name and user if you wish.
# db_name     = "webappdb"
# db_username = "dbadmin"

# 🔒 IMPORTANT: Use a strong, unique password. For production, use a secrets manager.
db_password = "YourSuperSecret&SecureP@ssw0rd123!"

# You can change the database size and number of read replicas.
# db_instance_class        = "db.t3.medium"
# db_reader_instance_count = 1


# -----------------------------------------------------------------------------
# APPLICATION SERVER VALUES
# -----------------------------------------------------------------------------
# You can change the application server size if needed.
# app_server_instance_type = "t3.micro"

# ⚠️ IMPORTANT: Replace with the name of an EC2 Key Pair that exists in your
# AWS account in the specified region (us-east-1).
ec2_key_pair_name = "your-key-pair-name"

# The Docker image to be pulled from Docker Hub for the application.
docker_image = "2000023946/auth-app:latest"

