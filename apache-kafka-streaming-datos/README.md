# Apache Kafka: particionamiento, grupos de consumidores y filtrado de streams

Ejemplo de código para el post [Kafka DevOps: Guía práctica para streaming de datos en tiempo real](https://www.devopsfreelance.pro/blog/posts/apache-kafka-streaming-datos/).

## Qué demuestra

El post argumenta que la dificultad real de Kafka está en las decisiones de
particionamiento y en las garantías de entrega, no en levantar un broker.
Este ejemplo levanta un clúster Kafka de un solo nodo (modo KRaft, sin
ZooKeeper) y con dos scripts en Python muestra:

1. **Particionamiento por clave** (`producer.py`): envía transacciones a un
   topic de 3 particiones usando `user_id` como clave. Verás en la salida
   que todas las transacciones de un mismo usuario caen siempre en la misma
   partición, preservando su orden relativo.
2. **Grupos de consumidores** (`consumer.py`): se une al grupo
   `fraud-detector` y Kafka le asigna particiones automáticamente. Si corrés
   una segunda instancia del mismo script en otra terminal con el mismo
   `group_id`, vas a ver el rebalanceo de particiones entre ambos consumidores.
3. **Filtro de streaming** (equivalente al ejemplo de Kafka Streams del
   post): el consumidor filtra transacciones con `amount > 10000` y publica
   una alerta en el topic `fraud-alerts`, replicando con un consumidor
   simple la misma idea que el snippet de `KStream.filter()` del post.

## Requisitos

- Docker y Docker Compose
- Python 3.9+
- Puerto `9092` libre en localhost

No se usan servicios pagos: todo corre en un contenedor local con la imagen
oficial `apache/kafka:3.7.0`.

## Pasos para ejecutarlo

### 1. Levantar Kafka

```bash
docker compose up -d
```

Esperá a que el healthcheck del contenedor esté en estado `healthy`:

```bash
docker compose ps
```

### 2. Instalar dependencias de Python

```bash
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

### 3. Correr el consumidor (en una terminal)

```bash
python3 consumer.py
```

Queda escuchando el topic `transactions`. Se corta solo después de 15
segundos sin mensajes nuevos, así que dejalo corriendo mientras ejecutás el
productor en otra terminal.

### 4. Correr el productor (en otra terminal)

```bash
python3 producer.py
```

Crea el topic `transactions` con 3 particiones (si no existe) y envía 20
transacciones simuladas para 4 usuarios distintos, con montos aleatorios
(algunos por encima de 10000, el umbral de fraude).

## Salida esperada

En la terminal del productor vas a ver algo como:

```
Topic 'transactions' creado con 3 particiones.
Enviando 20 transacciones (Ctrl+C para detener antes)...
Enviado txn-0 (user=user-2, amount=9800) -> partition=2 offset=0
Enviado txn-1 (user=user-3, amount=42000) -> partition=2 offset=1
Enviado txn-2 (user=user-1, amount=250) -> partition=2 offset=2
Enviado txn-3 (user=user-3, amount=1200) -> partition=2 offset=3
Enviado txn-4 (user=user-4, amount=9800) -> partition=1 offset=0
...
```

Notá que cada `user_id` cae siempre en la misma partición a lo largo de
toda la ejecución (por ejemplo `user-4` siempre en `partition=1`): eso es
el particionamiento por clave en acción. La distribución entre particiones
no tiene por qué ser pareja con pocas claves (es resultado del hash de la
clave), pero el orden por usuario queda garantizado.

En la terminal del consumidor:

```
Consumidor unido al grupo 'fraud-detector', escuchando 'transactions'...
Leido txn-4 (user=user-4, amount=9800) de partition=1 offset=0
Leido txn-9 (user=user-4, amount=250) de partition=1 offset=1
Leido txn-11 (user=user-4, amount=15000) de partition=1 offset=2
  -> ALERTA DE FRAUDE publicada en 'fraud-alerts': {'user_id': 'user-4', 'txn_id': 'txn-11', 'amount': 15000, 'alert_count_for_user': 1}
...
Sin mensajes nuevos durante 15s, finalizando. Resumen de alertas por usuario:
  user-4: 2 alerta(s)
  user-3: 3 alerta(s)
  user-1: 1 alerta(s)
  user-2: 3 alerta(s)
```

Los números exactos varían porque el productor genera montos y usuarios al
azar.

### 5. Ver el topic de alertas (opcional)

```bash
docker exec -it kafka-demo /opt/kafka/bin/kafka-console-consumer.sh \
  --bootstrap-server localhost:19092 \
  --topic fraud-alerts \
  --from-beginning
```

### 6. Limpiar

```bash
docker compose down -v
```

## Archivos

- `docker-compose.yml`: clúster Kafka de un nodo en modo KRaft (sin ZooKeeper).
- `producer.py`: crea el topic y envía transacciones con clave de particionamiento.
- `consumer.py`: consumidor en grupo que filtra transacciones y publica alertas.
- `requirements.txt`: dependencia `kafka-python`.

No hay secretos ni credenciales reales involucradas: el clúster corre
completamente en local, sin autenticación, solo para fines demostrativos.
