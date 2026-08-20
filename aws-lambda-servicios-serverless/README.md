# AWS Lambda: SQS -> Lambda -> DynamoDB con LocalStack

Ejemplo de código para el post [AWS Lambda: Guía Definitiva de Arquitecturas Serverless 2025](https://www.devopsfreelance.pro/blog/posts/aws-lambda-servicios-serverless/).

## Qué demuestra

El patrón de procesamiento asíncrono con reintentos que describe el post en la
sección "Fuentes de Eventos: SQS": una función Lambda se dispara cuando llegan
mensajes a una cola SQS, guarda cada pedido en DynamoDB y usa
`batchItemFailures` para que SQS reintente solo los mensajes que fallaron
(no todo el lote). Todo corre localmente contra [LocalStack](https://localstack.cloud/),
sin necesidad de una cuenta de AWS real ni de gastar dinero.

Archivos:
- `handler.py`: código de la función Lambda (idéntico en estructura al ejemplo del post).
- `docker-compose.yml`: levanta LocalStack con los servicios Lambda, SQS, DynamoDB e IAM.
- `deploy.sh`: crea la tabla, la cola, empaqueta y despliega la Lambda, y conecta SQS como event source.
- `send-order.sh`: envía un pedido de prueba a la cola y muestra el resultado en DynamoDB.

## Requisitos

- Docker y Docker Compose
- AWS CLI v2 (`aws --version`)
- `zip` (viene preinstalado en la mayoría de distros; en Debian/Ubuntu: `sudo apt install zip`)

No hace falta cuenta de AWS: LocalStack acepta cualquier credencial dummy
(`AWS_ACCESS_KEY_ID=test`, ya seteada en los scripts).

## Pasos para correrlo

```bash
cd aws-lambda-servicios-serverless

# 1. Levantar LocalStack
docker compose up -d

# 2. Esperar a que el healthcheck pase (unos 10-15 segundos)
docker compose ps

# 3. Dar permisos de ejecución a los scripts
chmod +x deploy.sh send-order.sh

# 4. Crear tabla, cola y desplegar la Lambda
./deploy.sh

# 5. Enviar un pedido de prueba (podés pasar un ID distinto como argumento)
./send-order.sh 1001
```

Para ver los logs de la Lambda en tiempo real mientras se ejecuta el paso 5:

```bash
docker compose logs -f localstack
```

Para limpiar todo al terminar:

```bash
docker compose down -v
rm -f function.zip
```

## Salida esperada

Al correr `./send-order.sh 1001` deberías ver:

```
==> Enviando pedido 1001 a la cola
==> Esperando 3s a que la Lambda procese el mensaje
==> Contenido actual de la tabla Orders:
---------------------------------------------------------------
|                              Scan                            |
+----------------------------------------------------------------+
||                            Items                             ||
|+------------+----------------------------+----------+---------+|
||  customer  |          order_id          |  status  |  total  ||
|+------------+----------------------------+----------+---------+|
||  Juan Perez|  1001                      |processing|  149.9  ||
|+------------+----------------------------+----------+---------+|
```

Si volvés a correr `./send-order.sh` con otro ID, el nuevo pedido se agrega
a la tabla junto al anterior.

## Notas

- `docker-reuse` como `LAMBDA_EXECUTOR` hace que LocalStack levante un
  contenedor Docker real para ejecutar el runtime Python de la Lambda, igual
  que en AWS (por eso el `docker-compose.yml` monta el socket de Docker).
- El código de `handler.py` es intencionalmente el mismo del post (sección
  SQS), con el agregado de leer `TABLE_NAME` y `DYNAMODB_ENDPOINT_URL` desde
  variables de entorno para poder apuntar a LocalStack en vez de a AWS real.
- Para desplegar esto en una cuenta de AWS real, sacar `endpoint_url` del
  cliente boto3 y `--endpoint-url` de los comandos de `aws`, y crear un rol
  IAM real en vez de `arn:aws:iam::000000000000:role/lambda-role`.
