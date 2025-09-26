# live/us-east-1/main.tf

# Instantiate the ElastiCache Redis cluster
module "cache" {
  # The source path should point to the directory of your cache module
  source = "../../../modules/cache"

  # Pass in the required variables
  project_name             = var.project_name
  environment              = var.environment
  private_subnet_ids       = module.network.private_subnet_ids
  cache_security_group_ids = [module.network.cache_sg_id] # This is a new required output from your network module

  # You can override the defaults if needed, for example:
  # instance_type = "cache.t3.medium"
}