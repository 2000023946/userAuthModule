project_name         = "webapp"
environment          = "prod"
key_name             = "my-aws-key-pair-name"
vpc_cidr_block       = "10.1.0.0/16"
private_subnet_cidrs = ["10.1.1.0/24", "10.1.2.0/24"]
public_subnet_cidrs = ["10.1.0.0/24", "10.1.4.0/24"]
ssh_ingress_cidr     = ["YOUR_IP_ADDRESS/32"] # <-- IMPORTANT: Change this!

db_password = "passwasdfo298poikajsd89ford"

# db_password should be set securely via an environment variable, not here.
# Run this in your terminal before applying:
# export TF_VAR_db_password="your-secure-password-here"