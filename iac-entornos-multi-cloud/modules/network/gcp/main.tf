variable "project" {
  type = string
}

variable "environment" {
  type = string
}

variable "cidr_block" {
  type = string
}

variable "region" {
  type = string
}

# GCP exige nombres en minusculas y solo permite guiones como separador.
locals {
  base_name = "${var.project}-${var.environment}-network"
  gcp_name  = lower(replace(local.base_name, "_", "-"))

  common_tags = {
    Project     = var.project
    Environment = var.environment
    ManagedBy   = "terraform"
    Provider    = "gcp"
  }
}

# En un entorno real esto seria un resource "google_compute_network". Aca
# usamos local_file para simular el "plan" de despliegue sin requerir
# credenciales de GCP.
resource "local_file" "plan" {
  filename = "${path.root}/.output/gcp-${var.environment}-network.json"
  content = jsonencode({
    provider   = "gcp"
    name       = local.gcp_name
    cidr_block = var.cidr_block
    region     = var.region
    tags       = local.common_tags
  })
}

output "name" {
  value = local.gcp_name
}

output "tags" {
  value = local.common_tags
}
