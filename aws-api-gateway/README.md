# AWS API Gateway + Lambda (demo local con LocalStack)

Ejemplo de código para el post [AWS API Gateway: Guía completa para arquitecturas serverless](https://www.devopsfreelance.pro/blog/posts/aws-api-gateway/).

## Qué demuestra

El post explica cómo AWS API Gateway actúa como proxy inverso administrado que recibe una solicitud HTTP, la autentica/procesa y la enruta hacia un backend (en este caso, una función Lambda), devolviendo la respuesta al cliente.

Este ejemplo reproduce ese flujo central en tu máquina, sin cuenta de AWS:

- Un **API Gateway REST API** con un recurso `/productos` y método `GET`.
- Una **integración `AWS_PROXY`** hacia una función **Lambda** en Python que responde con un catálogo de productos en JSON.
- Todo desplegado con **Terraform** contra **LocalStack** (emulador de AWS que corre en Docker), tal como se haría contra AWS real cambiando solo el `provider`.

No cubre autenticación, throttling, VTL ni stages avanzados (esos temas del post quedan fuera del alcance de este mini-ejemplo).

## Requisitos

- Docker y Docker Compose
- [Terraform](https://developer.hashicorp.com/terraform/install) >= 1.5
- `zip` y `curl` (herramientas estándar de línea de comandos)
- Python 3 (solo para formatear la respuesta JSON en la prueba final)

No se requiere cuenta de AWS ni credenciales reales: LocalStack acepta cualquier `access_key`/`secret_key` ficticios.

## Pasos para correrlo

1. Levantar LocalStack:

```bash
docker compose up -d
```

2. Esperar a que el healthcheck esté OK (unos segundos):

```bash
docker compose ps
```

3. Desplegar la API Gateway + Lambda y probar el endpoint:

```bash
./deploy.sh
```

El script empaqueta `lambda/handler.py`, ejecuta `terraform init && terraform apply` contra LocalStack, obtiene la URL de invocación y hace un `curl` de prueba.

4. Para volver a probar el endpoint manualmente en cualquier momento:

```bash
curl -s "$(terraform output -raw invoke_url)" | python3 -m json.tool
```

5. Para destruir los recursos y limpiar:

```bash
./destroy.sh
docker compose down
```

## Salida esperada

Al ejecutar `./deploy.sh`, la última parte de la salida debería verse así (el `id` de la REST API varía en cada corrida):

```json
{
    "message": "Hola desde AWS API Gateway + Lambda (LocalStack)",
    "method": "GET",
    "path": "/productos",
    "productos": [
        {
            "id": 1,
            "nombre": "Laptop DevOps Edition",
            "precio": 1200
        },
        {
            "id": 2,
            "nombre": "Teclado mecanico",
            "precio": 80
        }
    ]
}
```

## Notas

- `main.tf` apunta el provider de AWS a `http://localhost:4566` (endpoint único de LocalStack) con credenciales dummy (`test`/`test`). Para desplegar esto contra una cuenta de AWS real, bastaría con quitar el bloque `endpoints {}` y usar credenciales reales del `AWS_PROFILE`/variables de entorno estándar, no hay que rescribir los recursos.
- El archivo `lambda.zip` se genera en `deploy.sh` y no se versiona (es un artefacto de build).
- LocalStack Community (imagen `localstack/localstack`, gratuita) soporta API Gateway y Lambda, que es todo lo que usa este ejemplo.
