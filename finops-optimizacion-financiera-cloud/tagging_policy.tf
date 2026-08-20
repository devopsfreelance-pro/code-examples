## Política de etiquetado obligatorio en Terraform para AWS.
## Deniega el lanzamiento de instancias EC2 que no incluyan las tags
## "Environment" y "CostCenter", requisito base de la fase "Informar" de FinOps
## para poder asignar costos a equipos/proyectos (chargeback / showback).

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

resource "aws_iam_policy" "require_tags_policy" {
  name        = "require-resource-tags"
  description = "Require tags on all resources"

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Sid      = "DenyEc2RunInstanceWithoutEnvironmentTag"
        Effect   = "Deny"
        Action   = "ec2:RunInstances"
        Resource = "arn:aws:ec2:*:*:instance/*"
        Condition = {
          "StringNotLike" = {
            "aws:RequestTag/Environment" = ["prod", "dev", "qa", "stage"]
          }
        }
      },
      {
        Sid      = "DenyEc2RunInstanceWithoutCostCenterTag"
        Effect   = "Deny"
        Action   = "ec2:RunInstances"
        Resource = "arn:aws:ec2:*:*:instance/*"
        Condition = {
          "StringNotLike" = {
            "aws:RequestTag/CostCenter" = ["*"]
          }
        }
      }
    ]
  })
}

output "policy_arn" {
  description = "ARN de la policy generada (útil para adjuntarla a un rol/grupo)"
  value       = aws_iam_policy.require_tags_policy.arn
}
