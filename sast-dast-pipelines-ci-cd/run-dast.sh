#!/usr/bin/env bash
# DAST: levanta la app vulnerable y la ataca desde afuera con OWASP ZAP
# baseline scan, tal como describe el post (caja negra, app SI desplegada).
set -euo pipefail

cd "$(dirname "$0")"

IMAGE=sast-dast-demo-app:latest
CONTAINER=sast-dast-demo-app
NETWORK=sast-dast-demo-net

cleanup() {
  echo
  echo "== Limpieza =="
  docker rm -f "$CONTAINER" >/dev/null 2>&1 || true
  docker network rm "$NETWORK" >/dev/null 2>&1 || true
}
trap cleanup EXIT

echo "== Build de la imagen de la app =="
docker build -t "$IMAGE" .

docker network create "$NETWORK" >/dev/null 2>&1 || true

echo "== Deploy: levantando la app (simula el staging del pipeline) =="
docker rm -f "$CONTAINER" >/dev/null 2>&1 || true
docker run -d --rm \
  --name "$CONTAINER" \
  --network "$NETWORK" \
  "$IMAGE"

echo "Esperando a que la app responda..."
for i in $(seq 1 20); do
  if docker run --rm --network "$NETWORK" curlimages/curl:latest \
      -sf "http://${CONTAINER}:5000/" >/dev/null 2>&1; then
    echo "App lista."
    break
  fi
  if [ "$i" -eq 20 ]; then
    echo "La app no respondio a tiempo." >&2
    exit 1
  fi
  sleep 1
done

echo
echo "== DAST: OWASP ZAP baseline scan contra la app en ejecucion =="
docker run --rm \
  --network "$NETWORK" \
  -v "$(pwd)":/zap/wrk/:rw \
  ghcr.io/zaproxy/zaproxy:stable \
  zap-baseline.py \
  -t "http://${CONTAINER}:5000/" \
  -r dast-report.html \
  -I

echo
echo "Reporte guardado en dast-report.html"
echo "ZAP baseline usa -I (no falla el script aunque encuentre WARN/ALERT);"
echo "en un pipeline real se cambia a -I por --fail-on-warn o se revisa"
echo "el exit code de zap-baseline.py para romper el build."
