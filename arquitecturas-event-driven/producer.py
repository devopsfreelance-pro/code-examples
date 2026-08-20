#!/usr/bin/env python3
"""
Productor de eventos para el ejemplo de arquitectura event-driven.

Publica un evento `PedidoCreado` en el topic `pedidos` de Kafka, simulando
el primer paso del flujo descrito en el post: un cliente hace un pedido y
el resto de los servicios (inventario, notificaciones, etc.) reaccionan de
forma desacoplada, sin que este productor sepa nada de ellos.
"""
import json
import sys
import time
import uuid

from kafka import KafkaProducer
from kafka.errors import NoBrokersAvailable

BOOTSTRAP_SERVERS = ["localhost:9092"]
TOPIC = "pedidos"


def build_producer(retries: int = 10, delay_seconds: int = 3) -> KafkaProducer:
    """Reintenta la conexión mientras Kafka termina de arrancar."""
    last_error = None
    for attempt in range(1, retries + 1):
        try:
            return KafkaProducer(
                bootstrap_servers=BOOTSTRAP_SERVERS,
                value_serializer=lambda v: json.dumps(v).encode("utf-8"),
                acks="all",
            )
        except NoBrokersAvailable as exc:
            last_error = exc
            print(f"[productor] Kafka no disponible todavía (intento {attempt}/{retries}), reintentando...")
            time.sleep(delay_seconds)
    raise RuntimeError("No se pudo conectar a Kafka") from last_error


def main() -> None:
    total = float(sys.argv[1]) if len(sys.argv) > 1 else 99.99

    producer = build_producer()

    evento = {
        "tipo": "PedidoCreado",
        "pedido_id": str(uuid.uuid4())[:8],
        "cliente_id": "678",
        "total": total,
    }

    print(f"[productor] Publicando evento: {evento}")
    future = producer.send(TOPIC, evento)
    future.get(timeout=10)  # confirma que Kafka aceptó el evento
    producer.flush()
    print("[productor] Evento publicado y confirmado por el broker (acks=all).")


if __name__ == "__main__":
    main()
