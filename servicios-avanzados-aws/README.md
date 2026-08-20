# Ejemplo: arquitectura event-driven S3 -> Lambda -> DynamoDB

Post: [AWS Advanced: Arquitecturas Empresariales Escalables 2026](https://www.devopsfreelance.pro/blog/posts/servicios-avanzados-aws/)

## Que demuestra

El post menciona como patron central de las arquitecturas serverless avanzadas
el siguiente flujo: *"S3 disparando funciones Lambda cuando se cargan archivos,
procesando datos y almacenando resultados en DynamoDB, todo sin gestionar un
solo servidor"*.

Este ejemplo reproduce exactamente ese patron de forma local, sin usar una
cuenta de AWS real:

1. Un bucket S3 recibe un archivo.
2. La subida dispara automaticamente una funcion Lambda (evento `s3:ObjectCreated:*`).
3. La Lambda procesa el evento y escribe un item en una tabla DynamoDB.
4. Toda la infraestructura (bucket, tabla, rol IAM, funcion y el trigger)
   se define como codigo con Terraform.

Se usa [LocalStack](https://www.localstack.cloud/) para emular S3, Lambda,
DynamoDB e IAM en contenedores locales, así no hace falta ninguna cuenta de
AWS ni tarjeta de credito.

## Requisitos

- Docker y Docker Compose
- Terraform >= 1.5
- AWS CLI v2 (`aws --version`)
- `curl` (para el health check de LocalStack)

No hace falta instalar boto3 aparte: el runtime `python3.12` de Lambda ya lo
incluye.

## Estructura

```
servicios-avanzados-aws/
├── docker-compose.yml       # LocalStack (S3, Lambda, DynamoDB, IAM)
├── terraform/
│   └── main.tf              # Bucket, tabla, rol, funcion Lambda y trigger S3
├── lambda/
│   └── handler.py           # Codigo de la funcion Lambda
└── scripts/
    └── deploy_and_test.sh   # Aplica Terraform, sube un archivo y verifica el resultado
```

## Pasos para correrlo

1. Levantar LocalStack:

   ```bash
   cd servicios-avanzados-aws
   docker compose up -d
   ```

2. Dar permisos de ejecucion al script (una sola vez) y correr el flujo completo:

   ```bash
   chmod +x scripts/deploy_and_test.sh
   ./scripts/deploy_and_test.sh
   ```

   Este script:
   - espera a que LocalStack este disponible,
   - corre `terraform init` y `terraform apply -auto-approve` dentro de `terraform/`,
   - sube un archivo JSON de prueba (`pedido-test.json`) al bucket creado,
   - espera unos segundos a que la Lambda procese el evento,
   - consulta DynamoDB por el item resultante.

3. (Opcional) Repetir la prueba subiendo otro archivo manualmente:

   ```bash
   echo '{"otro": "pedido"}' > /tmp/otro.json
   aws --endpoint-url=http://localhost:4566 s3 cp /tmp/otro.json s3://advanced-aws-uploads/otro.json
   sleep 5
   aws --endpoint-url=http://localhost:4566 dynamodb scan --table-name processed-files
   ```

4. Ver los logs de la funcion (utiles para debug):

   ```bash
   docker logs localstack | grep -i "Procesado"
   ```

5. Limpiar todo al terminar:

   ```bash
   cd terraform && terraform destroy -auto-approve && cd ..
   docker compose down -v
   ```

## Salida esperada

El paso final del script (`dynamodb get-item`) devuelve algo similar a:

```json
{
    "Item": {
        "file_key": {
            "S": "pedido-test.json"
        },
        "bucket": {
            "S": "advanced-aws-uploads"
        },
        "size_bytes": {
            "N": "38"
        },
        "status": {
            "S": "PROCESSED"
        }
    }
}
```

Esto confirma que el archivo subido a S3 disparo la Lambda, y que la Lambda
escribio correctamente el resultado en DynamoDB, sin haber gestionado ni
aprovisionado ningun servidor manualmente.

## Notas

- El ejemplo usa credenciales dummy (`test`/`test`) porque corre 100% contra
  LocalStack, no contra una cuenta de AWS real. Si adaptás esto a AWS real,
  reemplazá el bloque `provider "aws"` de `terraform/main.tf` por credenciales
  reales gestionadas via variables de entorno o un rol IAM, nunca hardcodeadas.
- LocalStack ejecuta cada invocacion de Lambda en un contenedor Docker propio
  (`LAMBDA_EXECUTOR=docker` en `docker-compose.yml`), por eso se monta el
  socket de Docker del host.
