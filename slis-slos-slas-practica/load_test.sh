#!/usr/bin/env bash
## Genera trafico contra el servicio demo. Con --incident, primero sube la
## tasa de error 5xx del servicio (via /admin/error-rate) para superar el
## umbral del SLO (0.1%) y disparar la alerta de burn rate.
set -euo pipefail

APP_URL="${APP_URL:-http://localhost:8080}"
DURATION="${DURATION:-60}"
INCIDENT=0

for arg in "$@"; do
  case "$arg" in
    --incident) INCIDENT=1 ;;
    *) echo "Uso: $0 [--incident]" >&2; exit 1 ;;
  esac
done

if [ "$INCIDENT" -eq 1 ]; then
  echo "Simulando incidente: subiendo tasa de error 5xx a 15%..."
  curl -s -X POST "${APP_URL}/admin/error-rate?p=0.15" >/dev/null
else
  echo "Trafico normal: tasa de error 5xx en 0.05% (dentro del SLO)."
  curl -s -X POST "${APP_URL}/admin/error-rate?p=0.0005" >/dev/null
fi

echo "Generando trafico durante ${DURATION}s contra ${APP_URL}/api/search ..."
count=0
end=$((SECONDS + DURATION))
while [ $SECONDS -lt $end ]; do
  curl -s -o /dev/null "${APP_URL}/api/search?q=zapatillas" || true
  count=$((count + 1))
done
echo "Listo. ${count} solicitudes enviadas."

if [ "$INCIDENT" -eq 1 ]; then
  echo "Restaurando tasa de error normal..."
  curl -s -X POST "${APP_URL}/admin/error-rate?p=0.0005" >/dev/null
fi
