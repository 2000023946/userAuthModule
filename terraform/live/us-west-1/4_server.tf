module "application_server" {
  source = "../../modules/server_module"

  # Naming and instance configuration
  name_prefix   = var.project_name
  instance_type = var.app_server_instance_type
  key_name      = var.ec2_key_pair_name

  # Network inputs from the Network Module
  vpc_id                = module.network.vpc_id
  public_subnet_ids     = module.network.public_subnet_ids
  private_subnet_ids    = module.network.private_subnet_ids
  load_balancer_sg_id   = module.network.load_balancer_sg_id
  app_server_sg_id      = module.network.app_server_sg_id

  # Database inputs from the Database Module
  writer_db_host = module.database.writer_endpoint
  reader_db_host = module.database.reader_endpoint
  database_name  = module.database.database_name
  database_user  = module.database.database_user
  database_port  = module.database.database_port
  db_password    = var.db_password # Pass the sensitive password from the root variable

  # Cache inputs from the Cache Module
  redis_host = module.cache.primary_endpoint_address
  redis_port = module.cache.port
}