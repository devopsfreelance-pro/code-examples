variable "aws_region" {
  description = "Región AWS (simulada por LocalStack)"
  type        = string
  default     = "us-east-1"
}

variable "environment" {
  description = "Nombre del entorno"
  type        = string
  default     = "development"

  validation {
    condition     = contains(["development", "staging", "production"], var.environment)
    error_message = "Environment must be development, staging, or production."
  }
}

variable "project_name" {
  description = "Nombre del proyecto, usado para nombrar recursos"
  type        = string
  default     = "iac-demo"
}

variable "vpc_cidr" {
  description = "Bloque CIDR de la VPC"
  type        = string
  default     = "10.0.0.0/16"
}
