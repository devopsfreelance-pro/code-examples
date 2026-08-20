terraform {
  required_version = ">= 1.5.0"

  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = "~> 5.0"
    }
    archive = {
      source  = "hashicorp/archive"
      version = "~> 2.4"
    }
  }
}

# Provider apuntando a LocalStack en lugar de AWS real. Credenciales dummy:
# LocalStack no las valida, pero el provider las exige para no fallar.
provider "aws" {
  region                      = "us-east-1"
  access_key                  = "test"
  secret_key                  = "test"
  skip_credentials_validation = true
  skip_metadata_api_check     = true
  skip_requesting_account_id  = true

  endpoints {
    s3     = "http://localhost:4566"
    lambda = "http://localhost:4566"
    iam    = "http://localhost:4566"
  }
}

# Bucket de entrada: aqui se suben los archivos que disparan la funcion
resource "aws_s3_bucket" "input" {
  bucket        = "infra-serverless-input"
  force_destroy = true
}

# Bucket de salida: aqui la funcion escribe los metadatos generados
resource "aws_s3_bucket" "output" {
  bucket        = "infra-serverless-output"
  force_destroy = true
}

# Rol de ejecucion minimo para la Lambda (LocalStack no aplica la politica
# realmente, pero AWS real si la requeriria)
resource "aws_iam_role" "lambda_exec" {
  name = "infra-serverless-lambda-role"

  assume_role_policy = jsonencode({
    Version = "2012-10-17"
    Statement = [{
      Action = "sts:AssumeRole"
      Effect = "Allow"
      Principal = {
        Service = "lambda.amazonaws.com"
      }
    }]
  })
}

# Empaqueta el codigo de la funcion en un zip para el despliegue
data "archive_file" "lambda_zip" {
  type        = "zip"
  source_dir  = "${path.module}/lambda"
  output_path = "${path.module}/build/handler.zip"
}

resource "aws_lambda_function" "process_upload" {
  function_name    = "process-upload"
  role             = aws_iam_role.lambda_exec.arn
  handler          = "handler.handler"
  runtime          = "python3.12"
  filename         = data.archive_file.lambda_zip.output_path
  source_code_hash = data.archive_file.lambda_zip.output_base64sha256
  timeout          = 10
  memory_size      = 128

  environment {
    variables = {
      OUTPUT_BUCKET = aws_s3_bucket.output.bucket
    }
  }
}

# Permiso para que S3 pueda invocar la funcion
resource "aws_lambda_permission" "allow_s3" {
  statement_id  = "AllowExecutionFromS3"
  action        = "lambda:InvokeFunction"
  function_name = aws_lambda_function.process_upload.function_name
  principal     = "s3.amazonaws.com"
  source_arn    = aws_s3_bucket.input.arn
}

# Conecta el evento s3:ObjectCreated del bucket de entrada con la Lambda
resource "aws_s3_bucket_notification" "trigger" {
  bucket = aws_s3_bucket.input.id

  lambda_function {
    lambda_function_arn = aws_lambda_function.process_upload.arn
    events              = ["s3:ObjectCreated:*"]
  }

  depends_on = [aws_lambda_permission.allow_s3]
}

output "input_bucket" {
  value = aws_s3_bucket.input.bucket
}

output "output_bucket" {
  value = aws_s3_bucket.output.bucket
}
