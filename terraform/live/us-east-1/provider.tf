terraform {
  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = "~> 5.0"
    }
  }

  # Recommended: Configure a remote backend to store your state file
  # backend "s3" {
  #   bucket = "your-terraform-state-bucket"
  #   key    = "live/us-east-1/terraform.tfstate"
  #   region = "us-east-1"
  # }
}

provider "aws" {
  region = "us-east-1"
}