#!/usr/bin/env bash
# Cambia el upstream activo del proxy entre blue y green (despliegue blue-green).
# Uso: ./switch-deployment.sh blue|green

set -euo pipefail

TARGET="${1:-}"
CONF_FILE="$(dirname "$0")/nginx-proxy.conf"

if [[ "${TARGET}" != "blue" && "${TARGET}" != "green" ]]; then
    echo "Uso: $0 blue|green" >&2
    exit 1
fi

if [[ ! -f "${CONF_FILE}" ]]; then
    echo "No se encontro ${CONF_FILE}" >&2
    exit 1
fi

sed -i.bak -E "s/server app-(blue|green):5678;/server app-${TARGET}:5678;/" "${CONF_FILE}"
rm -f "${CONF_FILE}.bak"

docker compose exec proxy nginx -s reload

echo "Trafico redirigido a app-${TARGET}."
