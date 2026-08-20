# AWS SQS + SNS: patrón fan-out con LocalStack

Post: [AWS SQS: Guía completa de messaging serverless en 2026](https://www.devopsfreelance.pro/blog/posts/aws-sqs-sns-messaging-serverless/)

## Qué demuestra este ejemplo

El patrón central del post: **fan-out con SNS y SQS**. Un topic de SNS
(`eventos-pedidos`) distribuye cada mensaje publicado a dos colas SQS
suscritas (`procesamiento-inventario` y `procesamiento-facturacion`), de
forma que cada servicio consumidor procesa el mismo evento a su propio
ritmo, de forma desacoplada e independiente.

Todo corre localmente contra [LocalStack](https://www.localstack.cloud/),
sin necesidad de una cuenta de AWS real ni de gastar dinero.

## Requisitos

- Docker y Docker Compose
- Python 3.9+
- AWS CLI v2 (`aws --version`)
- `pip` para instalar dependencias de Python

## Pasos para correrlo

### 1. Levantar LocalStack

```bash
docker compose up -d
```

Esperá a que el healthcheck esté OK (unos segundos):

```bash
docker compose ps
```

### 2. Instalar dependencias de Python

```bash
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

### 3. Crear el topic SNS y las colas SQS (fan-out)

```bash
chmod +x setup.sh
./setup.sh
```

Salida esperada (resumida):

```
== Creando topic SNS: eventos-pedidos ==
TopicArn: arn:aws:sns:us-east-1:000000000000:eventos-pedidos
== Creando cola SQS: procesamiento-inventario ==
...
== Creando cola SQS: procesamiento-facturacion ==
...
Setup completo. TopicArn para publicar: arn:aws:sns:us-east-1:000000000000:eventos-pedidos
```

### 4. Levantar los consumidores (en dos terminales separadas)

Terminal A:

```bash
source venv/bin/activate
python3 consumer.py procesamiento-inventario
```

Terminal B:

```bash
source venv/bin/activate
python3 consumer.py procesamiento-facturacion
```

Ambos quedan escuchando con long polling (`WaitTimeSeconds=5`).

### 5. Publicar un evento

En una tercera terminal:

```bash
source venv/bin/activate
python3 publisher.py "cliente-demo"
```

Salida esperada del publisher:

```
Mensaje publicado. MessageId=xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx
{
  "evento": "pedido_creado",
  "pedido_id": "...",
  "cliente": "cliente-demo",
  "items": ["sku-123", "sku-456"],
  "timestamp": "2026-08-20T..."
}
```

Y en **cada** terminal de consumidor vas a ver el mismo evento recibido,
demostrando el fan-out:

```
Pedido recibido: <pedido_id> - cliente: cliente-demo
```

### 6. Limpiar

```bash
docker compose down -v
```

## Notas

- Las credenciales `test`/`test` son las que usa LocalStack por defecto,
  no son secretos reales; no requieren ninguna cuenta de AWS.
- Este ejemplo usa colas estándar (no FIFO) y no configura Dead Letter
  Queue, para mantenerlo mínimo. El post explica cómo agregar DLQ y
  ajustar el `visibility timeout` para producción.
- Para replicar esto contra AWS real, alcanza con quitar el parámetro
  `endpoint_url` de los clientes boto3 y usar credenciales de una cuenta
  propia con permisos sobre SNS/SQS.
