#!/usr/bin/env bash
# Consulta rapida de logs centralizados en Loki, simulando lo que harias
# desde Kibana (Discover) o el buscador de Graylog, pero via API HTTP.
set -euo pipefail

LOKI_URL="${LOKI_URL:-http://localhost:3100}"

echo "== Ultimos 20 logs (todos los servicios, job=demo-logs) =="
curl -sG "${LOKI_URL}/loki/api/v1/query_range" \
  --data-urlencode 'query={job="demo-logs"}' \
  --data-urlencode 'limit=20' \
  --data-urlencode "start=$(date -u -d '5 minutes ago' +%s%N 2>/dev/null || date -u -v-5M +%s%N)" \
  | python3 -m json.tool

echo
echo "== Solo logs con level=ERROR (busqueda filtrada, tipo Discover/Search) =="
curl -sG "${LOKI_URL}/loki/api/v1/query_range" \
  --data-urlencode 'query={job="demo-logs"} | json | level="ERROR"' \
  --data-urlencode 'limit=20' \
  | python3 -m json.tool

echo
echo "== Labels detectados (equivalente a los 'streams' de Graylog) =="
curl -s "${LOKI_URL}/loki/api/v1/labels" | python3 -m json.tool
