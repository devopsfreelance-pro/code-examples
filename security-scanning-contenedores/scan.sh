#!/usr/bin/env bash
# Construye una imagen con dependencias Node desactualizadas y la escanea
# con Trivy y con Grype (ambos via Docker, sin instalar nada en el host),
# tal como describe el post: dos escaneres distintos sobre la misma imagen,
# con umbral de severidad y .trivyignore para excepciones documentadas.
set -euo pipefail

IMAGE_NAME="demo-scan:latest"
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

echo "==> Construyendo imagen de ejemplo (${IMAGE_NAME})"
docker build -f "${SCRIPT_DIR}/Dockerfile.vulnerable" -t "${IMAGE_NAME}" "${SCRIPT_DIR}"

echo
echo "==> [1/2] Escaneando ${IMAGE_NAME} con Trivy (severidad CRITICAL,HIGH)"
echo "    Usa .trivyignore para excluir la excepcion documentada (CVE-2021-23337)"
set +e
docker run --rm \
  -v /var/run/docker.sock:/var/run/docker.sock \
  -v trivy-cache:/root/.cache/ \
  -v "${SCRIPT_DIR}/.trivyignore:/.trivyignore" \
  aquasec/trivy:latest image \
  --severity CRITICAL,HIGH \
  --ignorefile /.trivyignore \
  --exit-code 1 \
  "${IMAGE_NAME}"
TRIVY_EXIT=$?
set -e

echo
echo "==> [2/2] Escaneando ${IMAGE_NAME} con Grype (falla solo ante CRITICAL)"
set +e
docker run --rm \
  -v /var/run/docker.sock:/var/run/docker.sock \
  -v grype-cache:/root/.cache/grype \
  anchore/grype:latest \
  "docker:${IMAGE_NAME}" \
  --fail-on critical
GRYPE_EXIT=$?
set -e

echo
echo "==> Resumen"
echo "    Trivy exit code: ${TRIVY_EXIT} (1 = encontro HIGH/CRITICAL sin excepcion)"
echo "    Grype exit code: ${GRYPE_EXIT} (1 = encontro CRITICAL)"

if [ "${TRIVY_EXIT}" -ne 0 ] || [ "${GRYPE_EXIT}" -ne 0 ]; then
  echo "==> Al menos un escaner reporto vulnerabilidades bloqueantes. Exit 1."
  exit 1
fi

echo "==> Ningun escaner encontro vulnerabilidades bloqueantes. OK."
