#!/usr/bin/env bash
# Simula alertas estilo Alertmanager contra el motor de automatización.
# Demuestra: clasificación, runbook con acción, idempotencia, circuit breaker
# y escalamiento a on-call para alertas sin runbook.
set -euo pipefail

URL="http://localhost:5000/webhook/alert"

send_alert() {
  local alertname="$1"
  local severity="$2"
  local service="$3"
  local status="${4:-firing}"

  curl -s -X POST "$URL" \
    -H "Content-Type: application/json" \
    -d "{
      \"alerts\": [
        {
          \"status\": \"${status}\",
          \"labels\": {
            \"alertname\": \"${alertname}\",
            \"severity\": \"${severity}\",
            \"service\": \"${service}\"
          }
        }
      ]
    }" | python3 -m json.tool
  echo "---"
}

echo "1) Primera alerta ServiceDown -> el runbook ejecuta un restart"
send_alert "ServiceDown" "critical" "checkout-api"

echo "2) Misma alerta sigue firing -> idempotencia (no repite el restart)"
send_alert "ServiceDown" "critical" "checkout-api"

echo "3) Se resuelve el incidente -> limpia el estado"
send_alert "ServiceDown" "critical" "checkout-api" "resolved"

echo "4) HighCPULoad se dispara y resuelve 4 veces seguidas (ciclos reales de firing/resolved)."
echo "   Las primeras 3 ejecutan scale_out; la 4ta dispara el circuit breaker"
echo "   (MAX_ACTIONS_PER_HOUR=3 por defecto) y escala a on-call en vez de actuar."
for i in 1 2 3 4; do
  send_alert "HighCPULoad" "warning" "payments-worker"
  send_alert "HighCPULoad" "warning" "payments-worker" "resolved"
done

echo "5) Alerta sin runbook definido -> se escala directo a on-call"
send_alert "DiskAlmostFull" "warning" "billing-db"

echo "Listo. Revisá los logs del contenedor con: docker compose logs -f incident-responder"
