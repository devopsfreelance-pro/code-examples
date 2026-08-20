variable "project" {
  type = string
}

variable "environment" {
  type = string
}

variable "address_space" {
  type = string
}

variable "location" {
  type = string
}

# Azure restringe guiones bajos en varios tipos de recurso: se eliminan
# los separadores para obtener un nombre valido.
locals {
  base_name  = "${var.project}-${var.environment}-network"
  azure_name = replace(local.base_name, "-", "")

  common_tags = {
    Project     = var.project
    Environment = var.environment
    ManagedBy   = "terraform"
    Provider    = "azure"
  }
}

# En un entorno real esto seria un resource "azurerm_virtual_network". Aca
# usamos local_file para simular el "plan" de despliegue sin requerir
# credenciales de Azure.
resource "local_file" "plan" {
  filename = "${path.root}/.output/azure-${var.environment}-network.json"
  content = jsonencode({
    provider      = "azure"
    name          = local.azure_name
    address_space = var.address_space
    location      = var.location
    tags          = local.common_tags
  })
}

output "name" {
  value = local.azure_name
}

output "tags" {
  value = local.common_tags
}
