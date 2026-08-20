#!/usr/bin/env bash
# Simula localmente, con Docker, las mismas etapas que azure-pipelines.yml
# ejecutaría en Azure DevOps: instalar dependencias, correr tests, construir
# la imagen, levantar el contenedor y hacer un smoke test contra /health.
#
# Uso:
#   ./scripts/run_pipeline_locally.sh

set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT_DIR"

IMAGE_NAME="myapp"
IMAGE_TAG="local"
CONTAINER_NAME="myapp-ci-demo"
PORT="8080"

echo "==> Stage: Build and Test"

echo "--> Running unit tests"
python3 -m pip install --quiet --user pytest
python3 -m pytest app/test_app.py -v

echo "--> Building Docker image ($IMAGE_NAME:$IMAGE_TAG)"
docker build -t "$IMAGE_NAME:$IMAGE_TAG" .

echo "==> Stage: Deploy to Development (simulado con un contenedor local)"

docker rm -f "$CONTAINER_NAME" >/dev/null 2>&1 || true
docker run -d --name "$CONTAINER_NAME" -p "$PORT:8080" -e APP_ENVIRONMENT=development "$IMAGE_NAME:$IMAGE_TAG"

echo "--> Esperando a que el contenedor esté listo"
for i in $(seq 1 15); do
  if curl -sf "http://localhost:$PORT/health" >/dev/null; then
    break
  fi
  sleep 1
done

echo "--> Smoke test"
response=$(curl -s "http://localhost:$PORT/health")
echo "$response"

if echo "$response" | grep -q '"status": "ok"'; then
  echo "Smoke test PASSED"
else
  echo "Smoke test FAILED"
  docker logs "$CONTAINER_NAME"
  docker rm -f "$CONTAINER_NAME" >/dev/null 2>&1 || true
  exit 1
fi

echo "==> Limpiando contenedor de la demo"
docker rm -f "$CONTAINER_NAME" >/dev/null 2>&1 || true

echo "Pipeline local completado con éxito."
