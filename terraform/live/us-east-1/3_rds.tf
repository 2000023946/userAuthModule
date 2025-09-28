# --- DATABASE MODULE (New) ---
# This module creates the primary Aurora Global Database cluster.
module "database" {
  source = "../../modules/rds_modules/primary_module"

  # Pass through common and database-specific variables
  project_name          = var.project_name
  environment           = var.environment
  db_name               = var.db_name
  db_username           = var.db_username
  db_password           = var.db_password
  instance_class        = var.db_instance_class
  reader_instance_count = var.db_reader_instance_count

  # Connect to the network created by the network module
  private_subnet_ids     = module.network.private_subnet_ids
  rds_security_group_ids = [module.network.rds_sg_id]
}