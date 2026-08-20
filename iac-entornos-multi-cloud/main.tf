terraform {
  required_version = ">= 1.5.0"

  required_providers {
    local = {
      source  = "hashicorp/local"
      version = "~> 2.5"
    }
  }
}

variable "project" {
  description = "Nombre corto del proyecto, usado como prefijo de naming."
  type        = string
  default     = "demo"
}

variable "environment" {
  description = "Entorno (dev, staging, production)."
  type        = string
  default     = "production"
}

# Un mismo modulo de "red virtual" instanciado tres veces, una por
# proveedor. El codigo consumidor (este archivo) es agnostico de las
# particularidades de cada nube: cada submodulo se encarga de normalizar
# nombres y tags segun las reglas del proveedor correspondiente.
module "network_aws" {
  source = "./modules/network/aws"

  project     = var.project
  environment = var.environment
  cidr_block  = "10.0.0.0/16"
  region      = "us-east-1"
}

module "network_azure" {
  source = "./modules/network/azure"

  project       = var.project
  environment   = var.environment
  address_space = "10.1.0.0/16"
  location      = "eastus"
}

module "network_gcp" {
  source = "./modules/network/gcp"

  project     = var.project
  environment = var.environment
  cidr_block  = "10.2.0.0/16"
  region      = "us-central1"
}

output "resumen_multi_cloud" {
  description = "Nombre normalizado y tags de la red en cada proveedor."
  value = {
    aws   = { name = module.network_aws.name, tags = module.network_aws.tags }
    azure = { name = module.network_azure.name, tags = module.network_azure.tags }
    gcp   = { name = module.network_gcp.name, tags = module.network_gcp.tags }
  }
}
