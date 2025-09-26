terraform {
  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = "~> 6.0"
    }
  }
}

# Configure the AWS Provider
provider "aws" {
  region = "us-east-2"
  alias = "us_east_2"
}

# Provider for our Primary Region (e.g., US East 1)
provider "aws" {
  region = "us-east-1"
  alias  = "us_east_1"
}

# Provider for our Secondary Region (e.g., US West 2)
provider "aws" {
  region = "us-west-2"
  alias  = "us_west_2"
}

# Provider for our Secondary Region (e.g., US West 2)
provider "aws" {
  region = "us-west-1"
  alias  = "us_west_1"
}
