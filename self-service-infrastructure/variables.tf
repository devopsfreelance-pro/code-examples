## Todas las variables tienen un default que reproduce la ServiceRequest de
## ejemplo (`service-request.yaml`, servicio "orders-api-dev"). Asi
## `tofu plan`/`tofu apply` funcionan de forma standalone (por ejemplo en un
## smoke test de CI que corre `tofu plan` sin pasar por `provision.py`).
## `provision.py` sigue siendo el flujo real: genera `terraform.tfvars.json`
## a partir de la ServiceRequest, y esos valores pisan estos defaults.

variable "service_name" {
  type        = string
  description = "Nombre del servicio solicitado en la ServiceRequest"
  default     = "orders-api-dev"
}

variable "environment" {
  type        = string
  description = "Ambiente destino: development, staging o production"
  default     = "development"
}

variable "owner" {
  type        = string
  description = "Equipo dueno del servicio (trazabilidad y costos)"
  default     = "payments-team"
}

variable "git_repository" {
  type        = string
  description = "Repositorio de codigo fuente del servicio"
  default     = "https://github.com/company/orders-api"
}

variable "base_image" {
  type        = string
  description = "Imagen base derivada de la plantilla del catalogo"
  default     = "node:20-alpine"
}

variable "container_port" {
  type        = number
  description = "Puerto expuesto por el contenedor"
  default     = 3000
}

variable "health_check_path" {
  type        = string
  description = "Path de health check derivado de la plantilla"
  default     = "/healthz"
}

variable "db_engine" {
  type        = string
  description = "Motor de base de datos derivado del catalogo"
  default     = "postgres"
}

variable "db_version" {
  type        = string
  description = "Version del motor de base de datos"
  default     = "16"
}

variable "db_tier" {
  type        = string
  description = "Tier de la base de datos: shared o dedicated"
  default     = "shared"
}

variable "compute_cpu" {
  type        = string
  description = "CPU asignada segun el tamano de compute solicitado"
  default     = "250m"
}

variable "compute_memory" {
  type        = string
  description = "Memoria asignada segun el tamano de compute solicitado"
  default     = "512Mi"
}

variable "integrations" {
  type        = list(string)
  description = "Integraciones solicitadas (monitoring, logging, etc)"
  default     = ["monitoring", "logging"]
}
