# Event-Driven Architecture: Runnable Example with Kafka

Post: [Event-Driven Architecture: The Complete DevOps Guide](https://www.devopsfreelance.pro/blog/en/posts/event-driven-architecture/)

## What This Example Demonstrates

The e-commerce order system described in the post, stripped down to its
essence: a **producer** publishes an `OrderCreated` event to a Kafka topic,
and **two independent consumers** (inventory and notifications) each
process it on their own, without knowing about each other.

Running the example shows live the central point of an event-driven
architecture: adding the notifications consumer didn't require touching
either the producer or the inventory consumer. Each one uses its own Kafka
`group_id`, so both receive a full copy of the event stream and can fail
or restart independently.

Files:

- `docker-compose.yml`: spins up a single-node Kafka broker in KRaft mode
  (no Zookeeper), meant only for local testing.
- `producer.py`: publishes an `OrderCreated` event to the `pedidos` topic.
- `consumer_inventario.py`: consumes `pedidos` as the `inventario-service`
  group and simulates reserving stock.
- `consumer_notificaciones.py`: consumes the same topic as the
  `notificaciones-service` group and simulates sending a confirmation email.

## Requirements

- Docker and Docker Compose.
- Python 3.9+ with `pip`.
- Port `9092` free on your machine.

## Steps to Run It

### 1. Start Kafka

```bash
docker compose up -d
```

Wait for the healthcheck to go green (about 10-20 seconds):

```bash
docker compose ps
```

### 2. Install Python dependencies

```bash
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

### 3. Start the two consumers (in two separate terminals)

Terminal A:

```bash
source venv/bin/activate
python3 consumer_inventario.py
```

Terminal B:

```bash
source venv/bin/activate
python3 consumer_notificaciones.py
```

Both will sit waiting for events and print:

```
[inventario] Escuchando topic 'pedidos' como grupo 'inventario-service'...
[notificaciones] Escuchando topic 'pedidos' como grupo 'notificaciones-service'...
```

### 4. Publish an event (in a third terminal)

```bash
source venv/bin/activate
python3 producer.py 149.90
```

Expected producer output:

```
[productor] Publicando evento: {'tipo': 'PedidoCreado', 'pedido_id': 'a1b2c3d4', 'cliente_id': '678', 'total': 149.9}
[productor] Evento publicado y confirmado por el broker (acks=all).
```

And on each consumer, almost instantly:

```
[inventario] Procesando PedidoCreado para pedido a1b2c3d4: reservando stock por $149.9
```

```
[notificaciones] Procesando PedidoCreado para pedido a1b2c3d4: enviando email de confirmación al cliente 678
```

You can run `producer.py` several times in a row (with or without an amount
as an argument) and watch both consumers process each event independently
and in parallel.

### 5. Tear it all down

```bash
docker compose down -v
```

## Note

This example uses a single broker with no authentication and no
persistence configured beyond Kafka's defaults: it's only meant to help
you understand the producer/consumer/event-bus pattern locally, not for
production.

---

## 🇪🇸 Versión en español

# Arquitecturas Event-Driven: ejemplo ejecutable con Kafka

Post: [Arquitecturas Event-Driven: Guía Definitiva para DevOps](https://www.devopsfreelance.pro/blog/posts/arquitecturas-event-driven/)

## Qué demuestra este ejemplo

El sistema de pedidos de e-commerce que describe el post, simplificado a su
esencia: un **productor** publica un evento `PedidoCreado` en un topic de
Kafka, y **dos consumidores independientes** (inventario y notificaciones)
lo procesan cada uno por su lado, sin conocerse entre sí.

Corriendo el ejemplo se ve en vivo el punto central de una arquitectura
event-driven: agregar el consumidor de notificaciones no requirió tocar ni
al productor ni al consumidor de inventario. Cada uno usa su propio
`group_id` de Kafka, así que ambos reciben una copia completa del stream de
eventos y pueden fallar o reiniciarse de forma independiente.

Archivos:

- `docker-compose.yml`: levanta un broker Kafka de un solo nodo en modo
  KRaft (sin Zookeeper), pensado solo para probar en local.
- `producer.py`: publica un evento `PedidoCreado` en el topic `pedidos`.
- `consumer_inventario.py`: consume `pedidos` como grupo `inventario-service`
  y simula la reserva de stock.
- `consumer_notificaciones.py`: consume el mismo topic como grupo
  `notificaciones-service` y simula el envío de un email.

## Requisitos

- Docker y Docker Compose.
- Python 3.9+ con `pip`.
- Puerto `9092` libre en tu máquina.

## Pasos para correrlo

### 1. Levantar Kafka

```bash
docker compose up -d
```

Esperá a que el healthcheck esté en verde (unos 10-20 segundos):

```bash
docker compose ps
```

### 2. Instalar dependencias de Python

```bash
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

### 3. Levantar los dos consumidores (en dos terminales separadas)

Terminal A:

```bash
source venv/bin/activate
python3 consumer_inventario.py
```

Terminal B:

```bash
source venv/bin/activate
python3 consumer_notificaciones.py
```

Ambos van a quedar esperando eventos e imprimen:

```
[inventario] Escuchando topic 'pedidos' como grupo 'inventario-service'...
[notificaciones] Escuchando topic 'pedidos' como grupo 'notificaciones-service'...
```

### 4. Publicar un evento (en una tercera terminal)

```bash
source venv/bin/activate
python3 producer.py 149.90
```

Salida esperada del productor:

```
[productor] Publicando evento: {'tipo': 'PedidoCreado', 'pedido_id': 'a1b2c3d4', 'cliente_id': '678', 'total': 149.9}
[productor] Evento publicado y confirmado por el broker (acks=all).
```

Y en cada consumidor, casi al instante:

```
[inventario] Procesando PedidoCreado para pedido a1b2c3d4: reservando stock por $149.9
```

```
[notificaciones] Procesando PedidoCreado para pedido a1b2c3d4: enviando email de confirmación al cliente 678
```

Podés correr `producer.py` varias veces seguidas (con o sin monto como
argumento) y ver cómo ambos consumidores procesan cada evento de forma
independiente y en paralelo.

### 5. Apagar todo

```bash
docker compose down -v
```

## Nota

Este ejemplo usa un único broker sin autenticación ni persistencia
configurada más allá de la que trae Kafka por defecto: es solo para
entender el patrón productor/consumidor/bus de eventos en local, no para
producción.
