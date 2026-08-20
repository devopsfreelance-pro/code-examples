#!/usr/bin/env python3
"""
Productor de transacciones para el demo de particionamiento en Kafka.

Envia mensajes al topic "transactions" usando el user_id como clave de
particionamiento. Esto ilustra el concepto central del post: mensajes con
la misma clave siempre van a la misma particion, preservando el orden de
eventos de un mismo usuario.
"""
import json
import random
import time

from kafka import KafkaProducer
from kafka.admin import KafkaAdminClient, NewTopic
from kafka.errors import TopicAlreadyExistsError

BOOTSTRAP_SERVERS = "localhost:9092"
TOPIC = "transactions"
NUM_PARTITIONS = 3


def ensure_topic():
    admin = KafkaAdminClient(bootstrap_servers=BOOTSTRAP_SERVERS)
    try:
        admin.create_topics(
            [NewTopic(name=TOPIC, num_partitions=NUM_PARTITIONS, replication_factor=1)]
        )
        print(f"Topic '{TOPIC}' creado con {NUM_PARTITIONS} particiones.")
    except TopicAlreadyExistsError:
        print(f"Topic '{TOPIC}' ya existe.")
    finally:
        admin.close()


def main():
    ensure_topic()

    producer = KafkaProducer(
        bootstrap_servers=BOOTSTRAP_SERVERS,
        key_serializer=lambda k: k.encode("utf-8"),
        value_serializer=lambda v: json.dumps(v).encode("utf-8"),
    )

    users = ["user-1", "user-2", "user-3", "user-4"]

    print("Enviando 20 transacciones (Ctrl+C para detener antes)...")
    for i in range(20):
        user_id = random.choice(users)
        amount = random.choice([50, 250, 1200, 9800, 15000, 42000])
        txn = {
            "txn_id": f"txn-{i}",
            "user_id": user_id,
            "amount": amount,
            "timestamp": time.time(),
        }

        future = producer.send(TOPIC, key=user_id, value=txn)
        record_metadata = future.get(timeout=10)

        print(
            f"Enviado {txn['txn_id']} (user={user_id}, amount={amount}) -> "
            f"partition={record_metadata.partition} offset={record_metadata.offset}"
        )
        time.sleep(0.3)

    producer.flush()
    producer.close()
    print("Listo. Todas las transacciones fueron enviadas.")


if __name__ == "__main__":
    main()
