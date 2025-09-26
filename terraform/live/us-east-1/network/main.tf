// live/us-east-1/main.tf

// Configure the AWS provider for this specific region
provider "aws" {
  region = "us-east-1"
}

// Instantiate the network for us-east-1
module "network" {
  # The source path should point to the directory containing your network module files.
  source = "../../../modules/network_module"

  # --- Naming and Identification ---
  # These variables are used to create a consistent naming prefix (e.g., "webapp-prod")
  # for all resources created by this module (VPC, Subnets, Security Groups).
  project_name = var.project_name
  environment  = var.environment

  # --- Network Configuration ---
  # The main CIDR block for the entire VPC.
  vpc_cidr_block = var.vpc_cidr_block

  # Define at least two private subnets for high availability. The module will
  # automatically place them in different Availability Zones for you.
  # These CIDRs must be within the main vpc_cidr_block.
  private_subnet_cidrs = var.private_subnet_cidrs

  # --- Security Configuration ---
  # IMPORTANT: For security, you should restrict SSH access to only your IP address.
  # Replace the placeholder below with your actual IP.
  # You can find it by searching "what is my IP" on Google.
  ssh_ingress_cidr = var.ssh_ingress_cidr
}
