# Point-in-Time Recovery (PITR) en PostgreSQL

Ejemplo ejecutable del post [Database Backup: Guía completa de recuperación empresarial](https://www.devopsfreelance.pro/blog/posts/backup-recovery-bases-datos/).

## Qué demuestra

El script `demo.sh` reproduce, con contenedores locales, el flujo central del
post: un respaldo base con `pg_basebackup` combinado con archivado continuo de
WAL, y una restauración a un punto exacto en el tiempo (PITR) para deshacer un
incidente sin perder las transacciones válidas anteriores. Concretamente:

1. Levanta un PostgreSQL con `archive_mode=on` y `archive_command` guardando
   cada WAL en `./wal_archive`.
2. Crea una tabla `orders` con datos iniciales.
3. Toma un respaldo base con `pg_basebackup` (igual que en el post) y lo
   guarda en `./backup/base_backup.tar.gz`.
4. Inserta un pedido más (`monitor 4k`) y registra el timestamp exacto de ese
   momento como `RECOVERY_TARGET_TIME`.
5. Simula un incidente real: un `DROP TABLE orders` accidental (por ejemplo,
   una migración mal escrita corriendo en producción).
6. Levanta un segundo contenedor "de recuperación" a partir del respaldo base
   + los WAL archivados, con `recovery_target_time` apuntando al instante
   justo antes del `DROP TABLE`.
7. Muestra que la tabla `orders` reaparece completa (los 4 pedidos, incluido
   `monitor 4k`), sin rastro del `DROP TABLE` posterior.

Esto es exactamente la técnica descrita en la sección "Implementación de point
in time recovery" del post: respaldo base periódico + WAL archivado permite
reproducir el historial de transacciones hasta cualquier instante.

## Requisitos

- Docker + Docker Compose plugin (`docker compose version`)
- Bash
- No requiere PostgreSQL instalado en el host: todo corre dentro de contenedores.
- Sin credenciales ni cuentas externas: el usuario/clave de la base
  (`postgres` / `postgres`) es solo para este entorno local descartable,
  definido en `docker-compose.yml`.

## Cómo correrlo

```bash
cd backup-recovery-bases-datos
./demo.sh
```

El script es idempotente: al iniciar borra cualquier entorno previo
(`docker compose down -v`, volumen de restauración, carpetas `wal_archive/` y
`backup/`) y al terminar deja todo apagado y limpio (`docker compose down -v`).

No requiere pasos manuales adicionales: el propio script levanta la base,
aplica el respaldo, simula el incidente, restaura y apaga todo.

## Salida esperada

Los puntos clave a observar en la salida:

Antes del incidente (paso 5/8), la tabla tiene 4 filas:

```
 id |    item    |          created_at
----+------------+-------------------------------
  1 | laptop     | ...
  2 | mouse      | ...
  3 | teclado    | ...
  4 | monitor 4k | ...
(4 rows)
```

Después del `DROP TABLE` (paso 6/8):

```
Did not find any relations.
```

Tras la restauración PITR (paso 7/8), el contenedor de recuperación vuelve a
mostrar las mismas 4 filas (incluyendo `monitor 4k`, insertado antes del
punto de recuperación), confirmando que se recuperó el estado exacto previo
al incidente sin perder la última transacción válida:

```
--- Estado restaurado (deberia tener 4 pedidos, sin el DROP) ---
 id |    item    |          created_at
----+------------+-------------------------------
  1 | laptop     | ...
  2 | mouse      | ...
  3 | teclado    | ...
  4 | monitor 4k | ...
(4 rows)
```

## Archivos

- `docker-compose.yml`: PostgreSQL 16 con `wal_level=replica`, `archive_mode=on`
  y `archive_command` hacia `./wal_archive` (bind mount).
- `demo.sh`: orquesta todo el ciclo (setup, backup, incidente, restore,
  verificación y limpieza) usando `docker exec` y un `docker run` efímero
  para el contenedor de recuperación.

## Notas

- `./wal_archive/` y `./backup/` se generan y destruyen en cada corrida
  (ver `.gitignore`); no se versionan.
- El contenedor de recuperación usa un volumen Docker separado
  (`pitr-demo-restore-data`) para no tocar los datos "en producción" del
  contenedor principal mientras este sigue corriendo, tal como se explica en
  el post sobre restaurar en un entorno distinto para no interrumpir el
  servicio original.
