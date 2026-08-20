#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ROOT_DIR="$(cd "$SCRIPT_DIR/.." && pwd)"
ENDPOINT="http://localhost:4566"

echo "==> Esperando a que LocalStack este listo..."
until curl -s "$ENDPOINT/_localstack/health" | grep -q '"s3": "available"'; do
  sleep 2
done

echo "==> Aplicando infraestructura con Terraform..."
cd "$ROOT_DIR/terraform"
terraform init -input=false
terraform apply -auto-approve

BUCKET=$(terraform output -raw bucket_name)
TABLE=$(terraform output -raw table_name)

echo "==> Bucket: $BUCKET | Tabla: $TABLE"

TMP_FILE=$(mktemp /tmp/pedido-XXXX.json)
echo '{"pedido": "12345", "monto": 99.90}' > "$TMP_FILE"
OBJECT_KEY="pedido-test.json"

echo "==> Subiendo archivo de prueba a s3://$BUCKET/$OBJECT_KEY ..."
aws --endpoint-url="$ENDPOINT" s3 cp "$TMP_FILE" "s3://$BUCKET/$OBJECT_KEY"

echo "==> Esperando a que la Lambda procese el evento..."
sleep 6

echo "==> Consultando DynamoDB..."
aws --endpoint-url="$ENDPOINT" dynamodb get-item \
  --table-name "$TABLE" \
  --key "{\"file_key\": {\"S\": \"$OBJECT_KEY\"}}"

rm -f "$TMP_FILE"
