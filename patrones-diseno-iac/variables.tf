variable "environment" {
  description = "Entorno a desplegar: development, staging o production."
  type        = string
  default     = "development"
}

variable "vpc_cidr" {
  description = "Bloque CIDR de la VPC para este entorno."
  type        = string
  default     = "10.0.0.0/16"
}

variable "azs" {
  description = "Availability zones a usar."
  type        = list(string)
  default     = ["us-east-1a", "us-east-1b"]
}

variable "enable_nat_gateway" {
  description = "Habilitar NAT gateway (documentado, no crea recursos reales en este ejemplo)."
  type        = bool
  default     = true
}

# Patrón de "Entornos Parametrizados" del post: un único mapa con los
# valores que varían por entorno, en vez de duplicar el código de
# infraestructura una vez por cada uno.
variable "instance_sizes" {
  description = "Tamaño de instancia por entorno."
  type        = map(string)
  default = {
    development = "t3.small"
    staging     = "t3.medium"
    production  = "t3.xlarge"
  }
}
