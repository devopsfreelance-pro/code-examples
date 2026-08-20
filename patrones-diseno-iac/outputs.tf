output "environment" {
  value = var.environment
}

output "instance_type" {
  description = "Tamaño de instancia resuelto para el entorno actual."
  value       = module.network.instance_type
}

output "private_subnets" {
  value = module.network.private_subnets
}

output "config_file" {
  description = "Archivo JSON con el plan de red generado."
  value       = module.network.config_file
}
