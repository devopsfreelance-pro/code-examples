## variables.tf

variable "aws_region" {
  description = "Region de AWS (o del endpoint de LocalStack)"
  type        = string
  default     = "us-east-1"
}

variable "project_name" {
  description = "Nombre del proyecto, usado como prefijo en los tags"
  type        = string
  default     = "demo-terraform"
}

variable "environment" {
  description = "Entorno de despliegue"
  type        = string
  default     = "dev"

  validation {
    condition     = contains(["dev", "staging", "production"], var.environment)
    error_message = "El entorno debe ser dev, staging o production."
  }
}

variable "vpc_cidr" {
  description = "CIDR block para la VPC"
  type        = string
  default     = "10.0.0.0/16"

  validation {
    condition     = can(cidrhost(var.vpc_cidr, 0))
    error_message = "vpc_cidr debe ser un bloque CIDR valido, por ejemplo 10.0.0.0/16."
  }
}

variable "availability_zones" {
  description = "Zonas de disponibilidad. Agregar una mas crea una subnet publica adicional automaticamente."
  type        = list(string)
  default     = ["us-east-1a", "us-east-1b"]
}
