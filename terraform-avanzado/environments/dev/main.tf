## Entorno "dev": estado separado (backend local propio) y valores propios
## en terraform.tfvars, consumiendo el MISMO módulo que "prod".
## Esto ilustra la separación de estado por entorno que describe el post
## (sección "Gestión de Múltiples Entornos").

terraform {
  required_version = ">= 1.5"

  backend "local" {
    path = "dev.tfstate"
  }
}

module "app_stack" {
  source = "../../modules/app_stack"

  environment       = var.environment
  application_name  = var.application_name
  instance_type     = var.instance_type
  min_capacity      = var.min_capacity
  max_capacity      = var.max_capacity
  enable_monitoring = var.enable_monitoring
  enable_backup     = var.enable_backup
  backup_retention  = var.backup_retention

  tags = {
    Component = "api-gateway"
    Tier      = "application"
  }
}

variable "environment" {
  type    = string
  default = "dev"
}

variable "application_name" {
  type    = string
  default = "api-gateway"
}

variable "instance_type" {
  type    = string
  default = "t3.micro"
}

variable "min_capacity" {
  type    = number
  default = 1
}

variable "max_capacity" {
  type    = number
  default = 2
}

variable "enable_monitoring" {
  type    = bool
  default = true
}

variable "enable_backup" {
  type    = bool
  default = false
}

variable "backup_retention" {
  type    = number
  default = 7
}

output "config_path" {
  value = module.app_stack.config_path
}

output "applied_tags" {
  value = module.app_stack.applied_tags
}

output "capacity_range" {
  value = module.app_stack.capacity_range
}
