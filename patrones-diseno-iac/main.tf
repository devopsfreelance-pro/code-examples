terraform {
  required_version = ">= 1.5"

  required_providers {
    local = {
      source  = "hashicorp/local"
      version = "~> 2.5"
    }
  }
}

# Composición: la raíz solo pasa parámetros al módulo reutilizable.
# El mismo módulo "network" se invoca con distintos tfvars según el
# entorno (dev.tfvars / prod.tfvars), sin duplicar código: patrón de
# "Módulos Reutilizables" + "Entornos Parametrizados" combinados.
module "network" {
  source = "./modules/network"

  environment        = var.environment
  vpc_cidr           = var.vpc_cidr
  azs                = var.azs
  instance_sizes     = var.instance_sizes
  enable_nat_gateway = var.enable_nat_gateway
}
