#!/usr/bin/env bash
# Genera trafico continuo contra payment_service para que Prometheus y los
# paneles del dashboard (rate, error rate, heatmap, SLO) tengan datos reales
# que mostrar. Cortar con Ctrl+C.
set -euo pipefail

URL="http://localhost:8000/work"

echo "Generando trafico contra ${URL} (Ctrl+C para cortar)..."
while true; do
  curl -s -o /dev/null "${URL}" &
  curl -s -o /dev/null "${URL}" &
  curl -s -o /dev/null "${URL}" &
  wait
  sleep 0.1
done
