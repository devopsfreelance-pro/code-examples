terraform {
  required_version = ">= 1.5.0"
  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = "~> 5.0"
    }
  }
}

# Provider apuntando a AWS pero sin necesidad de credenciales reales:
# como los dos buckets son recursos nuevos (create), "terraform plan"
# no necesita llamar a la API de AWS para calcular el plan.
provider "aws" {
  region                      = "us-east-1"
  access_key                  = "test"
  secret_key                  = "test"
  skip_credentials_validation = true
  skip_metadata_api_check     = true
  skip_requesting_account_id  = true
}

# --- Bucket COMPLIANT: cifrado, acceso publico bloqueado y versionado ---

resource "aws_s3_bucket" "compliant" {
  bucket = "soc2-demo-compliant-bucket"
}

resource "aws_s3_bucket_server_side_encryption_configuration" "compliant" {
  bucket = aws_s3_bucket.compliant.bucket

  rule {
    apply_server_side_encryption_by_default {
      sse_algorithm = "AES256"
    }
  }
}

resource "aws_s3_bucket_public_access_block" "compliant" {
  bucket = aws_s3_bucket.compliant.bucket

  block_public_acls       = true
  block_public_policy     = true
  ignore_public_acls      = true
  restrict_public_buckets = true
}

resource "aws_s3_bucket_versioning" "compliant" {
  bucket = aws_s3_bucket.compliant.bucket

  versioning_configuration {
    status = "Enabled"
  }
}

# --- Bucket NO COMPLIANT: sin cifrado, sin bloqueo de acceso publico, sin versionado ---
# Simula un recurso que un desarrollador agrega sin pasar por los controles SOC2.

resource "aws_s3_bucket" "noncompliant" {
  bucket = "soc2-demo-noncompliant-bucket"
}
