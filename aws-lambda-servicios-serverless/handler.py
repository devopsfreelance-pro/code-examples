"""
Handler de AWS Lambda que procesa mensajes de una cola SQS y guarda
cada pedido en DynamoDB. Es el mismo patron "SQS -> Lambda -> DynamoDB"
descrito en el post del blog (seccion "Fuentes de Eventos: SQS").

Reporta los items fallidos individualmente via batchItemFailures para
que SQS reintente solo los mensajes que fallaron, no todo el batch.
"""
import json
import os

import boto3

dynamodb = boto3.resource(
    "dynamodb",
    endpoint_url=os.environ.get("DYNAMODB_ENDPOINT_URL"),
    region_name=os.environ.get("AWS_REGION", "us-east-1"),
)
table = dynamodb.Table(os.environ.get("TABLE_NAME", "Orders"))


def lambda_handler(event, context):
    failed_records = []

    for record in event.get("Records", []):
        try:
            order = json.loads(record["body"])

            if "id" not in order or "customer" not in order or "total" not in order:
                raise ValueError("Pedido invalido: faltan campos requeridos")

            table.put_item(
                Item={
                    "order_id": str(order["id"]),
                    "customer": order["customer"],
                    "total": str(order["total"]),
                    "status": "processing",
                }
            )
            print(f"Pedido {order['id']} guardado correctamente")
        except Exception as exc:
            print(f"Error procesando record {record.get('messageId')}: {exc}")
            failed_records.append({"itemIdentifier": record["messageId"]})

    return {"batchItemFailures": failed_records}
