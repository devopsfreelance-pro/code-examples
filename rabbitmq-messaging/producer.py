#!/usr/bin/env python3
"""
Publica eventos de pedidos en un topic exchange, tal como describe el post
"RabbitMQ: Guia completa de messaging para DevOps".

Declara:
  - exchange "orders" (topic, durable)
  - cola "order_processing" (durable) con dead-letter exchange
  - binding "order.created.*"

Publica 5 mensajes con routing keys distintas y usa publisher confirms
para verificar que RabbitMQ recibio cada mensaje.
"""
import json
import sys
import time
import uuid

import pika

HOST = "localhost"
PORT = 5672
USER = "admin"
PASSWORD = "secure_password"

REGIONS = ["ar", "br", "mx", "cl", "us"]


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

    # Dead-letter exchange/queue para mensajes rechazados sin reintento
    channel.exchange_declare(exchange="orders.dlx", exchange_type="fanout", durable=True)
    channel.queue_declare(queue="order_processing.dlq", durable=True)
    channel.queue_bind(exchange="orders.dlx", queue="order_processing.dlq")

    # Exchange y cola principales
    channel.exchange_declare(exchange="orders", exchange_type="topic", durable=True)
    channel.queue_declare(
        queue="order_processing",
        durable=True,
        arguments={
            "x-dead-letter-exchange": "orders.dlx",
        },
    )
    channel.queue_bind(exchange="orders", queue="order_processing", routing_key="order.created.*")

    # Publisher confirms: RabbitMQ confirma la recepcion de cada mensaje
    channel.confirm_delivery()

    for i in range(1, 6):
        region = REGIONS[i % len(REGIONS)]
        order = {
            "order_id": i,
            "customer_id": 1000 + i,
            "items": [{"sku": "SKU-1", "qty": 2}],
            "total": 49.90 * i,
            "region": region,
            "timestamp": time.time(),
        }

        properties = pika.BasicProperties(
            delivery_mode=2,  # mensaje persistente
            content_type="application/json",
            message_id=str(uuid.uuid4()),
            timestamp=int(time.time()),
        )

        routing_key = f"order.created.{region}"
        try:
            # Con confirm_delivery() activo, basic_publish bloquea hasta
            # recibir el ack de RabbitMQ y lanza UnroutableError si el
            # mensaje no pudo enrutarse a ninguna cola (mandatory=True).
            channel.basic_publish(
                exchange="orders",
                routing_key=routing_key,
                body=json.dumps(order),
                properties=properties,
                mandatory=True,
            )
            estado = "confirmado"
        except pika.exceptions.UnroutableError:
            estado = "SIN ENRUTAR (revisar bindings)"

        print(f"-> publicado order_id={i} routing_key={routing_key} [{estado}]")

    connection.close()
    print("\nListo. Corre consumer.py para procesar la cola order_processing.")


if __name__ == "__main__":
    try:
        main()
    except pika.exceptions.AMQPConnectionError as exc:
        print(f"No se pudo conectar a RabbitMQ en {HOST}:{PORT}: {exc}", file=sys.stderr)
        sys.exit(1)
