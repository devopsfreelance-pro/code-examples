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

# AWS permite guiones en nombres de recursos: se conserva el separador "-".
locals {
  base_name = "${var.project}-${var.environment}-network"
  aws_name  = replace(local.base_name, "_", "-")

  common_tags = {
    Project     = var.project
    Environment = var.environment
    ManagedBy   = "terraform"
    Provider    = "aws"
  }
}

# En un entorno real esto seria un resource "aws_vpc". Aca usamos local_file
# para simular el "plan" de despliegue sin requerir credenciales de AWS.
resource "local_file" "plan" {
  filename = "${path.root}/.output/aws-${var.environment}-network.json"
  content = jsonencode({
    provider   = "aws"
    name       = local.aws_name
    cidr_block = var.cidr_block
    region     = var.region
    tags       = local.common_tags
  })
}

output "name" {
  value = local.aws_name
}

output "tags" {
  value = local.common_tags
}
