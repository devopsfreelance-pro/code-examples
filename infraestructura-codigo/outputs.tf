output "config_path" {
  description = "Ruta del archivo generado que representa el recurso declarado."
  value       = local_file.web_server.filename
}

output "declared_state" {
  description = "Contenido declarado en el código (lo que Terraform espera que exista)."
  value       = jsondecode(local_file.web_server.content)
}
