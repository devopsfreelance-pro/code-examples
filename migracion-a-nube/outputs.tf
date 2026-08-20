## outputs.tf

output "vpc_id" {
  description = "ID de la VPC destino de la migracion."
  value       = aws_vpc.main.id
}

output "private_subnet_ids" {
  description = "IDs de las subnets privadas donde aterrizan las apps migradas."
  value       = aws_subnet.private[*].id
}

output "subnet_count" {
  description = "Cantidad de subnets privadas creadas (una por availability zone)."
  value       = length(aws_subnet.private)
}
