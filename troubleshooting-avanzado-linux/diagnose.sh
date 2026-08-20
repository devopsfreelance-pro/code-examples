#!/usr/bin/env bash
# Script de diagnostico que aplica la metodologia del post
# "Troubleshooting Avanzado en Linux" contra el contenedor de ejemplo:
#   1. Linea base / utilizacion de recursos (equivalente a top/iostat)
#   2. Identificacion del proceso que consume mas memoria (memory leak)
#   3. Analisis de logs con grep + awk (equivalente a journalctl del post)
#
# Requisito: el contenedor "troubleshooting-demo-app" debe estar corriendo
# (ver README.md, paso "docker compose up -d").

set -euo pipefail

CONTAINER="troubleshooting-demo-app"

if ! docker ps --format '{{.Names}}' | grep -q "^${CONTAINER}$"; then
    echo "ERROR: el contenedor ${CONTAINER} no esta corriendo." >&2
    echo "Ejecuta primero: docker compose up -d --build" >&2
    exit 1
fi

echo "=============================================="
echo "1) Linea base de utilizacion (metodologia USE)"
echo "=============================================="
docker stats --no-stream "${CONTAINER}"

echo
echo "=============================================="
echo "2) Procesos ordenados por uso de memoria (leak)"
echo "=============================================="
docker exec "${CONTAINER}" ps aux --sort=-%mem | head -5

echo
echo "=============================================="
echo "3) Memoria detallada del proceso principal"
echo "=============================================="
docker exec "${CONTAINER}" sh -c 'cat /proc/1/status | grep -E "VmRSS|VmSize|VmData"'

echo
echo "=============================================="
echo "4) Analisis de logs: errores y criticos (ultimos 200 eventos)"
echo "   equivalente a: journalctl -p err"
echo "=============================================="
docker logs --tail 200 "${CONTAINER}" 2>&1 | grep -E "ERROR|CRITICAL" || echo "(sin errores en la ventana analizada)"

echo
echo "=============================================="
echo "5) Correlacion de patrones: frecuencia de causas de error"
echo "   equivalente al pipeline journalctl | grep | awk | sort | uniq -c del post"
echo "=============================================="
docker logs --tail 500 "${CONTAINER}" 2>&1 \
    | grep -oE "causa=[a-z_]+" \
    | sort | uniq -c | sort -rn || echo "(sin datos de causa aun, esperar unos segundos mas)"

echo
echo "Diagnostico completado."
