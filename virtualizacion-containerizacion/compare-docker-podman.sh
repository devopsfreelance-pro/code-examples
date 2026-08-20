#!/usr/bin/env bash
# Construye la misma imagen y corre el mismo contenedor con Docker y,
# si esta disponible, con Podman rootless. Muestra que la CLI es
# practicamente identica (como explica el post) y que en ambos casos
# el "aislamiento" es namespaces + cgroups del kernel host, sin hipervisor.
#
# Uso:
#   ./compare-docker-podman.sh

set -euo pipefail

IMAGE_NAME="virtualizacion-demo:local"
CONTAINER_NAME="virtualizacion-demo-cli"

cd "$(dirname "$0")"

echo "== 1) Build de la imagen con Docker =="
docker build -t "${IMAGE_NAME}" .

echo
echo "== 2) Run con limites de CPU/memoria (Docker) =="
docker rm -f "${CONTAINER_NAME}" >/dev/null 2>&1 || true
docker run -d \
  --name "${CONTAINER_NAME}" \
  --cpus="0.5" \
  --memory="128m" \
  -p 8080:8080 \
  "${IMAGE_NAME}"

sleep 1
echo
echo "== 3) Info del proceso/cgroup visto desde dentro del contenedor =="
curl -s http://localhost:8080/ || echo "El servidor todavia no respondio, reintenta con: curl http://localhost:8080/"

echo
echo "== 4) Proceso del contenedor visible en el host (namespaces, no VM) =="
docker inspect "${CONTAINER_NAME}" --format 'PID en el host: {{.State.Pid}}'

echo
docker rm -f "${CONTAINER_NAME}" >/dev/null 2>&1 || true

if command -v podman >/dev/null 2>&1; then
  echo
  echo "== 5) Mismo flujo con Podman (sin daemon, rootless) =="
  podman build -t "${IMAGE_NAME}" .
  podman rm -f "${CONTAINER_NAME}" >/dev/null 2>&1 || true
  podman run -d \
    --name "${CONTAINER_NAME}" \
    --cpus="0.5" \
    --memory="128m" \
    -p 8080:8080 \
    "${IMAGE_NAME}"
  sleep 1
  curl -s http://localhost:8080/ || echo "El servidor todavia no respondio, reintenta con: curl http://localhost:8080/"
  podman rm -f "${CONTAINER_NAME}" >/dev/null 2>&1 || true
else
  echo
  echo "== 5) Podman no esta instalado, se omite la comparacion =="
  echo "Instalar con: sudo apt install podman  (Debian/Ubuntu)"
fi
