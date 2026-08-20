#!/usr/bin/env python3
"""
Mini ejemplo de automatización DevOps con Python + boto3.

Demuestra los patrones centrales del post "Python DevOps: Automatización
Profesional en 2026":
  - Uso de boto3 para gestionar infraestructura (bucket S3) como código.
  - Decorador de reintentos con backoff exponencial ante fallos transitorios.
  - Logging estructurado para observabilidad de scripts de automatización.

Corre contra LocalStack (levantado con docker-compose.yml), así que NO
necesita credenciales reales de AWS ni genera costos.
"""

import logging
import os
import sys
import time
from functools import wraps

import boto3
from botocore.exceptions import ClientError

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
)
log = logging.getLogger("automate_infra")

# Endpoint de LocalStack. Se puede sobreescribir con la variable de entorno
# AWS_ENDPOINT_URL si se corre LocalStack en otro host/puerto.
ENDPOINT_URL = os.environ.get("AWS_ENDPOINT_URL", "http://localhost:4566")
REGION = os.environ.get("AWS_REGION", "us-east-1")
BUCKET_NAME = os.environ.get("BUCKET_NAME", "devops-automation-demo")


def retry_with_backoff(max_retries=5, initial_delay=1):
    """Decorador para reintentar operaciones con backoff exponencial.

    Mismo patrón que el post ilustra para operaciones contra APIs cloud
    que pueden fallar de forma transitoria (throttling, timeouts, etc.).
    """

    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            delay = initial_delay
            for attempt in range(max_retries):
                try:
                    return func(*args, **kwargs)
                except ClientError as e:
                    if attempt == max_retries - 1:
                        log.error("Falló después de %s intentos: %s", max_retries, e)
                        raise
                    log.warning(
                        "Intento %s/%s falló (%s), reintentando en %ss",
                        attempt + 1,
                        max_retries,
                        e.response.get("Error", {}).get("Code", "Unknown"),
                        delay,
                    )
                    time.sleep(delay)
                    delay *= 2

        return wrapper

    return decorator


def get_s3_client():
    """Crea el cliente S3 apuntando a LocalStack.

    En producción contra AWS real, solo hay que quitar endpoint_url y
    dejar que boto3 resuelva credenciales via variables de entorno,
    perfil compartido o rol IAM (nunca hardcodeadas en el código).
    """
    return boto3.client(
        "s3",
        endpoint_url=ENDPOINT_URL,
        region_name=REGION,
        aws_access_key_id="test",
        aws_secret_access_key="test",
    )


@retry_with_backoff(max_retries=3)
def create_bucket(s3, bucket_name):
    """Crea el bucket S3 si no existe, con reintentos automáticos."""
    existing = [b["Name"] for b in s3.list_buckets()["Buckets"]]
    if bucket_name in existing:
        log.info("Bucket '%s' ya existe, se reutiliza", bucket_name)
        return

    if REGION == "us-east-1":
        s3.create_bucket(Bucket=bucket_name)
    else:
        s3.create_bucket(
            Bucket=bucket_name,
            CreateBucketConfiguration={"LocationConstraint": REGION},
        )
    log.info("Bucket '%s' creado", bucket_name)


@retry_with_backoff(max_retries=3)
def tag_bucket(s3, bucket_name):
    """Aplica tags al bucket, práctica estándar de infraestructura como código."""
    s3.put_bucket_tagging(
        Bucket=bucket_name,
        Tagging={
            "TagSet": [
                {"Key": "Environment", "Value": "demo"},
                {"Key": "ManagedBy", "Value": "python-automation"},
                {"Key": "Project", "Value": "devopsfreelance-blog"},
            ]
        },
    )
    log.info("Tags aplicados a '%s'", bucket_name)


@retry_with_backoff(max_retries=3)
def upload_sample_object(s3, bucket_name):
    """Sube un objeto de ejemplo para verificar que el flujo end-to-end funciona."""
    key = "reports/status.txt"
    body = "Automatización ejecutada correctamente.\n"
    s3.put_object(Bucket=bucket_name, Key=key, Body=body.encode("utf-8"))
    log.info("Objeto '%s' subido a '%s'", key, bucket_name)
    return key


def verify(s3, bucket_name, key):
    """Verifica el resultado final: bucket, tags y objeto."""
    tags = s3.get_bucket_tagging(Bucket=bucket_name)["TagSet"]
    obj = s3.get_object(Bucket=bucket_name, Key=key)
    content = obj["Body"].read().decode("utf-8").strip()

    log.info("Verificación final:")
    log.info("  Bucket: %s", bucket_name)
    log.info("  Tags: %s", {t["Key"]: t["Value"] for t in tags})
    log.info("  Contenido de '%s': %r", key, content)


def main():
    log.info("Iniciando automatización de infraestructura (LocalStack: %s)", ENDPOINT_URL)
    s3 = get_s3_client()

    try:
        create_bucket(s3, BUCKET_NAME)
        tag_bucket(s3, BUCKET_NAME)
        key = upload_sample_object(s3, BUCKET_NAME)
        verify(s3, BUCKET_NAME, key)
    except ClientError as e:
        log.error("La automatización falló: %s", e)
        sys.exit(1)

    log.info("Automatización completada con éxito.")


if __name__ == "__main__":
    main()
