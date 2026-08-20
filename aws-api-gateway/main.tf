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

  endpoints {
    apigateway = "http://localhost:4566"
    lambda     = "http://localhost:4566"
    iam        = "http://localhost:4566"
    sts        = "http://localhost:4566"
    logs       = "http://localhost:4566"
  }

  default_tags {
    tags = {
      Project = "aws-api-gateway-demo"
      Managed = "terraform"
    }
  }
}

resource "aws_iam_role" "lambda_exec" {
  name = "productos-lambda-role"

  assume_role_policy = jsonencode({
    Version = "2012-10-17"
    Statement = [{
      Action    = "sts:AssumeRole"
      Effect    = "Allow"
      Principal = { Service = "lambda.amazonaws.com" }
    }]
  })
}

resource "aws_lambda_function" "productos" {
  function_name    = "productos-handler"
  role             = aws_iam_role.lambda_exec.arn
  handler          = "handler.handler"
  runtime          = "python3.12"
  filename         = "${path.module}/lambda.zip"
  source_code_hash = filebase64sha256("${path.module}/lambda.zip")
}

resource "aws_api_gateway_rest_api" "demo" {
  name        = "productos-api"
  description = "API demo de catalogo de productos (post AWS API Gateway)"
}

resource "aws_api_gateway_resource" "productos" {
  rest_api_id = aws_api_gateway_rest_api.demo.id
  parent_id   = aws_api_gateway_rest_api.demo.root_resource_id
  path_part   = "productos"
}

resource "aws_api_gateway_method" "get_productos" {
  rest_api_id   = aws_api_gateway_rest_api.demo.id
  resource_id   = aws_api_gateway_resource.productos.id
  http_method   = "GET"
  authorization = "NONE"
}

resource "aws_api_gateway_integration" "lambda_integration" {
  rest_api_id             = aws_api_gateway_rest_api.demo.id
  resource_id             = aws_api_gateway_resource.productos.id
  http_method             = aws_api_gateway_method.get_productos.http_method
  integration_http_method = "POST"
  type                    = "AWS_PROXY"
  uri                     = aws_lambda_function.productos.invoke_arn
}

resource "aws_lambda_permission" "apigw" {
  statement_id  = "AllowAPIGatewayInvoke"
  action        = "lambda:InvokeFunction"
  function_name = aws_lambda_function.productos.function_name
  principal     = "apigateway.amazonaws.com"
  source_arn    = "${aws_api_gateway_rest_api.demo.execution_arn}/*/*"
}

resource "aws_api_gateway_deployment" "demo" {
  rest_api_id = aws_api_gateway_rest_api.demo.id

  triggers = {
    redeployment = sha1(jsonencode([
      aws_api_gateway_resource.productos.id,
      aws_api_gateway_method.get_productos.id,
      aws_api_gateway_integration.lambda_integration.id,
    ]))
  }

  lifecycle {
    create_before_destroy = true
  }

  depends_on = [aws_api_gateway_integration.lambda_integration]
}

resource "aws_api_gateway_stage" "dev" {
  deployment_id = aws_api_gateway_deployment.demo.id
  rest_api_id   = aws_api_gateway_rest_api.demo.id
  stage_name    = "dev"
}

output "invoke_url" {
  value = "http://localhost:4566/restapis/${aws_api_gateway_rest_api.demo.id}/${aws_api_gateway_stage.dev.stage_name}/_user_request_/productos"
}
