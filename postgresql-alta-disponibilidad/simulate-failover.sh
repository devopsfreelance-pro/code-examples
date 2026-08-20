#!/usr/bin/env bash
# Simula, en miniatura, lo que hace Patroni: monitorea la salud del primario
# y si deja de responder, promueve automaticamente la replica a primario.
#
# Uso:
#   ./simulate-failover.sh &          # deja el "watcher" corriendo en background
#   docker stop pg-primary            # en otra terminal: simula la caida
#   (el watcher detecta el fallo y promueve pg-replica automaticamente)
set -euo pipefail

DB_USER="appuser"
DB_NAME="appdb"
CHECK_INTERVAL=3
MAX_FAILURES=3

failures=0

echo "Watcher de failover iniciado. Monitoreando pg-primary cada ${CHECK_INTERVAL}s..."
echo "Umbral: ${MAX_FAILURES} chequeos fallidos consecutivos antes de promover pg-replica."

while true; do
  if docker exec pg-primary pg_isready -U "$DB_USER" -d "$DB_NAME" >/dev/null 2>&1; then
    if [ "$failures" -gt 0 ]; then
      echo "[$(date -Iseconds)] pg-primary respondio de nuevo, reseteando contador."
    fi
    failures=0
  else
    failures=$((failures + 1))
    echo "[$(date -Iseconds)] pg-primary no responde (fallo ${failures}/${MAX_FAILURES})"
  fi

  if [ "$failures" -ge "$MAX_FAILURES" ]; then
    echo "[$(date -Iseconds)] Umbral de fallos alcanzado. Promoviendo pg-replica a PRIMARIO..."
    docker exec pg-replica pg_ctl promote -D /bitnami/postgresql/data
    echo "[$(date -Iseconds)] pg-replica promovida. Ya acepta escrituras."
    echo "En un cluster real, Patroni ademas actualizaria el almacen de configuracion"
    echo "(etcd/Consul) y PgBouncer redirigiria las conexiones al nuevo lider."
    break
  fi

  sleep "$CHECK_INTERVAL"
done
