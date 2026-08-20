#!/usr/bin/env python3
"""Publica un evento 'pedido_creado' en el topic SNS.

El topic distribuye el mensaje automaticamente a todas las colas SQS
suscritas (patron fan-out), tal como se describe en el post del blog.
"""
import json
import sys
import uuid
from datetime import datetime, timezone

import boto3

ENDPOINT_URL = "http://localhost:4566"
REGION = "us-east-1"
TOPIC_NAME = "eventos-pedidos"


def get_topic_arn(sns_client) -> str:
    response = sns_client.list_topics()
    for topic in response.get("Topics", []):
        if topic["TopicArn"].endswith(f":{TOPIC_NAME}"):
            return topic["TopicArn"]
    raise RuntimeError(
        f"No se encontro el topic '{TOPIC_NAME}'. Corre ./setup.sh primero."
    )


def publicar_evento_pedido(sns_client, topic_arn: str, cliente: str) -> str:
    mensaje = {
        "evento": "pedido_creado",
        "pedido_id": str(uuid.uuid4()),
        "cliente": cliente,
        "items": ["sku-123", "sku-456"],
        "timestamp": datetime.now(timezone.utc).isoformat(),
    }

    response = sns_client.publish(
        TopicArn=topic_arn,
        Message=json.dumps(mensaje),
        Subject="Nuevo Pedido Creado",
    )

    print(f"Mensaje publicado. MessageId={response['MessageId']}")
    print(json.dumps(mensaje, indent=2, ensure_ascii=False))
    return response["MessageId"]


def main() -> None:
    cliente = sys.argv[1] if len(sys.argv) > 1 else "cliente-demo"

    sns = boto3.client(
        "sns",
        endpoint_url=ENDPOINT_URL,
        region_name=REGION,
        aws_access_key_id="test",
        aws_secret_access_key="test",
    )

    topic_arn = get_topic_arn(sns)
    publicar_evento_pedido(sns, topic_arn, cliente)


if __name__ == "__main__":
    main()
