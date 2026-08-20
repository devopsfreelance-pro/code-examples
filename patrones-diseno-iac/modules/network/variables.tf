variable "environment" {
  description = "Nombre del entorno (development, staging, production)."
  type        = string
}

variable "vpc_cidr" {
  description = "Bloque CIDR base de la VPC."
  type        = string
}

variable "azs" {
  description = "Availability zones donde se crean las subredes."
  type        = list(string)
}

variable "instance_sizes" {
  description = "Mapa environment -> tamaño de instancia (patrón de entornos parametrizados)."
  type        = map(string)
}

variable "enable_nat_gateway" {
  description = "Si se habilita NAT gateway para las subredes privadas."
  type        = bool
  default     = true
}
