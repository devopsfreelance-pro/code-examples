#!/usr/bin/env bash
# Verifica que ambos entornos de la estrategia hibrida quedaron operativos:
#  - "cloud" (bucket S3 en LocalStack)
#  - "on-premise" (contenedor Docker local)
set -euo pipefail

echo "== Verificando entorno cloud (LocalStack / S3) =="
if command -v aws >/dev/null 2>&1; then
  AWS_ACCESS_KEY_ID=test AWS_SECRET_ACCESS_KEY=test aws --endpoint-url=http://localhost:4566 \
    s3 ls | grep hybrid-demo-cloud-artifacts \
    && echo "OK: bucket cloud encontrado" \
    || echo "FALTA: bucket cloud no encontrado (corre terraform apply)"
else
  echo "AWS CLI no instalado, se omite verificacion directa del bucket."
fi

echo
echo "== Verificando entorno on-premise (contenedor Docker) =="
if docker ps --format '{{.Names}}' | grep -q hybrid-demo-onprem-web; then
  echo "OK: contenedor on-premise corriendo"
  curl -sf http://localhost:8080 >/dev/null && echo "OK: servicio on-premise responde en http://localhost:8080"
else
  echo "FALTA: contenedor on-premise no esta corriendo (corre terraform apply)"
fi
