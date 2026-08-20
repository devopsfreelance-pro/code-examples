#!/usr/bin/env python3
"""
Consume mensajes de "order_processing", confirmando (ack) los validos y
rechazando (nack, sin reintento) los que no se pueden parsear -- estos
caen en la dead-letter queue "order_processing.dlq" segun el binding
configurado en producer.py.

Usa basic_get en un bucle hasta vaciar la cola (en vez de start_consuming
indefinido), para que la demo termine sola.
"""
import json
import sys

import pika

HOST = "localhost"
PORT = 5672
USER = "admin"
PASSWORD = "secure_password"


def main():
    credentials = pika.PlainCredentials(USER, PASSWORD)
    parameters = pika.ConnectionParameters(
        host=HOST,
        port=PORT,
        credentials=credentials,
        heartbeat=600,
        blocked_connection_timeout=300,
    )

    connection = pika.BlockingConnection(parameters)
    channel = connection.channel()

    channel.queue_declare(
        queue="order_processing",
        durable=True,
        arguments={"x-dead-letter-exchange": "orders.dlx"},
    )

    channel.basic_qos(prefetch_count=10)

    processed = 0
    rejected = 0
    print("Consumiendo order_processing hasta vaciar la cola...")

    while True:
        method, properties, body = channel.basic_get(queue="order_processing", auto_ack=False)
        if method is None:
            break  # cola vacia, fin de la demo

        try:
            order = json.loads(body)
            print(
                f"<- procesado order_id={order['order_id']} "
                f"region={order['region']} total={order['total']:.2f}"
            )
            channel.basic_ack(delivery_tag=method.delivery_tag)
            processed += 1
        except json.JSONDecodeError:
            print("<- mensaje malformado, enviado a dead-letter queue")
            channel.basic_reject(delivery_tag=method.delivery_tag, requeue=False)
            rejected += 1

    connection.close()
    print(f"\nTotal procesados: {processed} | rechazados a DLQ: {rejected}")


if __name__ == "__main__":
    try:
        main()
    except pika.exceptions.AMQPConnectionError as exc:
        print(f"No se pudo conectar a RabbitMQ en {HOST}:{PORT}: {exc}", file=sys.stderr)
        sys.exit(1)
