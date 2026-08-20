## Módulo reutilizable "app_stack": encapsula el patrón de infraestructura
## de una aplicación (tal como describe el post) con variables tipadas,
## validación y outputs. No depende de ningún proveedor de nube: escribe
## un archivo local que representa la infraestructura, así el ejemplo
## corre en segundos sin cuenta de AWS ni Docker.

terraform {
  required_version = ">= 1.5"
  required_providers {
    local = {
      source  = "hashicorp/local"
      version = "~> 2.5"
    }
  }
}

variable "environment" {
  description = "Entorno de despliegue"
  type        = string

  validation {
    condition     = contains(["dev", "staging", "production"], var.environment)
    error_message = "El entorno debe ser dev, staging o production."
  }
}

variable "application_name" {
  description = "Nombre de la aplicación"
  type        = string
}

variable "instance_type" {
  description = "Tamaño de instancia (simulado)"
  type        = string
  default     = "t3.micro"
}

variable "min_capacity" {
  description = "Capacidad mínima del auto scaling"
  type        = number
  default     = 1
}

variable "max_capacity" {
  description = "Capacidad máxima del auto scaling"
  type        = number
  default     = 3

  validation {
    condition     = var.max_capacity >= var.min_capacity
    error_message = "max_capacity debe ser mayor o igual que min_capacity."
  }
}

variable "enable_monitoring" {
  description = "Habilita monitoreo"
  type        = bool
  default     = true
}

variable "enable_backup" {
  description = "Habilita backups"
  type        = bool
  default     = false
}

variable "backup_retention" {
  description = "Días de retención de backup"
  type        = number
  default     = 7
}

variable "tags" {
  description = "Tags adicionales del componente"
  type        = map(string)
  default     = {}
}

locals {
  common_tags = {
    ManagedBy = "terraform"
    Module    = "app_stack"
  }

  all_tags = merge(local.common_tags, var.tags)
}

## Simula el recurso de infraestructura real (p.ej. un ASG + Load Balancer).
## Se usa local_file en vez de un provider de nube para que el ejemplo
## corra en cualquier máquina sin credenciales.
resource "local_file" "app_config" {
  filename = "${path.root}/output/${var.environment}-${var.application_name}.json"

  content = jsonencode({
    environment       = var.environment
    application_name  = var.application_name
    instance_type     = var.instance_type
    min_capacity      = var.min_capacity
    max_capacity      = var.max_capacity
    enable_monitoring = var.enable_monitoring
    enable_backup     = var.enable_backup
    backup_retention  = var.enable_backup ? var.backup_retention : 0
    tags              = local.all_tags
  })
}

output "config_path" {
  description = "Ruta del archivo generado que representa la infraestructura"
  value       = local_file.app_config.filename
}

output "applied_tags" {
  description = "Tags finales aplicados al componente"
  value       = local.all_tags
}

output "capacity_range" {
  description = "Rango de capacidad configurado"
  value       = "${var.min_capacity}-${var.max_capacity}"
}
