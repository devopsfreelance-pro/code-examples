output "instance_type" {
  description = "Tamaño de instancia resuelto para el entorno."
  value       = local.instance_type
}

output "private_subnets" {
  description = "Subredes privadas calculadas a partir del CIDR de la VPC."
  value       = local.private_subnets
}

output "config_file" {
  description = "Ruta del archivo JSON generado con la configuración de red."
  value       = local_file.network_config.filename
}
