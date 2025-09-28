# --- CACHE MODULE (New) ---
# This module creates the ElastiCache for Redis cluster.
# It uses the outputs from the network module for its configuration.
module "cache" {
  source = "../../modules/cache_module"

  # Pass through common variables
  project_name = var.project_name
  environment  = var.environment

  # Connect to the network created by the network module
  private_subnet_ids       = module.network.private_subnet_ids
  cache_security_group_ids = [module.network.cache_sg_id]

}