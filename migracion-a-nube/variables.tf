## variables.tf
## Parametros del landing zone de migracion.

variable "aws_region" {
  description = "Region de AWS (o de LocalStack)."
  type        = string
  default     = "us-east-1"
}

variable "project_name" {
  description = "Nombre del proyecto, usado como prefijo de tags."
  type        = string
  default     = "migracion-cloud"
}

variable "environment" {
  description = "Entorno de destino de la migracion."
  type        = string
  default     = "production"

  validation {
    condition     = contains(["dev", "staging", "production"], var.environment)
    error_message = "El entorno debe ser dev, staging o production."
  }
}

variable "vpc_cidr" {
  description = "Bloque CIDR de la VPC destino."
  type        = string
  default     = "10.0.0.0/16"

  validation {
    condition     = can(cidrhost(var.vpc_cidr, 0))
    error_message = "vpc_cidr debe ser un bloque CIDR valido, por ejemplo 10.0.0.0/16."
  }
}

variable "availability_zones" {
  description = "Zonas de disponibilidad donde aterrizan las apps migradas (una subnet privada por AZ)."
  type        = list(string)
  default     = ["us-east-1a", "us-east-1b", "us-east-1c"]
}
