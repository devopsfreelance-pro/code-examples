#!/usr/bin/env bash
# Envía eventos de ejemplo al endpoint HTTP de Fluentd para disparar el pipeline:
# filtrado de health-checks, enriquecimiento y routing con copy a dos destinos.
set -euo pipefail

FLUENTD_URL="http://localhost:9880"

echo "Enviando evento critico (va a critical.log + stdout)..."
curl -sf -X POST -d 'json={"message":"disk usage above 90% on node-3","level":"critical"}' \
  "${FLUENTD_URL}/app.critical.disk"

echo "Enviando evento general (va a general.log)..."
curl -sf -X POST -d 'json={"message":"request completed in 120ms","level":"info"}' \
  "${FLUENTD_URL}/app.requests"

echo "Enviando health-check (debe ser descartado por el filtro grep)..."
curl -sf -X POST -d 'json={"message":"health-check ok","level":"debug"}' \
  "${FLUENTD_URL}/app.requests"

echo "Enviando segundo evento critico (va a critical.log + stdout)..."
curl -sf -X POST -d 'json={"message":"payment service unreachable","level":"critical"}' \
  "${FLUENTD_URL}/app.critical.payments"

echo "Listo. Esperando 3s a que Fluentd haga flush de los buffers..."
sleep 3
echo "OK"
