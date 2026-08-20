#!/bin/bash
# Script de admin automation: limpieza idempotente de logs antiguos.
#
# Reproduce los patrones centrales del post "Admin Automation":
#   - task scheduling vía cron (ver /etc/cron.d/admin-automation)
#   - modo estricto y manejo de errores (fail-fast)
#   - logging estructurado a archivo
#   - lock file para evitar ejecuciones concurrentes
#   - retención configurable (idempotencia: correrlo N veces da el mismo resultado)
set -euo pipefail

LOG_DIR="/var/log/app"
RETENTION_DAYS="${RETENTION_DAYS:-7}"
SCRIPT_LOG="/var/log/cleanup-logs.log"
LOCK_FILE="/var/lock/cleanup-logs.lock"

log() {
    echo "[$(date +'%Y-%m-%d %H:%M:%S')] $*" | tee -a "$SCRIPT_LOG"
}

error_exit() {
    log "ERROR: $1"
    exit 1
}

acquire_lock() {
    if [ -f "$LOCK_FILE" ]; then
        local pid
        pid=$(cat "$LOCK_FILE")
        if ps -p "$pid" > /dev/null 2>&1; then
            log "Ya hay una ejecución en curso (PID: $pid). Saliendo."
            exit 0
        fi
        log "Lock obsoleto encontrado (PID: $pid ya no existe). Se remueve."
        rm -f "$LOCK_FILE"
    fi
    echo $$ > "$LOCK_FILE"
}

release_lock() {
    rm -f "$LOCK_FILE"
}

trap release_lock EXIT

acquire_lock

log "Iniciando limpieza de logs en $LOG_DIR (retención: ${RETENTION_DAYS}d)"

[[ -d "$LOG_DIR" ]] || error_exit "El directorio $LOG_DIR no existe"
[[ -w "$LOG_DIR" ]] || error_exit "No hay permisos de escritura en $LOG_DIR"

deleted_count=0
while IFS= read -r -d '' old_log; do
    rm -f "$old_log"
    log "Eliminado: $old_log"
    deleted_count=$((deleted_count + 1))
done < <(find "$LOG_DIR" -maxdepth 1 -name '*.log' -mtime "+${RETENTION_DAYS}" -print0)

log "Limpieza completada. $deleted_count archivo(s) eliminado(s)."
