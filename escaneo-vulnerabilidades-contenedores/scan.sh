#!/usr/bin/env bash
# Construye una imagen con dependencias desactualizadas y la escanea con
# Trivy (via Docker, sin instalar nada en el host). Falla con exit code 1
# si aparecen vulnerabilidades HIGH o CRITICAL, igual que en un pipeline CI/CD.
set -euo pipefail

IMAGE_NAME="demo-scan:latest"
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

echo "==> Construyendo imagen de ejemplo (${IMAGE_NAME})"
docker build -f "${SCRIPT_DIR}/Dockerfile.vulnerable" -t "${IMAGE_NAME}" "${SCRIPT_DIR}"

echo "==> Escaneando ${IMAGE_NAME} con Trivy"
docker run --rm \
  -v /var/run/docker.sock:/var/run/docker.sock \
  -v trivy-cache:/root/.cache/ \
  aquasec/trivy:latest image \
  --exit-code 1 \
  --severity HIGH,CRITICAL \
  --ignore-unfixed \
  "${IMAGE_NAME}"

echo "==> Sin vulnerabilidades HIGH/CRITICAL corregibles. OK."
