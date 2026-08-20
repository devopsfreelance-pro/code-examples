# Admin automation: cron + script idempotente con lock y retención

Ejemplo de código para el post [Admin Automation: Guía Completa para Equipos DevOps 2026](https://www.devopsfreelance.pro/blog/posts/automatizacion-tareas-administrativas/).

## Qué demuestra

El post explica que la admin automation no es solo "un script en cron", sino un
script robusto (idempotente, con logging, lock y fail-fast) disparado por un
scheduler. Este ejemplo reproduce exactamente esos elementos, ejecutables en
minutos:

- **Task scheduling con cron** (`crontab`, montado en `/etc/cron.d/`): el
  contenedor corre `cleanup-logs.sh` en cada tick, igual que los `crontab`
  del post (aquí cada minuto para que se vea rápido; en producción sería
  `0 2 * * *`, tal como muestra el comentario del propio archivo).
- **Script robusto** (`scripts/cleanup-logs.sh`): modo estricto
  (`set -euo pipefail`), función `log()` con timestamp, `error_exit()` para
  fail-fast, validaciones de pre-condiciones sobre el directorio de logs y
  **retención configurable** (`RETENTION_DAYS`, default 7 días).
- **Lock file** (`/var/lock/cleanup-logs.lock` + `trap release_lock EXIT`):
  evita que dos ejecuciones se pisen si una tarda más que el intervalo del
  cron, igual que el patrón "Problemas de concurrencia" del post.
- **Idempotencia**: correr el script muchas veces seguidas produce el mismo
  resultado (los archivos ya borrados simplemente no vuelven a aparecer).

El `entrypoint.sh` genera, al arrancar el contenedor, 5 logs "viejos" (1, 5,
10, 20 y 30 días de antigüedad) y 3 "recientes" (0, 1 y 2 días) usando
`touch -d`, para que en el primer tick de cron se vea en vivo cuáles
sobreviven y cuáles se eliminan.

## Requisitos

- Docker y Docker Compose (`docker compose version`).

## Cómo correrlo

```bash
cd automatizacion-tareas-administrativas

# Levanta el contenedor (build + start) en primer plano
docker compose up --build
```

Vas a ver primero el listado inicial de `/var/log/app` con los 8 archivos de
ejemplo, y unos segundos después (en el próximo minuto en punto) el cron
dispara el script y aparecen líneas como:

```
=== Estado inicial de /var/log/app ===
-rw-r--r-- 1 root root 0 ... app-old-10d.log
-rw-r--r-- 1 root root 0 ... app-old-1d.log
-rw-r--r-- 1 root root 0 ... app-old-20d.log
-rw-r--r-- 1 root root 0 ... app-old-30d.log
-rw-r--r-- 1 root root 0 ... app-old-5d.log
-rw-r--r-- 1 root root 0 ... app-recent-0d.log
-rw-r--r-- 1 root root 0 ... app-recent-1d.log
-rw-r--r-- 1 root root 0 ... app-recent-2d.log
===================================
[2026-01-01 00:01:00] Iniciando limpieza de logs en /var/log/app (retención: 7d)
[2026-01-01 00:01:00] Eliminado: /var/log/app/app-old-10d.log
[2026-01-01 00:01:00] Eliminado: /var/log/app/app-old-20d.log
[2026-01-01 00:01:00] Eliminado: /var/log/app/app-old-30d.log
[2026-01-01 00:01:00] Limpieza completada. 3 archivo(s) eliminado(s).
```

Los archivos de 0, 1, 2 y 5 días quedan intactos (retención de 7 días); solo
se borran los de 10, 20 y 30 días. En el próximo tick (un minuto después) el
script vuelve a correr y ya no hay nada que borrar, demostrando idempotencia:

```
[2026-01-01 00:02:00] Iniciando limpieza de logs en /var/log/app (retención: 7d)
[2026-01-01 00:02:00] Limpieza completada. 0 archivo(s) eliminado(s).
```

Para verificar el estado de archivos desde el host (quedan mapeados en
`./output/`), en otra terminal:

```bash
ls -la automatizacion-tareas-administrativas/output/app/
```

Para cortar el demo:

```bash
docker compose down
```

Nota: como el contenedor corre como root, `./output/` queda con archivos
propiedad de root. Para borrarlo sin `sudo`:

```bash
docker run --rm -v "$(pwd):/work" debian:bookworm-slim sh -c "rm -rf /work/output"
```

## Llevarlo a producción

Cambios mínimos respecto al demo:

- Cambiar la línea del `crontab` a algo como `0 2 * * *` (diario a las 2 AM),
  tal como se explica en el post.
- Ajustar `RETENTION_DAYS` a la política real de retención (variable de
  entorno del contenedor o `docker-compose.yml`).
- Reemplazar el volumen local por el punto de montaje real de logs de la
  aplicación.
- Enviar `SCRIPT_LOG` a un sistema centralizado (ver el post enlazado sobre
  [monitoreo con Prometheus y Grafana](https://www.devopsfreelance.pro/blog/posts/monitoreo-con-prometheus-grafana/))
  en vez de a un archivo local.
