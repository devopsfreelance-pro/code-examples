#!/usr/bin/env bash
# Envia un pedido de prueba a la cola SQS para disparar la Lambda.
set -euo pipefail

ENDPOINT="http://localhost:4566"
REGION="us-east-1"
QUEUE_NAME="orders-queue"

export AWS_ACCESS_KEY_ID="test"
export AWS_SECRET_ACCESS_KEY="test"
export AWS_DEFAULT_REGION="$REGION"

QUEUE_URL=$(aws --endpoint-url="$ENDPOINT" --region "$REGION" \
  sqs get-queue-url --queue-name "$QUEUE_NAME" --query 'QueueUrl' --output text)

ORDER_ID="${1:-1001}"

MESSAGE=$(cat <<JSON
{"id": "$ORDER_ID", "customer": "Juan Perez", "total": 149.90}
JSON
)

echo "==> Enviando pedido $ORDER_ID a la cola"
aws --endpoint-url="$ENDPOINT" --region "$REGION" \
  sqs send-message --queue-url "$QUEUE_URL" --message-body "$MESSAGE" >/dev/null

echo "==> Esperando 3s a que la Lambda procese el mensaje"
sleep 3

echo "==> Contenido actual de la tabla Orders:"
aws --endpoint-url="$ENDPOINT" --region "$REGION" \
  dynamodb scan --table-name Orders --output table
