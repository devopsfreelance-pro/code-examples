#!/usr/bin/env python3
"""
Consumidor del servicio de notificaciones.

Se suscribe al MISMO topic `pedidos` que consumer_inventario.py, pero con un
consumer group distinto (`notificaciones-service`). Esto demuestra que se
puede agregar un nuevo consumidor sin tocar al productor ni a los demás
consumidores: cada grupo recibe una copia completa del stream de eventos.
"""
import json
import time

from kafka import KafkaConsumer
from kafka.errors import NoBrokersAvailable

BOOTSTRAP_SERVERS = ["localhost:9092"]
TOPIC = "pedidos"
GROUP_ID = "notificaciones-service"


def build_consumer(retries: int = 10, delay_seconds: int = 3) -> KafkaConsumer:
    last_error = None
    for attempt in range(1, retries + 1):
        try:
            return KafkaConsumer(
                TOPIC,
                bootstrap_servers=BOOTSTRAP_SERVERS,
                value_deserializer=lambda m: json.loads(m.decode("utf-8")),
                group_id=GROUP_ID,
                auto_offset_reset="earliest",
            )
        except NoBrokersAvailable as exc:
            last_error = exc
            print(f"[notificaciones] Kafka no disponible todavía (intento {attempt}/{retries}), reintentando...")
            time.sleep(delay_seconds)
    raise RuntimeError("No se pudo conectar a Kafka") from last_error


def main() -> None:
    print(f"[notificaciones] Escuchando topic '{TOPIC}' como grupo '{GROUP_ID}'...")
    consumer = build_consumer()

    for message in consumer:
        evento = message.value
        print(
            f"[notificaciones] Procesando {evento['tipo']} para pedido {evento['pedido_id']}: "
            f"enviando email de confirmación al cliente {evento['cliente_id']}"
        )


if __name__ == "__main__":
    main()
