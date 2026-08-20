variable "vpc_cidr" {
  description = "CIDR block para la VPC principal"
  type        = string

  validation {
    condition     = can(cidrhost(var.vpc_cidr, 0))
    error_message = "El valor vpc_cidr debe ser un bloque CIDR válido."
  }
}

variable "environment" {
  description = "Nombre del entorno (dev, staging, prod)"
  type        = string

  validation {
    condition     = contains(["dev", "staging", "prod"], var.environment)
    error_message = "El entorno debe ser dev, staging o prod."
  }
}

variable "public_subnet_cidrs" {
  description = "Lista de bloques CIDR para subnets públicas"
  type        = list(string)
  default     = []
}

variable "availability_zones" {
  description = "Zonas de disponibilidad para las subnets públicas"
  type        = list(string)
  default     = ["us-east-1a", "us-east-1b"]
}

variable "enable_dns_hostnames" {
  description = "Habilitar nombres DNS en la VPC"
  type        = bool
  default     = true
}

variable "enable_dns_support" {
  description = "Habilitar resolución DNS en la VPC"
  type        = bool
  default     = true
}

variable "common_tags" {
  description = "Tags comunes aplicados a todos los recursos"
  type        = map(string)
  default     = {}
}
