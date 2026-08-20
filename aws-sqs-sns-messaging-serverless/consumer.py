#!/usr/bin/env python3
"""Consume mensajes de una cola SQS suscrita al topic de fan-out.

Uso:
    python3 consumer.py procesamiento-inventario
    python3 consumer.py procesamiento-facturacion
"""
import json
import sys

import boto3

ENDPOINT_URL = "http://localhost:4566"
REGION = "us-east-1"


def procesar_mensajes(sqs_client, queue_url: str) -> None:
    print(f"Escuchando en {queue_url} (Ctrl+C para salir)...")
    while True:
        response = sqs_client.receive_message(
            QueueUrl=queue_url,
            MaxNumberOfMessages=10,
            WaitTimeSeconds=5,  # long polling
            MessageAttributeNames=["All"],
        )

        mensajes = response.get("Messages", [])
        if not mensajes:
            continue

        for mensaje in mensajes:
            try:
                # SNS envuelve el mensaje original dentro del campo "Message"
                envoltorio = json.loads(mensaje["Body"])
                datos = json.loads(envoltorio["Message"])

                print(f"Pedido recibido: {datos['pedido_id']} - cliente: {datos['cliente']}")

                sqs_client.delete_message(
                    QueueUrl=queue_url,
                    ReceiptHandle=mensaje["ReceiptHandle"],
                )
            except Exception as exc:  # noqa: BLE001 - demo simple, se loguea y sigue
                print(f"Error procesando mensaje: {exc}")


def main() -> None:
    if len(sys.argv) != 2:
        print("Uso: python3 consumer.py <nombre-de-cola>")
        sys.exit(1)

    queue_name = sys.argv[1]

    sqs = boto3.client(
        "sqs",
        endpoint_url=ENDPOINT_URL,
        region_name=REGION,
        aws_access_key_id="test",
        aws_secret_access_key="test",
    )

    queue_url = sqs.get_queue_url(QueueName=queue_name)["QueueUrl"]

    try:
        procesar_mensajes(sqs, queue_url)
    except KeyboardInterrupt:
        print("\nConsumer detenido.")


if __name__ == "__main__":
    main()
