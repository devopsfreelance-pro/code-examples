## Entorno "production": mismo módulo que "dev", backend local propio
## (estado separado) y valores más exigentes (más capacidad, backup
## habilitado con retención de 30 días), igual que en el ejemplo del post.

terraform {
  required_version = ">= 1.5"

  backend "local" {
    path = "prod.tfstate"
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
  default = "production"
}

variable "application_name" {
  type    = string
  default = "api-gateway"
}

variable "instance_type" {
  type    = string
  default = "t3.large"
}

variable "min_capacity" {
  type    = number
  default = 3
}

variable "max_capacity" {
  type    = number
  default = 10
}

variable "enable_monitoring" {
  type    = bool
  default = true
}

variable "enable_backup" {
  type    = bool
  default = true
}

variable "backup_retention" {
  type    = number
  default = 30
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
