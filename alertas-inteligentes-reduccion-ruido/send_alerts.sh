#!/usr/bin/env bash
# Envia alertas de prueba a Alertmanager para demostrar dos tecnicas de
# reduccion de ruido descriptas en el post:
#   1) Agrupamiento: 5 alertas relacionadas -> 1 sola notificacion.
#   2) Inhibicion: una alerta critical suprime la high del mismo service.
set -euo pipefail

AM_URL="${AM_URL:-http://localhost:9093}"
NOW() { date -u +"%Y-%m-%dT%H:%M:%SZ"; }

post_alerts() {
  curl -sf -XPOST "${AM_URL}/api/v2/alerts" \
    -H "Content-Type: application/json" \
    -d "$1" > /dev/null
}

echo "== Escenario 1: agrupamiento (noise reduction) =="
echo "5 instancias del servicio 'checkout' fallan por la misma dependencia."
echo "Sin agrupamiento serian 5 notificaciones separadas; con group_by"
echo "[alertname, service] llegan como 1 sola al canal 'high'."
echo

payload="["
for i in 1 2 3 4 5; do
  ts=$(NOW)
  payload+=$(cat <<EOF
{
  "labels": {
    "alertname": "BackendUnavailable",
    "service": "checkout",
    "instance": "checkout-$i",
    "severity": "high"
  },
  "annotations": {
    "summary": "checkout-$i no responde"
  },
  "startsAt": "$ts"
},
EOF
)
done
payload="${payload%,}]"
post_alerts "$payload"
echo "Enviadas 5 alertas 'BackendUnavailable' (service=checkout, severity=high)."
echo "Esperando group_wait (~15s) para que Alertmanager las agrupe..."
sleep 20

echo
echo "== Escenario 2: inhibicion =="
echo "Cae la base de datos de 'payments' (critical). Un momento despues"
echo "aparece latencia alta en el mismo service (high): la critical la inhibe"
echo "porque comparten el label 'service' (inhibit_rules en alertmanager.yml)."
echo

ts=$(NOW)
post_alerts "[{
  \"labels\": {
    \"alertname\": \"DatabaseDown\",
    \"service\": \"payments\",
    \"severity\": \"critical\"
  },
  \"annotations\": {
    \"summary\": \"Base de datos de payments caida\"
  },
  \"startsAt\": \"$ts\"
}]"
echo "Enviada alerta critical DatabaseDown (service=payments)."
sleep 6

ts=$(NOW)
post_alerts "[{
  \"labels\": {
    \"alertname\": \"HighLatency\",
    \"service\": \"payments\",
    \"severity\": \"high\"
  },
  \"annotations\": {
    \"summary\": \"Latencia elevada en payments\"
  },
  \"startsAt\": \"$ts\"
}]"
echo "Enviada alerta high HighLatency (service=payments)."
echo "Esta NO deberia aparecer en el canal 'high' del receiver: quedo inhibida."
echo
echo "Revisa los logs con: docker compose logs -f receiver"
echo "y el estado de las alertas con: curl -s ${AM_URL}/api/v2/alerts | jq"
