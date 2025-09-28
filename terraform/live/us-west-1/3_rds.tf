
# --- SECONDARY DATABASE (READ-REPLICA) ---
module "database_secondary" {
  providers = {
    aws = aws.secondary
  }
  source = "../../modules/rds_modules/secondary_module"

  project_name              = var.project_name
  environment               = "${var.environment}-dr"
  instance_class            = var.secondary_db_instance_class
  global_cluster_identifier = module.database_primary.global_cluster_id
  private_subnet_ids        = module.network_secondary.private_subnet_ids
  rds_security_group_ids    = [module.network_secondary.rds_sg_id]
}
