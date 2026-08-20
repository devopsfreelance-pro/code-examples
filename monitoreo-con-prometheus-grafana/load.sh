#!/usr/bin/env bash
# Genera trafico continuo contra el endpoint /work de la demo app
# para que haya metricas visibles en Prometheus/Grafana.
set -euo pipefail

URL="${1:-http://localhost:8000/work}"

echo "Generando trafico contra ${URL} (Ctrl+C para detener)..."
while true; do
  curl -s -o /dev/null "${URL}" || true
  sleep 0.2
done
