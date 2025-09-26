// Instantiate the app server and load balancer
module "app_server_lb" {
  source = "../../../modules/server_module"

  vpc_id                = module.network.vpc_id
  public_subnet_ids     = module.network.public_subnet_ids
  private_subnet_ids    = module.network.private_subnet_ids // <-- FIX: Get this from the network module
  load_balancer_sg_id   = module.network.load_balancer_sg_id
  app_server_sg_id      = module.network.app_server_sg_id
  key_name              = var.key_name

  // Pass outputs from the RDS module as inputs here
  writer_db_host        = module.rds.writer_endpoint
  reader_db_host        = module.rds.reader_endpoint
  database_name         = module.rds.database_name
  database_user         = module.rds.database_user
  db_password           = module.primary_rds.db_password
  database_port         = module.rds.database_port
}