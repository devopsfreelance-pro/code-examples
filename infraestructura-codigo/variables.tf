variable "environment" {
  description = "Entorno donde se declara el recurso (dev, staging, production)."
  type        = string
  default     = "dev"

  validation {
    condition     = contains(["dev", "staging", "production"], var.environment)
    error_message = "El entorno debe ser dev, staging o production."
  }
}

variable "instance_type" {
  description = "Tipo de instancia declarado para el servidor web (solo texto, no crea nada real)."
  type        = string
  default     = "t3.micro"
}
