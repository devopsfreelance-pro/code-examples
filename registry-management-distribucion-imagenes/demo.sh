#!/usr/bin/env bash
# Demo de registry management: push/pull, versionado semantico,
# inspeccion via API de distribucion OCI y garbage collection.
#
# Uso: ./demo.sh
set -euo pipefail

REGISTRY="localhost:5000"
IMAGE_NAME="demo-app"
TAG="v1.0.0"

step() {
  echo
  echo "=== $1 ==="
}

step "1. Levantar el registry local"
docker compose up -d
echo "Esperando a que el registry responda..."
for i in $(seq 1 20); do
  if curl -sf "http://${REGISTRY}/v2/" >/dev/null; then
    break
  fi
  sleep 1
done
curl -sf "http://${REGISTRY}/v2/" >/dev/null || { echo "El registry no respondio a tiempo"; exit 1; }
echo "Registry OK en http://${REGISTRY}/v2/"

step "2. Construir una imagen minima de ejemplo"
BUILD_DIR="$(mktemp -d)"
trap 'rm -rf "${BUILD_DIR}"' EXIT
cat > "${BUILD_DIR}/Dockerfile" <<'EOF'
FROM alpine:3.20
RUN echo "imagen de demo para registry management" > /app.txt
CMD ["cat", "/app.txt"]
EOF
docker build -t "${IMAGE_NAME}:${TAG}" "${BUILD_DIR}"

step "3. Etiquetar con versionado semantico explicito (nunca 'latest' en produccion)"
docker tag "${IMAGE_NAME}:${TAG}" "${REGISTRY}/${IMAGE_NAME}:${TAG}"

step "4. Push al registry local"
docker push "${REGISTRY}/${IMAGE_NAME}:${TAG}"

step "5. Listar el catalogo de repositorios via API de distribucion"
curl -s "http://${REGISTRY}/v2/_catalog" | tee /dev/stderr | grep -q "${IMAGE_NAME}"

step "6. Listar tags del repositorio"
curl -s "http://${REGISTRY}/v2/${IMAGE_NAME}/tags/list"

step "7. Obtener el manifiesto (metadatos + referencias a capas)"
curl -s \
  -H "Accept: application/vnd.docker.distribution.manifest.v2+json" \
  "http://${REGISTRY}/v2/${IMAGE_NAME}/manifests/${TAG}"

step "8. Simular un consumidor: borrar la imagen local y hacer pull desde el registry"
docker rmi "${REGISTRY}/${IMAGE_NAME}:${TAG}" >/dev/null
docker pull "${REGISTRY}/${IMAGE_NAME}:${TAG}"
docker run --rm "${REGISTRY}/${IMAGE_NAME}:${TAG}"

step "9. Garbage collection: eliminar el manifiesto y compactar capas huerfanas"
DIGEST=$(curl -s -I \
  -H "Accept: application/vnd.docker.distribution.manifest.v2+json" \
  "http://${REGISTRY}/v2/${IMAGE_NAME}/manifests/${TAG}" \
  | grep -i Docker-Content-Digest | awk '{print $2}' | tr -d '\r')
echo "Digest del manifiesto: ${DIGEST}"
curl -s -o /dev/null -w "DELETE manifest -> HTTP %{http_code}\n" \
  -X DELETE "http://${REGISTRY}/v2/${IMAGE_NAME}/manifests/${DIGEST}"
docker compose exec registry bin/registry garbage-collect /etc/docker/registry/config.yml

echo
echo "Demo completa. Para apagar el registry: docker compose down -v"
