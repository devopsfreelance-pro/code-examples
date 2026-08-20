output "vpc_id" {
  description = "ID de la VPC creada"
  value       = aws_vpc.main.id
}

output "public_subnet_id" {
  description = "ID de la subred pública"
  value       = aws_subnet.public.id
}

output "artifacts_bucket" {
  description = "Nombre del bucket S3 de artefactos"
  value       = aws_s3_bucket.artifacts.bucket
}
