#!/usr/bin/env bash
# Construye ambas imagenes (sin optimizar y optimizada con multi-stage build)
# y muestra la diferencia de tamano.
set -euo pipefail

cd "$(dirname "$0")"

IMG_SIN_OPTIMIZAR="docker-size-demo:sin-optimizar"
IMG_OPTIMIZADO="docker-size-demo:optimizado"

echo "==> Construyendo imagen SIN optimizar..."
docker build -f Dockerfile.sin-optimizar -t "$IMG_SIN_OPTIMIZAR" .

echo "==> Construyendo imagen OPTIMIZADA (multi-stage)..."
docker build -f Dockerfile.optimizado -t "$IMG_OPTIMIZADO" .

echo
echo "==> Comparacion de tamanos:"
docker images --format "table {{.Repository}}:{{.Tag}}\t{{.Size}}" \
  | grep -E "docker-size-demo|REPOSITORY"

echo
echo "==> Probando que la imagen optimizada funciona:"
HOST_PORT=8080
if ! CONTAINER_ID=$(docker run -d -p "${HOST_PORT}:8080" "$IMG_OPTIMIZADO" 2>/dev/null); then
  echo "Puerto ${HOST_PORT} ocupado, probando con 18080..."
  HOST_PORT=18080
  CONTAINER_ID=$(docker run -d -p "${HOST_PORT}:8080" "$IMG_OPTIMIZADO")
fi
sleep 1
curl -sf "http://localhost:${HOST_PORT}/" || echo "ADVERTENCIA: el healthcheck curl fallo"
docker stop "$CONTAINER_ID" >/dev/null
docker rm "$CONTAINER_ID" >/dev/null

echo
echo "==> Listo. La imagen optimizada deberia pesar unos pocos MB vs cientos de MB de la version sin optimizar."
