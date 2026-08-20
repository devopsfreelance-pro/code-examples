#!/usr/bin/env bash
# Ejecuta el flujo completo de policy-as-code: genera un plan de Terraform
# y lo valida contra las politicas OPA con Conftest (via Docker).
set -euo pipefail

cd "$(dirname "$0")/terraform"

export AWS_ACCESS_KEY_ID="test"
export AWS_SECRET_ACCESS_KEY="test"
export AWS_DEFAULT_REGION="us-east-1"

echo "== terraform init =="
terraform init -input=false

echo "== terraform plan =="
terraform plan -input=false -out=tfplan

echo "== terraform show -json =="
terraform show -json tfplan > tfplan.json

cd ..

echo "== conftest test (OPA policy-as-code) =="
docker run --rm \
  -v "$(pwd)":/project \
  -w /project \
  openpolicyagent/conftest test terraform/tfplan.json --policy policy --all-namespaces
