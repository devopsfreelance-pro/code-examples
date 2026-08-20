# Ejemplo mínimo de Infraestructura como Código con Terraform.
# Provisiona una VPC con subred pública y un bucket S3, todo etiquetado,
# contra LocalStack (simulador de AWS local, sin costo ni cuenta real).

terraform {
  required_version = ">= 1.5"
  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = "~> 5.0"
    }
  }
}

provider "aws" {
  region                      = var.aws_region
  access_key                  = "test"
  secret_key                  = "test"
  s3_use_path_style           = true
  skip_credentials_validation = true
  skip_metadata_api_check     = true
  skip_requesting_account_id  = true

  default_tags {
    tags = {
      Environment = var.environment
      Project     = var.project_name
      ManagedBy   = "terraform"
    }
  }

  endpoints {
    ec2 = "http://localhost:4566"
    s3  = "http://localhost:4566"
  }
}

# VPC declarada de forma declarativa: describimos el estado deseado,
# Terraform decide cómo llegar a él (crear/actualizar/destruir).
resource "aws_vpc" "main" {
  cidr_block           = var.vpc_cidr
  enable_dns_hostnames = true
  enable_dns_support   = true

  tags = {
    Name = "${var.project_name}-vpc-${var.environment}"
  }
}

resource "aws_internet_gateway" "main" {
  vpc_id = aws_vpc.main.id

  tags = {
    Name = "${var.project_name}-igw-${var.environment}"
  }
}

resource "aws_subnet" "public" {
  vpc_id                  = aws_vpc.main.id
  cidr_block              = cidrsubnet(var.vpc_cidr, 8, 0)
  map_public_ip_on_launch = true

  tags = {
    Name = "${var.project_name}-public-${var.environment}"
    Type = "public"
  }
}

resource "aws_route_table" "public" {
  vpc_id = aws_vpc.main.id

  route {
    cidr_block = "0.0.0.0/0"
    gateway_id = aws_internet_gateway.main.id
  }

  tags = {
    Name = "${var.project_name}-public-rt"
  }
}

resource "aws_route_table_association" "public" {
  subnet_id      = aws_subnet.public.id
  route_table_id = aws_route_table.public.id
}

# Bucket S3 para artefactos de la infraestructura (ej: logs, backups).
# Idempotencia: aplicar este archivo varias veces no crea recursos duplicados.
resource "aws_s3_bucket" "artifacts" {
  bucket = "${var.project_name}-artifacts-${var.environment}"

  tags = {
    Name = "${var.project_name}-artifacts"
  }
}
