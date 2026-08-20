# Ejemplo de "test driven infrastructure" del post: infraestructura como
# código que se valida ANTES de aplicarse, no después de romper producción.
#
# A propósito, este archivo contiene dos problemas típicos que el post
# menciona explícitamente: un puerto innecesariamente expuesto (SSH abierto
# a internet) y una credencial hardcodeada. El script check_infra_tests.sh
# los detecta en segundos, igual que en el caso real de fintech del post.

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
  region = "us-east-1"
}

# PROBLEMA 1: 0.0.0.0/0 en el puerto 22 (SSH abierto a todo internet).
# El script de shift left debe bloquear esto antes de un `terraform apply`.
resource "aws_security_group" "app" {
  name        = "shift-left-demo-sg"
  description = "Security group de la app de demo"

  ingress {
    description = "SSH abierto a todo internet (a corregir)"
    from_port   = 22
    to_port     = 22
    protocol    = "tcp"
    cidr_blocks = ["0.0.0.0/0"]
  }

  egress {
    from_port   = 0
    to_port     = 0
    protocol    = "-1"
    cidr_blocks = ["0.0.0.0/0"]
  }

  tags = {
    Project     = "shift-left-testing-devops"
    Environment = "demo"
  }
}

# PROBLEMA 2: credencial hardcodeada en el código (nunca en un repo real).
resource "aws_db_instance" "app_db" {
  identifier          = "shift-left-demo-db"
  engine              = "postgres"
  instance_class      = "db.t3.micro"
  allocated_storage   = 20
  username            = "admin"
  password            = "AKIAIOSFODNN7EXAMPLE" # hardcodeado a propósito
  skip_final_snapshot = true

  tags = {
    Project     = "shift-left-testing-devops"
    Environment = "demo"
  }
}
