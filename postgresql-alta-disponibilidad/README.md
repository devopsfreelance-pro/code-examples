# PostgreSQL HA: replicacion, PgBouncer y failover

Ejemplo ejecutable del post [PostgreSQL HA: Guia completa de alta disponibilidad](https://www.devopsfreelance.pro/blog/posts/postgresql-alta-disponibilidad/).

## Que demuestra

Un mini cluster de PostgreSQL en alta disponibilidad con Docker Compose, cubriendo los tres pilares que explica el post:

- **Replicacion streaming primario -> replica**: `pg-primary` y `pg-replica` corren con `bitnami/postgresql:16`, configurados via variables de entorno (`POSTGRESQL_REPLICATION_MODE=master/slave`) para que la replica reciba el WAL del primario en continuo, igual que describe la seccion "Fundamentos de la alta disponibilidad".
- **Failover automatico (version mini de lo que hace Patroni)**: `simulate-failover.sh` monitorea el primario con `pg_isready` y, si deja de responder durante varios chequeos seguidos, promueve la replica a primario con `pg_ctl promote`. Patroni hace lo mismo a mayor escala, coordinando la decision via etcd/Consul/ZooKeeper.
- **Pooling de conexiones con PgBouncer**: el servicio `pgbouncer` (imagen `edoburu/pgbouncer`) expone un puerto de pooling en modo `transaction` sobre el primario, tal como describe la seccion de optimizacion de conexiones del post.

No incluye Patroni ni etcd reales (serian muchos mas contenedores para un ejemplo "mini"), pero el flujo de deteccion de fallo + promocion automatica es el mismo concepto que Patroni automatiza en produccion.

## Requisitos

- Docker y Docker Compose (`docker compose version`)
- Puertos libres en el host: `5432`, `5433`, `6432`
- Sin cuentas ni servicios pagos: todo corre local en contenedores (imagenes publicas `bitnami/postgresql` y `edoburu/pgbouncer`)

## Pasos para correrlo

1. Levantar el cluster (primario, replica y PgBouncer):

```bash
cd postgresql-alta-disponibilidad
docker compose up -d
```

Esperar unos 20-30 segundos a que la replica termine la sincronizacion inicial (`pg_basebackup`) con el primario.

2. Verificar la replicacion: escribe un dato en el primario y confirma que aparece en la replica, ademas de mostrar el lag de replicacion:

```bash
chmod +x test-replication.sh
./test-replication.sh
```

Salida esperada (resumida):

```
== 4. Leyendo el mismo registro desde la REPLICA (solo lectura) ==
 id |                  msg                   |          created_at
----+-----------------------------------------+-------------------------------
  1 | escrito en el primario a las 2026-08-...| 2026-08-...

== 5. Estado de replicacion visto desde el primario (pg_stat_replication) ==
 application_name | client_addr |   state   | sync_state | replay_lag
-------------------+-------------+-----------+------------+------------
 walreceiver       | ...         | streaming | async      |

== 6. Lag de replicacion visto desde la replica ==
 lag_replicacion
------------------
 00:00:00.0...
```

El dato se escribio unicamente en `pg-primary` y aparece en `pg-replica` sin haberlo insertado ahi: eso es la replicacion streaming funcionando.

3. Probar la conexion pooleada via PgBouncer (misma base, puerto distinto):

```bash
docker exec -e PGPASSWORD=apppass pg-primary psql -h pgbouncer -p 5432 -U appuser -d appdb -c "SELECT count(*) FROM ha_demo;"
```

4. Simular una caida del primario y ver el failover automatico. En una terminal, arrancar el watcher:

```bash
chmod +x simulate-failover.sh
./simulate-failover.sh
```

En otra terminal, simular la caida del primario:

```bash
docker stop pg-primary
```

Salida esperada del watcher (resumida):

```
[...] pg-primary no responde (fallo 1/3)
[...] pg-primary no responde (fallo 2/3)
[...] pg-primary no responde (fallo 3/3)
[...] Umbral de fallos alcanzado. Promoviendo pg-replica a PRIMARIO...
[...] pg-replica promovida. Ya acepta escrituras.
```

Confirmar que `pg-replica` ya acepta escrituras (paso manual, ya que en este mini demo no hay etcd que reconfigure PgBouncer automaticamente):

```bash
docker exec -e PGPASSWORD=apppass pg-replica psql -U appuser -d appdb -c "INSERT INTO ha_demo (msg) VALUES ('escrito en la ex-replica ya promovida');"
```

5. Apagar y limpiar todo:

```bash
docker compose down -v
```

## Notas

- Usuario/password (`appuser`/`apppass`, `repl_user`/`repl_pass`) son valores fijos solo para este demo local; en un entorno real van en un gestor de secretos (Vault, AWS Secrets Manager, K8s Secrets), nunca hardcodeados.
- Una vez promovida, `pg-replica` queda como primario independiente: no vuelve a sincronizarse sola con el `pg-primary` original si este se reinicia (necesitaria reclonarse como nueva replica). Eso es exactamente el trabajo que en produccion resuelve Patroni de forma automatica.
