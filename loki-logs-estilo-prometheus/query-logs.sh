#!/usr/bin/env bash
# Consulta logs en Loki usando LogQL, filtrando por etiquetas (no por texto completo).
# Ilustra el concepto central del post: Loki indexa metadatos (labels), no el contenido.
set -euo pipefail

LOKI_URL="${LOKI_URL:-http://localhost:3100}"

echo "== Labels disponibles en Loki =="
curl -s "${LOKI_URL}/loki/api/v1/labels" | python3 -m json.tool

echo
echo "== Ultimos logs del job 'demo-app' (todas las etiquetas) =="
curl -s -G "${LOKI_URL}/loki/api/v1/query_range" \
  --data-urlencode 'query={job="demo-app"}' \
  --data-urlencode "since=5m" \
  --data-urlencode "limit=10" | python3 -m json.tool

echo
echo "== Solo logs con etiqueta level=\"error\" (filtro por label, estilo Prometheus) =="
curl -s -G "${LOKI_URL}/loki/api/v1/query_range" \
  --data-urlencode 'query={job="demo-app", level="error"}' \
  --data-urlencode "since=5m" \
  --data-urlencode "limit=10" | python3 -m json.tool
