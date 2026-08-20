## outputs.tf

output "vpc_id" {
  description = "ID de la VPC creada"
  value       = aws_vpc.main.id
}

output "public_subnet_ids" {
  description = "IDs de las subnets publicas (una por availability zone)"
  value       = aws_subnet.public[*].id
}

output "subnet_count" {
  description = "Cantidad de subnets publicas creadas, igual a length(var.availability_zones)"
  value       = length(aws_subnet.public)
}
