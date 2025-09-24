resource "aws_db_instance" "tf_rds" {
    allocated_storage    = 10
    engine               = "postgres" # CHANGED from mysql
    engine_version       = "16.3"                     # CHANGED to a modern, supported version
    instance_class       = "db.t3.micro"
    username             = "foo"
    password             = var.db_password
    parameter_group_name = "default.postgres16"       # CORRECTED to match the Postgres engine and version
    skip_final_snapshot  = true

    db_subnet_group_name   = aws_db_subnet_group.default.name
    vpc_security_group_ids = [aws_security_group.rds_sg.id]
}

# 3. Define the variable for the database password
variable "db_password" {
    description = "The password for the RDS database"
    type        = string
    sensitive   = true # Hides the password from Terraform output
    default = "password"
}

# 3. Define the variable for the database password
variable "db_port" {
  description = "PORT for db"
  type        = number
  sensitive   = true # Hides the password from Terraform output
  default = 5432
}