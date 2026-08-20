## Capa de infraestructura del ejemplo.
##
## En una plataforma real esta capa usaria providers de AWS/Azure/GCP para
## crear computo, base de datos y redes de verdad. Para poder correr este
## ejemplo en minutos y sin costo, se usa el provider `local`: cada
## "recurso de infraestructura" se materializa como un archivo en disco,
## pero el flujo (una ServiceRequest -> N recursos provisionados de forma
## coherente) es el mismo que describe el post.

terraform {
  required_providers {
    local = {
      source  = "hashicorp/local"
      version = "~> 2.5"
    }
  }
}

## "Computo" provisionado para el servicio: representa lo que en un cluster
## real seria un Deployment de Kubernetes generado a partir de la plantilla.
resource "local_file" "compute_manifest" {
  filename = "${path.module}/output/${var.service_name}/compute.json"
  content = jsonencode({
    kind        = "Deployment"
    name        = var.service_name
    image       = var.base_image
    port        = var.container_port
    healthz     = var.health_check_path
    resources   = { cpu = var.compute_cpu, memory = var.compute_memory }
    environment = var.environment
  })
}

## "Base de datos" provisionada segun el catalogo de la solicitud.
resource "local_file" "database_manifest" {
  filename = "${path.module}/output/${var.service_name}/database.json"
  content = jsonencode({
    kind        = "Database"
    engine      = var.db_engine
    version     = var.db_version
    tier        = var.db_tier
    environment = var.environment
  })
}

## Monitoreo/logging: solo se crea si el desarrollador lo pidio en
## `integrations`, igual que en el catalogo del post.
resource "local_file" "monitoring_manifest" {
  count    = contains(var.integrations, "monitoring") ? 1 : 0
  filename = "${path.module}/output/${var.service_name}/monitoring.json"
  content = jsonencode({
    kind   = "PrometheusRule"
    target = var.service_name
    alerts = ["high_error_rate", "pod_restarts"]
  })
}

resource "local_file" "logging_manifest" {
  count    = contains(var.integrations, "logging") ? 1 : 0
  filename = "${path.module}/output/${var.service_name}/logging.json"
  content = jsonencode({
    kind   = "LogPipeline"
    target = var.service_name
    sink   = "central-log-store"
  })
}

## Manifest final: registro auditable de que se aprovisiono, para quien y
## cuando (seccion "trazabilidad y auditoria" del post).
resource "local_file" "environment_manifest" {
  filename = "${path.module}/environment-manifest.json"
  content = jsonencode({
    service        = var.service_name
    owner          = var.owner
    environment    = var.environment
    git_repository = var.git_repository
    provisioned = {
      compute      = "${var.compute_cpu} CPU / ${var.compute_memory} RAM"
      database     = "${var.db_engine} ${var.db_version} (${var.db_tier})"
      integrations = var.integrations
    }
  })
}

output "summary" {
  value = "Servicio '${var.service_name}' (${var.environment}) provisionado para el equipo '${var.owner}'."
}
