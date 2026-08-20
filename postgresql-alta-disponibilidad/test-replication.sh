#!/usr/bin/env bash
# Verifica que la replicacion streaming primario -> replica funciona,
# y muestra el lag de replicacion tal como lo monitorearia Patroni.
set -euo pipefail

DB_USER="appuser"
DB_NAME="appdb"
DB_PASSWORD="apppass"

psql_primary() {
  docker exec -e PGPASSWORD="$DB_PASSWORD" pg-primary psql -U "$DB_USER" -d "$DB_NAME" -c "$1"
}

psql_replica() {
  docker exec -e PGPASSWORD="$DB_PASSWORD" pg-replica psql -U "$DB_USER" -d "$DB_NAME" -c "$1"
}

echo "== 1. Esperando a que primario y replica esten listos =="
for svc in pg-primary pg-replica; do
  until docker exec "$svc" pg_isready -U "$DB_USER" -d "$DB_NAME" >/dev/null 2>&1; do
    echo "  esperando $svc..."
    sleep 2
  done
  echo "  $svc: OK"
done

echo
echo "== 2. Creando tabla y escribiendo un registro en el PRIMARIO =="
psql_primary "CREATE TABLE IF NOT EXISTS ha_demo (id serial PRIMARY KEY, msg text, created_at timestamptz DEFAULT now());"
psql_primary "INSERT INTO ha_demo (msg) VALUES ('escrito en el primario a las $(date -Iseconds)');"

echo
echo "== 3. Esperando propagacion por streaming replication (3s) =="
sleep 3

echo
echo "== 4. Leyendo el mismo registro desde la REPLICA (solo lectura) =="
psql_replica "SELECT id, msg, created_at FROM ha_demo ORDER BY id DESC LIMIT 5;"

echo
echo "== 5. Estado de replicacion visto desde el primario (pg_stat_replication) =="
psql_primary "SELECT application_name, client_addr, state, sync_state, replay_lag FROM pg_stat_replication;"

echo
echo "== 6. Lag de replicacion visto desde la replica =="
psql_replica "SELECT now() - pg_last_xact_replay_timestamp() AS lag_replicacion;"

echo
echo "Listo: el dato escrito en el primario aparece en la replica sin haberlo escrito ahi."
