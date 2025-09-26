# live/us-east-1/terraform.tfvars

project_name = "webapp"
environment  = "prod"
db_password = "password"#fix later
# db_password should be set securely, for example via an environment variable (TF_VAR_db_password=...) 
# or fetched from a secrets manager, not stored in this file.