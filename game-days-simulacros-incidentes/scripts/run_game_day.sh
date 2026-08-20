#!/usr/bin/env bash
# Simulacro de incidente (game day) de un servicio de pagos:
#   1. Mide una línea base de latencia/errores con el sistema sano.
#   2. Inyecta el fallo (dependencia externa degradada, la que describe el post
#      como "Latencia +2s en 30% de requests" / "Timeouts completos en 50%").
#   3. Verifica que las métricas de Prometheus detecten la degradación.
#   4. Revierte el fallo y confirma la recuperación.
#
# Requiere: docker compose ya levantado (ver README) y curl.

set -euo pipefail

APP_URL="http://localhost:8000"
PROM_URL="http://localhost:9090"
REQUESTS_PER_PHASE=20

count_errors=0

fire_requests() {
  local label="$1"
  count_errors=0
  echo "--- Fase: ${label} (${REQUESTS_PER_PHASE} requests a ${APP_URL}/pay) ---"
  for _ in $(seq 1 "${REQUESTS_PER_PHASE}"); do
    start=$(date +%s.%N)
    status=$(curl -s -o /dev/null -w "%{http_code}" "${APP_URL}/pay" || echo "000")
    end=$(date +%s.%N)
    elapsed=$(awk "BEGIN {printf \"%.2f\", ${end} - ${start}}")
    if [ "${status}" != "200" ]; then
      count_errors=$((count_errors + 1))
    fi
    echo "  status=${status} latencia=${elapsed}s"
  done
  echo "  => errores en esta fase: ${count_errors}/${REQUESTS_PER_PHASE}"
}

echo "=== Game day: degradación del proveedor de pagos ==="

echo
echo "[1/4] Línea base con el sistema sano"
fire_requests "baseline"
baseline_errors=${count_errors}

echo
echo "[2/4] Inyectando fallo: dependencia externa degradada"
curl -s -X POST "${APP_URL}/toggle-dependency?degraded=true" | grep -q '"degraded":true' \
  && echo "  fallo inyectado correctamente" \
  || { echo "  ERROR: no se pudo inyectar el fallo"; exit 1; }

fire_requests "incidente"
incident_errors=${count_errors}

echo
echo "[3/4] Consultando la métrica de errores en Prometheus"
prom_query='sum(game_day_requests_total{status="error"})'
prom_result=$(curl -s --data-urlencode "query=${prom_query}" "${PROM_URL}/api/v1/query" \
  | python3 -c "import json,sys; d=json.load(sys.stdin); r=d['data']['result']; print(r[0]['value'][1] if r else '0')")
echo "  game_day_requests_total{status=\"error\"} = ${prom_result}"
echo "  (también podés explorarlo en ${PROM_URL}/graph)"

echo
echo "[4/4] Revirtiendo el fallo y verificando recuperación"
curl -s -X POST "${APP_URL}/toggle-dependency?degraded=false" | grep -q '"degraded":false' \
  && echo "  fallo revertido correctamente" \
  || { echo "  ERROR: no se pudo revertir el fallo"; exit 1; }

fire_requests "recuperacion"
recovery_errors=${count_errors}

echo
echo "=== Resumen del game day ==="
echo "Errores baseline:    ${baseline_errors}/${REQUESTS_PER_PHASE}"
echo "Errores en incidente: ${incident_errors}/${REQUESTS_PER_PHASE}"
echo "Errores post-recuperación: ${recovery_errors}/${REQUESTS_PER_PHASE}"

if [ "${incident_errors}" -gt "${baseline_errors}" ] && [ "${recovery_errors}" -le "${baseline_errors}" ]; then
  echo "Resultado: el sistema detectó y se recuperó del fallo inyectado. Objetivo del game day cumplido."
else
  echo "Resultado: revisá el comportamiento, no siguió el patrón esperado (esto también es un aprendizaje válido de un game day real)."
fi
