"""
Lambda "sin estado" que se dispara con el evento s3:ObjectCreated.

Demuestra el flujo descrito en el post: un evento (subida de un archivo a un
bucket) desencadena automaticamente una funcion, que lee el objeto original,
extrae metadatos y guarda un resultado en otra ubicacion, sin gestionar
ningun servidor.
"""

import json
import os
import urllib.parse
from datetime import datetime, timezone

import boto3

OUTPUT_BUCKET = os.environ["OUTPUT_BUCKET"]

# LocalStack inyecta LOCALSTACK_HOSTNAME en cada contenedor Lambda que
# levanta para que la funcion pueda llamar de vuelta a la API de S3. En
# AWS real esa variable no existe y boto3 usa el endpoint publico normal.
_localstack_host = os.environ.get("LOCALSTACK_HOSTNAME")
_endpoint_url = f"http://{_localstack_host}:4566" if _localstack_host else None

s3 = boto3.client("s3", endpoint_url=_endpoint_url)


def handler(event, context):
    resultados = []

    for record in event.get("Records", []):
        bucket = record["s3"]["bucket"]["name"]
        key = urllib.parse.unquote_plus(record["s3"]["object"]["key"])

        head = s3.head_object(Bucket=bucket, Key=key)

        metadata = {
            "bucket_origen": bucket,
            "key": key,
            "tamano_bytes": head["ContentLength"],
            "content_type": head.get("ContentType", "desconocido"),
            "procesado_en": datetime.now(timezone.utc).isoformat(),
        }

        output_key = f"{key}.metadata.json"
        s3.put_object(
            Bucket=OUTPUT_BUCKET,
            Key=output_key,
            Body=json.dumps(metadata, indent=2).encode("utf-8"),
            ContentType="application/json",
        )

        resultados.append({"output_bucket": OUTPUT_BUCKET, "output_key": output_key})

    return {"statusCode": 200, "body": json.dumps(resultados)}
