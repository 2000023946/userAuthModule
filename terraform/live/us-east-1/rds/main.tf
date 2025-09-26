# live/us-east-1/main.tf

# Instantiate the Aurora Global Database
module "primary_rds" {
  # The source path should point to the directory of your RDS module
  source = "../../../modules/rds_modules/primary_module" # Make sure this path is correct

  # --- Naming & Tagging ---
  project_name = var.project_name
  environment  = var.environment

  # --- Network Configuration ---
  # Pass the private subnet IDs from the network module
  private_subnet_ids = module.network.private_subnet_ids
  
  # Pass the RDS security group ID from the network module (must be a list)
  rds_security_group_ids = [module.network.rds_sg_id]

  # --- Database Configuration ---
  db_password = var.db_password

  # --- ADD THIS LINE ---
  # Tell the module to create one read-replica instance in the cluster
  reader_instance_count = 1

}