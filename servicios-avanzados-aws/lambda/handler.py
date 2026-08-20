"""
Lambda que procesa eventos de S3 y registra el resultado en DynamoDB.

Ilustra el patron event-driven descripto en el post "AWS Advanced":
S3 dispara la funcion Lambda cuando se sube un archivo, la funcion
procesa el evento y guarda el resultado en DynamoDB sin gestionar
un solo servidor.
"""

import json
import os

import boto3


def _dynamodb_resource():
    # LocalStack inyecta LOCALSTACK_HOSTNAME dentro del contenedor de la
    # Lambda para que pueda llamar de vuelta a otros servicios emulados.
    hostname = os.environ.get("LOCALSTACK_HOSTNAME")
    if hostname:
        endpoint_url = f"http://{hostname}:{os.environ.get('EDGE_PORT', '4566')}"
        return boto3.resource("dynamodb", endpoint_url=endpoint_url, region_name="us-east-1")
    # En AWS real no se define LOCALSTACK_HOSTNAME: se usa el endpoint por defecto.
    return boto3.resource("dynamodb", region_name=os.environ.get("AWS_REGION", "us-east-1"))


def lambda_handler(event, context):
    table_name = os.environ["TABLE_NAME"]
    table = _dynamodb_resource().Table(table_name)

    processed = 0
    for record in event.get("Records", []):
        s3_info = record.get("s3", {})
        bucket = s3_info.get("bucket", {}).get("name", "desconocido")
        key = s3_info.get("object", {}).get("key", "desconocido")
        size = s3_info.get("object", {}).get("size", 0)

        table.put_item(
            Item={
                "file_key": key,
                "bucket": bucket,
                "size_bytes": size,
                "status": "PROCESSED",
            }
        )
        processed += 1
        print(f"Procesado {key} de {bucket} ({size} bytes)")

    return {
        "statusCode": 200,
        "body": json.dumps({"processed": processed}),
    }
