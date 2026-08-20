# RabbitMQ Messaging - Ejemplo ejecutable

Post relacionado: [RabbitMQ: Guía completa de messaging para DevOps](https://www.devopsfreelance.pro/blog/posts/rabbitmq-messaging/)

## Qué demuestra

Un flujo mínimo de mensajería con RabbitMQ usando el patrón central del
post (topic exchange + cola durable + acknowledgments):

- `producer.py` declara un exchange `orders` de tipo **topic** y una cola
  `order_processing` con **dead-letter exchange**, y publica 5 pedidos con
  routing keys distintas (`order.created.ar`, `order.created.br`, etc.)
  usando **publisher confirms** para verificar que RabbitMQ recibió cada
  mensaje.
- `consumer.py` consume esa cola, hace `basic_ack` de los mensajes válidos
  y `basic_reject` (sin reintento) de los que no puede parsear, que caen
  en la cola `order_processing.dlq` tal como describe la sección de dead
  letter exchanges del post.
- La UI de gestión de RabbitMQ (puerto 15672) permite ver en vivo el
  exchange, el binding y los mensajes fluyendo por la cola.

## Requisitos

- Docker y Docker Compose
- Python 3.9+ y `pip`

## Pasos para correrlo

```bash
# 1. Levantar RabbitMQ (con plugin de gestión habilitado)
docker compose up -d

# 2. Esperar a que el healthcheck esté OK (unos segundos)
docker compose ps

# 3. Instalar el cliente Python
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt

# 4. Publicar 5 pedidos de ejemplo
python3 producer.py

# 5. Consumirlos
python3 consumer.py
```

Credenciales de la UI de gestión (solo para este entorno local de
demo): usuario `admin`, password `secure_password`, disponible en
http://localhost:15672 mientras `docker compose up` está corriendo.

## Salida esperada

`producer.py`:

```
-> publicado order_id=1 routing_key=order.created.br [confirmado]
-> publicado order_id=2 routing_key=order.created.mx [confirmado]
-> publicado order_id=3 routing_key=order.created.cl [confirmado]
-> publicado order_id=4 routing_key=order.created.us [confirmado]
-> publicado order_id=5 routing_key=order.created.ar [confirmado]

Listo. Corre consumer.py para procesar la cola order_processing.
```

`consumer.py`:

```
Consumiendo order_processing hasta vaciar la cola...
<- procesado order_id=1 region=br total=49.90
<- procesado order_id=2 region=mx total=99.80
<- procesado order_id=3 region=cl total=149.70
<- procesado order_id=4 region=us total=199.60
<- procesado order_id=5 region=ar total=249.50

Total procesados: 5 | rechazados a DLQ: 0
```

## Limpiar

```bash
docker compose down -v
```
