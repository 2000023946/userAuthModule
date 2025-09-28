
module "network" {
  source = "../../modules/network_module"

  # Pass values from the root variables to the module's variables
  project_name          = var.project_name
  environment           = var.environment
  vpc_cidr_block        = var.vpc_cidr_block
  public_subnet_cidrs   = var.public_subnet_cidrs
  private_subnet_cidrs  = var.private_subnet_cidrs
  ssh_ingress_cidr      = ["${var.my_ip}/32"]
}