# Módulo mínimo: un bucket S3 con encriptación y bloqueo de acceso público.
# Apunta a LocalStack en vez de AWS real, así el ciclo completo
# (validate -> plan -> policy -> apply -> destroy) es gratis y reproducible.

terraform {
  required_version = ">= 1.5.0"

  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = "~> 5.0"
    }
  }
}

provider "aws" {
  region                      = "us-east-1"
  access_key                  = "test"
  secret_key                  = "test"
  skip_credentials_validation = true
  skip_metadata_api_check     = true
  skip_requesting_account_id  = true
  s3_use_path_style           = true

  endpoints {
    s3 = "http://localhost:4566"
  }
}

variable "bucket_name" {
  description = "Nombre del bucket S3 de prueba"
  type        = string
  default     = "testing-infra-demo-bucket"
}

# Toggle intencional para poder romper la policy en la demo:
# con enable_encryption = false, conftest debe bloquear el plan.
variable "enable_encryption" {
  description = "Si false, el bucket queda sin cifrado (para probar que la policy lo detecta)"
  type        = bool
  default     = true
}

resource "aws_s3_bucket" "demo" {
  bucket = var.bucket_name

  tags = {
    ManagedBy = "terraform"
    Purpose   = "testing-infraestructura-demo"
  }
}

resource "aws_s3_bucket_public_access_block" "demo" {
  bucket = aws_s3_bucket.demo.id

  block_public_acls       = true
  block_public_policy     = true
  ignore_public_acls      = true
  restrict_public_buckets = true
}

resource "aws_s3_bucket_server_side_encryption_configuration" "demo" {
  count  = var.enable_encryption ? 1 : 0
  bucket = aws_s3_bucket.demo.id

  rule {
    apply_server_side_encryption_by_default {
      sse_algorithm = "AES256"
    }
  }
}

output "bucket_id" {
  value = aws_s3_bucket.demo.id
}
