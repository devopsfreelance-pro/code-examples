#!/usr/bin/env bash
# Crea la tabla DynamoDB, la cola SQS, empaqueta y despliega la Lambda,
# y conecta la cola como event source, todo contra LocalStack.
set -euo pipefail

ENDPOINT="http://localhost:4566"
REGION="us-east-1"
FUNCTION_NAME="procesar-pedido"
QUEUE_NAME="orders-queue"
TABLE_NAME="Orders"

export AWS_ACCESS_KEY_ID="test"
export AWS_SECRET_ACCESS_KEY="test"
export AWS_DEFAULT_REGION="$REGION"

aws_local() {
  aws --endpoint-url="$ENDPOINT" --region "$REGION" "$@"
}

echo "==> Creando tabla DynamoDB: $TABLE_NAME"
aws_local dynamodb create-table \
  --table-name "$TABLE_NAME" \
  --attribute-definitions AttributeName=order_id,AttributeType=S \
  --key-schema AttributeName=order_id,KeyType=HASH \
  --billing-mode PAY_PER_REQUEST \
  >/dev/null 2>&1 || echo "    (la tabla ya existe, se reutiliza)"

echo "==> Creando cola SQS: $QUEUE_NAME"
aws_local sqs create-queue --queue-name "$QUEUE_NAME" >/dev/null 2>&1 \
  || echo "    (la cola ya existe, se reutiliza)"

QUEUE_URL=$(aws_local sqs get-queue-url --queue-name "$QUEUE_NAME" --query 'QueueUrl' --output text)
QUEUE_ARN=$(aws_local sqs get-queue-attributes --queue-url "$QUEUE_URL" \
  --attribute-names QueueArn --query 'Attributes.QueueArn' --output text)

echo "==> Empaquetando el codigo de la Lambda"
rm -f function.zip
zip -q function.zip handler.py

echo "==> Creando/actualizando la funcion Lambda: $FUNCTION_NAME"
if aws_local lambda get-function --function-name "$FUNCTION_NAME" >/dev/null 2>&1; then
  aws_local lambda update-function-code \
    --function-name "$FUNCTION_NAME" \
    --zip-file fileb://function.zip >/dev/null
else
  aws_local lambda create-function \
    --function-name "$FUNCTION_NAME" \
    --runtime python3.12 \
    --handler handler.lambda_handler \
    --zip-file fileb://function.zip \
    --role arn:aws:iam::000000000000:role/lambda-role \
    --environment "Variables={TABLE_NAME=$TABLE_NAME,DYNAMODB_ENDPOINT_URL=http://localstack:4566}" \
    --timeout 30 \
    >/dev/null
fi

echo "==> Esperando a que la funcion este activa"
aws_local lambda wait function-active --function-name "$FUNCTION_NAME"

echo "==> Conectando la cola SQS como event source de la Lambda"
aws_local lambda create-event-source-mapping \
  --function-name "$FUNCTION_NAME" \
  --event-source-arn "$QUEUE_ARN" \
  --batch-size 5 \
  >/dev/null 2>&1 || echo "    (el event source mapping ya existe)"

echo ""
echo "Listo. QUEUE_URL=$QUEUE_URL"
echo "Enviá un mensaje de prueba con: ./send-order.sh"
