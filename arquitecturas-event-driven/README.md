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
