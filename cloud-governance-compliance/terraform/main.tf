terraform {
  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = "~> 3.75"
    }
  }
}

provider "aws" {
  region                      = "us-east-1"
  skip_credentials_validation = true
  skip_requesting_account_id  = true
  skip_metadata_api_check     = true
  access_key                  = "test"
  secret_key                  = "test"
}

# Bucket NO conforme: no tiene cifrado (server-side encryption) configurado.
resource "aws_s3_bucket" "noncompliant" {
  bucket = "mi-empresa-datos-noncompliant"
}

# Bucket conforme: cifrado con KMS habilitado (bloque inline, como en el post).
resource "aws_s3_bucket" "compliant" {
  bucket = "mi-empresa-datos-compliant"

  server_side_encryption_configuration {
    rule {
      apply_server_side_encryption_by_default {
        sse_algorithm = "aws:kms"
      }
    }
  }
}

# Instancia NO conforme: falta el tag obligatorio "Environment".
resource "aws_instance" "noncompliant" {
  ami           = "ami-0123456789abcdef0"
  instance_type = "t3.micro"

  tags = {
    Owner = "platform-team"
  }
}

# Instancia conforme: tiene todos los tags requeridos.
resource "aws_instance" "compliant" {
  ami           = "ami-0123456789abcdef0"
  instance_type = "t3.micro"

  tags = {
    Environment = "production"
    Owner       = "platform-team"
    Project     = "payment-service"
  }
}
