#!/usr/bin/env python3
"""
Consumidor que ilustra dos ideas centrales del post:

1. Grupos de consumidores: el consumidor se une al grupo "fraud-detector"
   y Kafka le asigna particiones automaticamente.
2. Un filtro de streaming equivalente al ejemplo de Kafka Streams del post
   (filter + count de transacciones sospechosas), implementado aqui con un
   consumidor simple que publica las alertas en el topic "fraud-alerts".

Ejecutar en dos terminales con el mismo group_id demuestra el rebalanceo:
cada particion queda asignada a un unico consumidor del grupo.
"""
import json

from kafka import KafkaConsumer, KafkaProducer

BOOTSTRAP_SERVERS = "localhost:9092"
SOURCE_TOPIC = "transactions"
ALERTS_TOPIC = "fraud-alerts"
GROUP_ID = "fraud-detector"
FRAUD_THRESHOLD = 10000


def main():
    consumer = KafkaConsumer(
        SOURCE_TOPIC,
        bootstrap_servers=BOOTSTRAP_SERVERS,
        group_id=GROUP_ID,
        auto_offset_reset="earliest",
        enable_auto_commit=True,
        key_deserializer=lambda k: k.decode("utf-8") if k else None,
        value_deserializer=lambda v: json.loads(v.decode("utf-8")),
        consumer_timeout_ms=15000,
    )

    producer = KafkaProducer(
        bootstrap_servers=BOOTSTRAP_SERVERS,
        key_serializer=lambda k: k.encode("utf-8"),
        value_serializer=lambda v: json.dumps(v).encode("utf-8"),
    )

    print(f"Consumidor unido al grupo '{GROUP_ID}', escuchando '{SOURCE_TOPIC}'...")
    alert_counts = {}

    for message in consumer:
        txn = message.value
        print(
            f"Leido {txn['txn_id']} (user={txn['user_id']}, amount={txn['amount']}) "
            f"de partition={message.partition} offset={message.offset}"
        )

        if txn["amount"] > FRAUD_THRESHOLD:
            user_id = txn["user_id"]
            alert_counts[user_id] = alert_counts.get(user_id, 0) + 1

            alert = {
                "user_id": user_id,
                "txn_id": txn["txn_id"],
                "amount": txn["amount"],
                "alert_count_for_user": alert_counts[user_id],
            }
            producer.send(ALERTS_TOPIC, key=user_id, value=alert)
            print(f"  -> ALERTA DE FRAUDE publicada en '{ALERTS_TOPIC}': {alert}")

    producer.flush()
    producer.close()
    consumer.close()
    print("Sin mensajes nuevos durante 15s, finalizando. Resumen de alertas por usuario:")
    for user_id, count in alert_counts.items():
        print(f"  {user_id}: {count} alerta(s)")


if __name__ == "__main__":
    main()
