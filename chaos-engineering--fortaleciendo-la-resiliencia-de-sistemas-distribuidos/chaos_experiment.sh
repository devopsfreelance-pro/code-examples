#!/usr/bin/env bash
# Mini experimento de Chaos Engineering siguiendo los 4 pilares del post:
# 1) hipotesis de estado estable, 2) inyeccion de fallo real (latencia de red
# via Toxiproxy), 3) observacion, 4) rollback automatico y verificacion.
set -euo pipefail

TOXIPROXY_API="http://localhost:8474"
SERVICE_URL="http://localhost:8080/health"
PROXY_NAME="payment_service"
LATENCY_MS=1000
TOLERANCE_MS=300

measure_latency_ms() {
  local start end
  start=$(date +%s%N)
  if ! curl -sf -o /dev/null --max-time 5 "$SERVICE_URL"; then
    echo "-1"
    return
  fi
  end=$(date +%s%N)
  echo $(( (end - start) / 1000000 ))
}

echo "=== 1. Hipotesis de estado estable ==="
echo "Hipotesis: /health responde en menos de ${TOLERANCE_MS}ms"

latency=$(measure_latency_ms)
echo "Latencia medida (baseline): ${latency}ms"
if [ "$latency" -lt 0 ] || [ "$latency" -ge "$TOLERANCE_MS" ]; then
  echo "ABORTADO: el sistema no esta en estado estable antes del experimento."
  exit 1
fi
echo "OK: estado estable confirmado."
echo

echo "=== 2. Inyeccion de fallo: latencia de red de ${LATENCY_MS}ms ==="
curl -sf -X POST "${TOXIPROXY_API}/proxies/${PROXY_NAME}/toxics" \
  -H "Content-Type: application/json" \
  -d "{\"name\":\"latency_down\",\"type\":\"latency\",\"stream\":\"downstream\",\"attributes\":{\"latency\":${LATENCY_MS},\"jitter\":50}}" \
  > /dev/null
echo "Toxic 'latency_down' agregada al proxy ${PROXY_NAME}."
echo

echo "=== 3. Observacion durante el fallo ==="
latency_degraded=$(measure_latency_ms)
echo "Latencia medida (con fallo inyectado): ${latency_degraded}ms"
echo

echo "=== 4. Rollback: eliminar la toxina ==="
curl -sf -X DELETE "${TOXIPROXY_API}/proxies/${PROXY_NAME}/toxics/latency_down" > /dev/null
echo "Toxic eliminada."
echo

echo "=== 5. Verificacion de recuperacion ==="
latency_recovered=$(measure_latency_ms)
echo "Latencia medida (post-rollback): ${latency_recovered}ms"

if [ "$latency_recovered" -ge 0 ] && [ "$latency_recovered" -lt "$TOLERANCE_MS" ]; then
  echo "OK: el sistema recupero su estado estable."
else
  echo "ALERTA: el sistema no recupero el estado estable esperado."
  exit 1
fi

echo
echo "=== Resultado del experimento ==="
echo "Baseline:   ${latency}ms"
echo "Con fallo:  ${latency_degraded}ms (aumento de $(( latency_degraded - latency ))ms)"
echo "Recuperado: ${latency_recovered}ms"
