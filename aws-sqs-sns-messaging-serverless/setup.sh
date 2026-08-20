#!/usr/bin/env bash
# Crea el topic SNS y las dos colas SQS suscritas (patron fan-out) en LocalStack.
set -euo pipefail

ENDPOINT="http://localhost:4566"
REGION="us-east-1"
AWS="aws --endpoint-url=${ENDPOINT} --region=${REGION}"

export AWS_ACCESS_KEY_ID="test"
export AWS_SECRET_ACCESS_KEY="test"

echo "== Creando topic SNS: eventos-pedidos =="
TOPIC_ARN=$(${AWS} sns create-topic --name eventos-pedidos --query 'TopicArn' --output text)
echo "TopicArn: ${TOPIC_ARN}"

for QUEUE in procesamiento-inventario procesamiento-facturacion; do
  echo "== Creando cola SQS: ${QUEUE} =="
  QUEUE_URL=$(${AWS} sqs create-queue --queue-name "${QUEUE}" --query 'QueueUrl' --output text)
  QUEUE_ARN=$(${AWS} sqs get-queue-attributes \
    --queue-url "${QUEUE_URL}" \
    --attribute-names QueueArn \
    --query 'Attributes.QueueArn' --output text)

  echo "== Suscribiendo ${QUEUE} al topic =="
  ${AWS} sns subscribe \
    --topic-arn "${TOPIC_ARN}" \
    --protocol sqs \
    --notification-endpoint "${QUEUE_ARN}" > /dev/null

  echo "QueueUrl (${QUEUE}): ${QUEUE_URL}"
done

echo ""
echo "Setup completo. TopicArn para publicar: ${TOPIC_ARN}"
