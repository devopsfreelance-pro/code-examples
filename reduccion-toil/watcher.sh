#!/bin/sh
# Watcher de auto-recuperacion: version containerizada del script de
# "Automatizacion Progresiva" del post. En vez de systemctl restart,
# usa `docker restart` sobre el contenedor del servicio monitoreado.
#
# Esto elimina el toil de "entrar a la maquina y reiniciar a mano cada
# vez que el servicio se degrada": el propio watcher detecta, reintenta
# y remedia sin intervencion humana.

set -eu

SERVICE_CONTAINER="${SERVICE_CONTAINER:-reduccion-toil-flaky}"
HEALTH_URL="${HEALTH_URL:-http://flaky-service:8080/health}"
MAX_RETRIES="${MAX_RETRIES:-3}"
RETRY_DELAY="${RETRY_DELAY:-5}"

retry_count=0

check_service_health() {
    status=$(curl -s -o /dev/null -w "%{http_code}" "$HEALTH_URL" || echo "000")
    [ "$status" = "200" ]
}

restart_service() {
    echo "[$(date '+%H:%M:%S')] Reiniciando $SERVICE_CONTAINER (auto-remediacion)..."
    docker restart "$SERVICE_CONTAINER" >/dev/null
    sleep 3
}

echo "[$(date '+%H:%M:%S')] Watcher iniciado. Monitoreando $HEALTH_URL"

while true; do
    if check_service_health; then
        echo "[$(date '+%H:%M:%S')] Servicio saludable"
        retry_count=0
    else
        retry_count=$((retry_count + 1))
        echo "[$(date '+%H:%M:%S')] Servicio no responde (intento $retry_count/$MAX_RETRIES)"

        if [ "$retry_count" -ge "$MAX_RETRIES" ]; then
            restart_service
            retry_count=0
        fi
    fi

    sleep "$RETRY_DELAY"
done
