#!/usr/bin/env python3
"""
Consumidor del servicio de inventario.

Se suscribe al topic `pedidos` como parte del consumer group
`inventario-service` y reacciona a cada `PedidoCreado` reservando stock.
No conoce al productor ni a otros consumidores (ver consumer_notificaciones.py):
ese desacoplamiento es el punto central de una arquitectura event-driven.
"""
import json
import time

from kafka import KafkaConsumer
from kafka.errors import NoBrokersAvailable

BOOTSTRAP_SERVERS = ["localhost:9092"]
TOPIC = "pedidos"
GROUP_ID = "inventario-service"


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
            print(f"[inventario] Kafka no disponible todavía (intento {attempt}/{retries}), reintentando...")
            time.sleep(delay_seconds)
    raise RuntimeError("No se pudo conectar a Kafka") from last_error


def main() -> None:
    print(f"[inventario] Escuchando topic '{TOPIC}' como grupo '{GROUP_ID}'...")
    consumer = build_consumer()

    for message in consumer:
        evento = message.value
        print(
            f"[inventario] Procesando {evento['tipo']} para pedido {evento['pedido_id']}: "
            f"reservando stock por ${evento['total']}"
        )


if __name__ == "__main__":
    main()
