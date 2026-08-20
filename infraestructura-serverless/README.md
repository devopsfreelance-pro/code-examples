# Infraestructura Serverless: S3 -> Lambda con Terraform (IaC) sobre LocalStack

Ejemplo de código para el post [Infraestructura Serverless: Guía Práctica para DevOps 2025](https://www.devopsfreelance.pro/blog/posts/infraestructura-serverless/).

## Qué demuestra

El post describe dos ideas centrales: (1) el modelo de ejecución orientado a
eventos (subir un archivo a un bucket dispara una función que la procesa,
extrae metadatos y guarda el resultado, "todo sin gestionar un solo
servidor") y (2) que esa infraestructura debe definirse con **Infrastructure
as Code** usando herramientas como Terraform.

Este ejemplo implementa ambas cosas con Terraform real:

- Un bucket S3 de entrada (`infra-serverless-input`).
- Una función Lambda (Python) que se dispara con el evento
  `s3:ObjectCreated`, lee el objeto subido, extrae sus metadatos
  (tamaño, content-type, timestamp) y escribe un JSON de resultado.
- Un bucket S3 de salida (`infra-serverless-output`) donde queda el JSON
  generado.
- Todo declarado como código versionable (`main.tf`), sin clicks en una
  consola.

Corre 100% local contra [LocalStack](https://localstack.cloud/), sin cuenta
de AWS real ni costo.

Archivos:
- `main.tf`: define ambos buckets, el rol IAM, la función Lambda y el
  trigger S3 -> Lambda, apuntando el provider de AWS a LocalStack.
- `lambda/handler.py`: código de la función (idéntico en estructura al
  ejemplo de procesamiento de imágenes que describe el post, simplificado a
  extracción de metadatos para que corra sin dependencias de imagen).
- `docker-compose.yml`: levanta LocalStack con los servicios S3, Lambda, IAM
  y Logs.

## Requisitos

- Docker y Docker Compose
- Terraform >= 1.5 (`terraform -version`)
- AWS CLI v2, solo para subir el archivo de prueba (`aws --version`)

No hace falta cuenta de AWS: LocalStack acepta cualquier credencial dummy
(el provider ya está configurado con `access_key = "test"` / `secret_key = "test"`).

## Pasos para correrlo

```bash
cd infraestructura-serverless

# 1. Levantar LocalStack
docker compose up -d

# 2. Esperar a que el healthcheck pase (unos 10-15 segundos)
docker compose ps

# 3. Inicializar y aplicar Terraform (crea buckets, rol, Lambda y el trigger)
terraform init
terraform apply -auto-approve

# 4. Subir un archivo de prueba al bucket de entrada
echo '{"hola": "mundo"}' > /tmp/prueba.json

aws --endpoint-url=http://localhost:4566 --region us-east-1 \
  s3 cp /tmp/prueba.json s3://infra-serverless-input/prueba.json

# 5. Esperar unos segundos a que se ejecute la Lambda y revisar el resultado
sleep 5

aws --endpoint-url=http://localhost:4566 --region us-east-1 \
  s3 ls s3://infra-serverless-output/

aws --endpoint-url=http://localhost:4566 --region us-east-1 \
  s3 cp s3://infra-serverless-output/prueba.json.metadata.json -
```

## Salida esperada

El `ls` del paso 5 debe listar un objeto `prueba.json.metadata.json`, y el
`cp ... -` debe imprimir algo similar a:

```json
{
  "bucket_origen": "infra-serverless-input",
  "key": "prueba.json",
  "tamano_bytes": 20,
  "content_type": "application/json",
  "procesado_en": "2026-08-20T14:32:01.123456+00:00"
}
```

Esto confirma el flujo completo descrito en el post: el evento de subida al
bucket disparó automáticamente la función (cold start incluido, la primera
vez tarda un poco más), la función procesó el objeto y persistió el
resultado sin que en ningún momento se haya aprovisionado o administrado un
servidor manualmente.

## Limpieza

```bash
terraform destroy -auto-approve
docker compose down -v
```
