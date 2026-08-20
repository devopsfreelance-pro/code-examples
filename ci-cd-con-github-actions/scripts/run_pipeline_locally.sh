#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ROOT_DIR="$(cd "${SCRIPT_DIR}/.." && pwd)"

IMAGE_NAME="ci-cd-github-actions-demo:local"
CONTAINER_NAME="ci-cd-github-actions-demo"
PORT="8080"

cleanup() {
  echo "==> Limpiando contenedor de la demo"
  docker rm -f "${CONTAINER_NAME}" >/dev/null 2>&1 || true
}
trap cleanup EXIT

echo "==> Job: build-and-test"
echo "--> Corriendo tests (node --test)"
(cd "${ROOT_DIR}/app" && npm test)

echo "--> Construyendo imagen Docker (${IMAGE_NAME})"
docker build -t "${IMAGE_NAME}" "${ROOT_DIR}"

echo "==> Job: deploy (simulado con un contenedor local)"
docker rm -f "${CONTAINER_NAME}" >/dev/null 2>&1 || true
docker run -d --name "${CONTAINER_NAME}" -p "${PORT}:8080" \
  -e APP_ENVIRONMENT=production "${IMAGE_NAME}" >/dev/null

echo "--> Esperando a que el contenedor esté listo"
for i in $(seq 1 10); do
  if curl -sf "http://localhost:${PORT}/health" >/dev/null 2>&1; then
    break
  fi
  sleep 1
done

echo "--> Smoke test"
RESPONSE="$(curl -sf "http://localhost:${PORT}/health")"
echo "${RESPONSE}"

if echo "${RESPONSE}" | grep -q '"status":"ok"'; then
  echo "Smoke test PASSED"
else
  echo "Smoke test FAILED"
  exit 1
fi

echo "Pipeline local completado con éxito."
