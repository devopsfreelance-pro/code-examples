#!/bin/bash
# Prepara datos de ejemplo y arranca cron en primer plano.
set -euo pipefail

LOG_DIR="/var/log/app"
mkdir -p "$LOG_DIR"

# Genera logs "viejos" (deberían borrarse) y "nuevos" (deberían sobrevivir),
# simulando semanas de acumulación con un solo comando touch -d.
if [ -z "$(find "$LOG_DIR" -maxdepth 1 -name '*.log' -print -quit)" ]; then
    for i in 1 5 10 20 30; do
        f="$LOG_DIR/app-old-${i}d.log"
        : > "$f"
        touch -d "-${i} days" "$f"
    done
    for i in 0 1 2; do
        f="$LOG_DIR/app-recent-${i}d.log"
        : > "$f"
        touch -d "-${i} days" "$f"
    done
fi

touch /var/log/cleanup-logs.log /var/log/cleanup-cron.log

echo "=== Estado inicial de $LOG_DIR ==="
ls -la "$LOG_DIR"
echo "==================================="
echo "Iniciando cron. Con RETENTION_DAYS=7 (default), los archivos de 10, 20 y 30"
echo "dias deberian desaparecer en el proximo tick del minuto. Tail de logs abajo:"

cron

# Mantiene el contenedor en primer plano mostrando la actividad de los scripts.
tail -F /var/log/cleanup-logs.log /var/log/cleanup-cron.log
