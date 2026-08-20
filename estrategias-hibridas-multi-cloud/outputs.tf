output "cloud_bucket_name" {
  description = "Nombre del bucket S3 provisionado en el entorno cloud (LocalStack)"
  value       = aws_s3_bucket.cloud_artifacts.bucket
}

output "onprem_container_name" {
  description = "Nombre del contenedor que simula el servicio on-premise"
  value       = docker_container.onprem_web.name
}

output "onprem_url" {
  description = "URL local para verificar el servicio on-premise"
  value       = "http://localhost:8080"
}
