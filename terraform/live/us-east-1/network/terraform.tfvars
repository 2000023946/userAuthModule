# --- Naming and Identification ---
project_name = "webapp"
environment  = "prod"

# --- Network Configuration ---
vpc_cidr_block = "10.1.0.0/16"
private_subnet_cidrs = ["10.1.1.0/24", "10.1.2.0/24"]

# --- Security Configuration ---
# IMPORTANT: Replace with your actual public IP address for security.
ssh_ingress_cidr = ["YOUR_IP_ADDRESS/32"]
