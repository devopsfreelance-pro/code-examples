variable "nombre_servicio" {
  description = "Nombre del microservicio"
  type        = string
}

variable "replicas" {
  description = "Cantidad de réplicas simuladas"
  type        = number
  default     = 1
}

variable "habilitar_metricas" {
  description = "Si el servicio expone métricas (simulado)"
  type        = bool
  default     = false
}

variable "puerto_metricas" {
  description = "Puerto de métricas simulado"
  type        = number
  default     = 9090
}

# Simula el "aprovisionamiento" de un microservicio generando un archivo
# de configuración local. En un caso real este módulo crearía un
# aws_ecs_service, un kubernetes_deployment, etc.
resource "local_file" "servicio" {
  filename = "${path.module}/../../output/${var.nombre_servicio}.json"
  content = jsonencode({
    servicio           = var.nombre_servicio
    replicas           = var.replicas
    habilitar_metricas = var.habilitar_metricas
    puerto_metricas    = var.habilitar_metricas ? var.puerto_metricas : null
    managed_by         = "OpenTofu"
  })
}

output "archivo_generado" {
  value = local_file.servicio.filename
}
