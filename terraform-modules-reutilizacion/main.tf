terraform {
  required_version = ">= 1.5.0"

  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = "~> 5.0"
    }
  }
}

# Provider apuntando a LocalStack (sin credenciales reales, sin costo)
provider "aws" {
  region                      = "us-east-1"
  access_key                  = "test"
  secret_key                  = "test"
  skip_credentials_validation = true
  skip_metadata_api_check     = true
  skip_requesting_account_id  = true

  endpoints {
    ec2 = "http://localhost:4566"
  }
}

# Mismo módulo reutilizado dos veces con distintos parámetros:
# esto es lo que demuestra el post - un módulo, múltiples consumidores.
module "network_dev" {
  source = "./modules/vpc-network"

  environment         = "dev"
  vpc_cidr            = "10.0.0.0/16"
  availability_zones  = ["us-east-1a", "us-east-1b"]
  public_subnet_cidrs = ["10.0.1.0/24", "10.0.2.0/24"]

  common_tags = {
    Project = "code-examples"
    Owner   = "devopsfreelance-pro"
  }
}

module "network_prod" {
  source = "./modules/vpc-network"

  environment         = "prod"
  vpc_cidr            = "10.100.0.0/16"
  availability_zones  = ["us-east-1a", "us-east-1b"]
  public_subnet_cidrs = ["10.100.1.0/24", "10.100.2.0/24"]

  common_tags = {
    Project = "code-examples"
    Owner   = "devopsfreelance-pro"
  }
}

output "dev_vpc_id" {
  description = "ID de la VPC del entorno dev"
  value       = module.network_dev.vpc_id
}

output "dev_public_subnet_ids" {
  description = "IDs de subnets públicas del entorno dev"
  value       = module.network_dev.public_subnet_ids
}

output "prod_vpc_id" {
  description = "ID de la VPC del entorno prod"
  value       = module.network_prod.vpc_id
}

output "prod_public_subnet_ids" {
  description = "IDs de subnets públicas del entorno prod"
  value       = module.network_prod.public_subnet_ids
}
