#!/usr/bin/env bash
# Ejecuta un mix de queries (algunas sin indice a proposito) contra la base
# de demo para generar estadisticas reales en pg_stat_statements, igual que
# ocurriria contra una instancia RDS o Cloud SQL en produccion.
set -euo pipefail

CONTAINER="comparativa-bd-postgres"
DB_USER="demo"
DB_NAME="production_db"

run_query() {
    docker exec -i "$CONTAINER" psql -U "$DB_USER" -d "$DB_NAME" -q -c "$1" >/dev/null
}

echo "Generando carga de queries de ejemplo..."

for i in $(seq 1 30); do
    # Query costosa: filtra por country sin indice
    run_query "SELECT c.name, count(*) FROM orders o JOIN customers c ON c.id = o.customer_id WHERE c.country = 'AR' GROUP BY c.name;"

    # Query barata: busqueda por PK
    run_query "SELECT * FROM orders WHERE id = $((RANDOM % 20000 + 1));"

    # Query de agregacion por status
    run_query "SELECT status, count(*), sum(total_cents) FROM orders GROUP BY status;"
done

echo "Carga generada. Ahora corre: cat top_queries.sql | docker exec -i $CONTAINER psql -U $DB_USER -d $DB_NAME"
