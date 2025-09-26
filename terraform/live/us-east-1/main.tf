# Call the network module first, as everything depends on it
# module "network" {
#   source = "./network" # Assumes 'network' is a directory inside us-east-1
  
#   # Pass any variables the network module needs
#   project_name = var.project_name
#   environment  = var.environment
# }

# # Call the RDS module, giving it info from the network module
# module "rds" {
#   source = "./rds"

#   project_name           = var.project_name
#   environment            = var.environment
#   private_subnet_ids     = module.network.private_subnet_ids
#   rds_security_group_ids = [module.network.rds_sg_id]
#   db_password            = var.db_password
# }

# # Call the Cache module, also giving it info from the network module
# module "cache" {
#   source = "./cache"

#   project_name             = var.project_name
#   environment              = var.environment
#   private_subnet_ids       = module.network.private_subnet_ids
#   cache_security_group_ids = [module.network.cache_sg_id]
# }

# # Finally, call the Server module, giving it info from all other modules
# module "server" {
#   source = "./server"

#   project_name           = var.project_name
#   environment            = var.environment
#   public_subnet_ids      = module.network.public_subnet_ids
#   private_subnet_ids     = module.network.private_subnet_ids
#   app_server_sg_id       = module.network.app_server_sg_id
#   load_balancer_sg_id    = module.network.load_balancer_sg_id
#   key_name               = var.key_name

#   # Pass database and cache connection details
#   writer_db_host = module.rds.writer_endpoint
#   reader_db_host = module.rds.reader_endpoint
#   redis_host     = module.cache.primary_endpoint_address
#   # ... other variables like db_name, db_user, etc.
# }