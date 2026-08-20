#!/usr/bin/env bash
#
# Demo de Point-in-Time Recovery (PITR) en PostgreSQL con pg_basebackup + WAL.
# Reproduce el flujo descrito en el post "Database Backup: Guía completa de
# recuperación empresarial": respaldo base + archivado continuo de WAL,
# incidente (DROP accidental) y restauración al segundo exacto anterior al error.
#
# Requisitos: Docker + Docker Compose plugin. Sin dependencias pagas.
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

DB_CONTAINER="pitr-demo-db"
RESTORE_VOLUME="pitr-demo-restore-data"
COMPOSE="docker compose"

log() { printf '\n\033[1;36m==> %s\033[0m\n' "$1"; }

cleanup_previous() {
  log "Limpiando entorno previo (si existe)"
  $COMPOSE down -v --remove-orphans >/dev/null 2>&1 || true
  docker volume rm -f "$RESTORE_VOLUME" >/dev/null 2>&1 || true
  rm -rf "$SCRIPT_DIR/wal_archive" "$SCRIPT_DIR/backup"
  mkdir -p "$SCRIPT_DIR/wal_archive" "$SCRIPT_DIR/backup"
  chmod 777 "$SCRIPT_DIR/wal_archive"
}

wait_for_db() {
  log "Esperando que PostgreSQL acepte conexiones"
  for _ in $(seq 1 30); do
    if docker exec "$DB_CONTAINER" pg_isready -U postgres >/dev/null 2>&1; then
      return 0
    fi
    sleep 1
  done
  echo "PostgreSQL no arrancó a tiempo" >&2
  exit 1
}

psql_c() {
  docker exec -e PGPASSWORD=postgres "$DB_CONTAINER" psql -U postgres -d appdb -v ON_ERROR_STOP=1 -c "$1"
}

main() {
  cleanup_previous

  log "1/8 - Levantando PostgreSQL (docker compose up)"
  $COMPOSE up -d
  wait_for_db

  log "2/8 - Creando tabla 'orders' con datos iniciales"
  psql_c "CREATE TABLE orders (id serial PRIMARY KEY, item text, created_at timestamptz DEFAULT now());"
  psql_c "INSERT INTO orders (item) VALUES ('laptop'), ('mouse'), ('teclado');"

  log "3/8 - Respaldo base con pg_basebackup (equivalente a lo descrito en el post)"
  docker exec "$DB_CONTAINER" bash -c '
    set -e
    rm -rf /tmp/base_backup
    pg_basebackup -D /tmp/base_backup -Fp -Xnone -U postgres -h 127.0.0.1 -P
    tar czf /tmp/base_backup.tar.gz -C /tmp/base_backup .
  '
  docker cp "$DB_CONTAINER:/tmp/base_backup.tar.gz" "$SCRIPT_DIR/backup/base_backup.tar.gz"
  echo "Respaldo base guardado en ./backup/base_backup.tar.gz"

  log "4/8 - Insertando el último pedido válido (order 'monitor 4k')"
  psql_c "INSERT INTO orders (item) VALUES ('monitor 4k');"
  psql_c "SELECT pg_switch_wal();"
  sleep 2
  RECOVERY_TARGET_TIME="$(date -u +"%Y-%m-%d %H:%M:%S %Z")"
  echo "Punto de recuperación objetivo (RECOVERY_TARGET_TIME): $RECOVERY_TARGET_TIME"
  sleep 2

  log "5/8 - Estado ANTES del incidente"
  psql_c "SELECT * FROM orders ORDER BY id;"

  log "6/8 - Simulando incidente: un deploy corre un DROP TABLE por error"
  psql_c "DROP TABLE orders;"
  psql_c "SELECT pg_switch_wal();"
  echo "Tabla 'orders' eliminada accidentalmente. Verificando que ya no existe:"
  psql_c "\dt" || true

  log "7/8 - Restaurando en un contenedor nuevo hasta justo antes del incidente"
  docker run --rm \
    --name pitr-demo-restore \
    -v "$RESTORE_VOLUME:/var/lib/postgresql/data" \
    -v "$SCRIPT_DIR/wal_archive:/wal_archive:ro" \
    -v "$SCRIPT_DIR/backup:/backup:ro" \
    -e RECOVERY_TARGET_TIME="$RECOVERY_TARGET_TIME" \
    --entrypoint bash \
    postgres:16-alpine -c '
      set -e
      rm -rf /var/lib/postgresql/data/*
      tar -xzf /backup/base_backup.tar.gz -C /var/lib/postgresql/data
      touch /var/lib/postgresql/data/recovery.signal
      cat >> /var/lib/postgresql/data/postgresql.auto.conf <<EOF
restore_command = '"'"'cp /wal_archive/%f %p'"'"'
recovery_target_time = '"'"'${RECOVERY_TARGET_TIME}'"'"'
recovery_target_action = '"'"'promote'"'"'
EOF
      chown -R postgres:postgres /var/lib/postgresql/data
      chmod 700 /var/lib/postgresql/data
      su postgres -c "pg_ctl -D /var/lib/postgresql/data -w -t 60 start"
      echo "--- Estado restaurado (deberia tener 4 pedidos, sin el DROP) ---"
      su postgres -c "psql -d appdb -c \"SELECT * FROM orders ORDER BY id;\""
      su postgres -c "pg_ctl -D /var/lib/postgresql/data stop"
    '

  log "8/8 - Listo. Apagando el entorno (docker compose down -v) para dejar todo limpio"
  $COMPOSE down -v >/dev/null 2>&1
  docker volume rm -f "$RESTORE_VOLUME" >/dev/null 2>&1 || true

  echo
  echo "Demo completa: la tabla 'orders' se restauró en el contenedor de recuperación"
  echo "con los 4 pedidos originales (incluyendo 'monitor 4k'), sin rastro del DROP TABLE."
}

main "$@"
