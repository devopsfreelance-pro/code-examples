#!/usr/bin/env bash
# Construye la misma app Flask con dos Dockerfiles distintos (Alpine
# multi-stage vs Debian slim single-stage) y compara el tamaño final de
# cada imagen, replicando el argumento central del post.
set -euo pipefail

cd "$(dirname "$0")/.."

echo "==> Construyendo imagen Alpine (multi-stage)..."
docker build -f Dockerfile.alpine -t alpine-demo:alpine .

echo
echo "==> Construyendo imagen Debian slim (single-stage)..."
docker build -f Dockerfile.debian -t alpine-demo:debian .

echo
echo "==> Comparación de tamaños:"
docker images alpine-demo --format "table {{.Tag}}\t{{.Size}}"

echo
echo "==> Smoke test: levantando alpine-demo:alpine y probando /health"
CONTAINER_ID=$(docker run -d -p 5000:5000 alpine-demo:alpine)
trap 'docker rm -f "$CONTAINER_ID" >/dev/null' EXIT

# Esperar a que el servidor Flask esté listo
for i in $(seq 1 10); do
  if curl -sf http://localhost:5000/health >/dev/null; then
    break
  fi
  sleep 1
done

echo "Respuesta de /health:"
curl -s http://localhost:5000/health
echo
