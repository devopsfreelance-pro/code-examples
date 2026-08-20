#!/usr/bin/env bash
# Valida la sintaxis y estructura de las reglas de alerta de Prometheus
# usando promtool (parte de la imagen oficial de Prometheus), sin
# necesidad de instalar nada localmente.
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

docker run --rm \
  --entrypoint promtool \
  -v "${SCRIPT_DIR}/alerts:/alerts" \
  prom/prometheus:latest \
  check rules /alerts/validator-alerts.yml
