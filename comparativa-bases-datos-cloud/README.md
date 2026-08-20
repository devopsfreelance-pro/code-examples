# Detectar queries costosas con pg_stat_statements (RDS vs Cloud SQL)

Post relacionado: [RDS vs Cloud SQL: Guía definitiva para elegir tu base de datos](https://www.devopsfreelance.pro/blog/posts/comparativa-bases-datos-cloud/)

## Qué demuestra este ejemplo

El post compara Amazon RDS y Google Cloud SQL y menciona `pg_stat_statements` como
herramienta para identificar queries costosas en PostgreSQL, algo aplicable a
ambas plataformas gestionadas (RDS y Cloud SQL exponen esta misma extensión).

Este mini-laboratorio levanta un PostgreSQL local con `pg_stat_statements`
habilitado, carga datos de ejemplo, genera un mix de queries (una de ellas
deliberadamente costosa por no tener índice) y muestra cómo identificar cuál
query está consumiendo más tiempo total, exactamente el mismo flujo que
usarías contra una instancia real de RDS o Cloud SQL.

## Requisitos

- Docker y Docker Compose
- Cliente `psql` no es necesario en el host (se usa el que trae el contenedor)

## Pasos para ejecutarlo

```bash
# 1. Levantar PostgreSQL con pg_stat_statements y datos de ejemplo
docker compose up -d

# 2. Esperar a que el healthcheck esté OK (unos segundos)
docker compose ps

# 3. Limpiar estadísticas acumuladas durante la inicialización
docker exec -i comparativa-bd-postgres psql -U demo -d production_db -c "SELECT pg_stat_statements_reset();"

# 4. Dar permisos de ejecución y generar carga de queries
chmod +x generate_load.sh
./generate_load.sh

# 5. Ver el ranking de queries más costosas
cat top_queries.sql | docker exec -i comparativa-bd-postgres psql -U demo -d production_db
```

## Salida esperada

En el paso 4 vas a ver una tabla similar a esta, donde la query con el JOIN
sin índice por `country` aparece primera por tiempo total acumulado:

```
                               query                                | calls | total_time_ms | mean_time_ms | max_time_ms
----------------------------------------------------------------------+-------+----------------+---------------+-------------
 SELECT c.name, count(*) FROM orders o JOIN customers c ON c.id = ... |    30 |         850.42 |         28.35 |       45.10
 SELECT status, count(*), sum(total_cents) FROM orders GROUP BY ...   |    30 |          210.15 |          7.01 |       12.40
 SELECT * FROM orders WHERE id = $1                                   |    30 |            9.87 |          0.33 |        1.20
```

(Los valores exactos de tiempo varían según tu máquina; lo importante es el
orden relativo: la query con JOIN sin índice queda arriba.)

## Limpiar

```bash
docker compose down -v
```

## Relación con RDS y Cloud SQL

- En **RDS**, este mismo análisis lo hace `Performance Insights`, que usa
  `pg_stat_statements` por debajo.
- En **Cloud SQL**, `Query Insights` ofrece la misma funcionalidad sobre la
  misma extensión.
- Este ejemplo reproduce localmente, sin costo, la consulta SQL que el post
  muestra para PostgreSQL, para que puedas probarla antes de conectarte a
  una instancia gestionada real.
