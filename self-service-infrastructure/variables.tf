variable "service_name" {
  type        = string
  description = "Nombre del servicio solicitado en la ServiceRequest"
}

variable "environment" {
  type        = string
  description = "Ambiente destino: development, staging o production"
}

variable "owner" {
  type        = string
  description = "Equipo dueno del servicio (trazabilidad y costos)"
}

variable "git_repository" {
  type        = string
  description = "Repositorio de codigo fuente del servicio"
}

variable "base_image" {
  type        = string
  description = "Imagen base derivada de la plantilla del catalogo"
}

variable "container_port" {
  type        = number
  description = "Puerto expuesto por el contenedor"
}

variable "health_check_path" {
  type        = string
  description = "Path de health check derivado de la plantilla"
}

variable "db_engine" {
  type        = string
  description = "Motor de base de datos derivado del catalogo"
}

variable "db_version" {
  type        = string
  description = "Version del motor de base de datos"
}

variable "db_tier" {
  type        = string
  description = "Tier de la base de datos: shared o dedicated"
}

variable "compute_cpu" {
  type        = string
  description = "CPU asignada segun el tamano de compute solicitado"
}

variable "compute_memory" {
  type        = string
  description = "Memoria asignada segun el tamano de compute solicitado"
}

variable "integrations" {
  type        = list(string)
  description = "Integraciones solicitadas (monitoring, logging, etc)"
  default     = []
}
