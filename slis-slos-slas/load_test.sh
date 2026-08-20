#!/usr/bin/env bash
# Genera trafico contra el servicio demo para poblar los SLI en Prometheus.
#
# Uso:
#   ./load_test.sh              # 60s de trafico normal
#   ./load_test.sh --degrade    # activa modo degradado durante el trafico, luego lo restaura
#
# Variables de entorno opcionales:
#   APP_URL   (default http://localhost:8080)
#   DURATION  (default 60, en segundos)

set -euo pipefail

APP_URL="${APP_URL:-http://localhost:8080}"
DURATION="${DURATION:-60}"

if [[ "${1:-}" == "--degrade" ]]; then
  echo "Activando modo degradado en el servicio..."
  curl -s "${APP_URL}/admin/degrade?on=1" >/dev/null
  trap 'echo "Restaurando modo normal..."; curl -s "${APP_URL}/admin/degrade?on=0" >/dev/null' EXIT
fi

echo "Generando trafico durante ${DURATION}s contra ${APP_URL}/work ..."
end=$((SECONDS + DURATION))
count=0
while [[ $SECONDS -lt $end ]]; do
  curl -s -o /dev/null "${APP_URL}/work" &
  count=$((count + 1))
  if (( count % 10 == 0 )); then
    wait
  fi
  sleep 0.05
done
wait

echo "Listo. ${count} solicitudes enviadas."
