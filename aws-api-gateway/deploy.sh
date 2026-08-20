#!/usr/bin/env bash
# Empaqueta la Lambda, aplica el Terraform contra LocalStack y prueba el endpoint.
set -euo pipefail

cd "$(dirname "$0")"

echo "==> Empaquetando funcion Lambda"
cd lambda
zip -q -r ../lambda.zip handler.py
cd ..

echo "==> Inicializando Terraform"
terraform init -input=false

echo "==> Aplicando configuracion (API Gateway + Lambda) en LocalStack"
terraform apply -auto-approve

INVOKE_URL=$(terraform output -raw invoke_url)

echo "==> Endpoint desplegado: ${INVOKE_URL}"
echo "==> Probando la API"
curl -s "${INVOKE_URL}" | python3 -m json.tool
