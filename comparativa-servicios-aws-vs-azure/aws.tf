# AWS: red privada + almacenamiento de objetos con versionado
# Servicios: VPC + S3 (ver sección "Servicios de Networking" y "Almacenamiento" del post)

resource "aws_vpc" "main" {
  cidr_block           = "10.0.0.0/16"
  enable_dns_support   = true
  enable_dns_hostnames = true

  tags = {
    Name    = "demo-vpc"
    Project = "comparativa-cloud"
  }
}

resource "aws_subnet" "private" {
  vpc_id            = aws_vpc.main.id
  cidr_block        = "10.0.1.0/24"
  availability_zone = "us-east-1a"

  tags = {
    Name = "demo-private-subnet"
  }
}

resource "aws_s3_bucket" "demo" {
  bucket = "demo-comparativa-cloud-bucket"

  tags = {
    Project = "comparativa-cloud"
  }
}

resource "aws_s3_bucket_versioning" "demo" {
  bucket = aws_s3_bucket.demo.id

  versioning_configuration {
    status = "Enabled"
  }
}
