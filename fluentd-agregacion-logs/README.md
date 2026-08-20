# Fluentd: pipeline de agregación de logs con routing y copy a dos destinos

Ejemplo ejecutable que acompaña al post [Fluentd: Guía Completa de Agregación de Logs en 2025](https://www.devopsfreelance.pro/blog/posts/fluentd-agregacion-logs/).

## Qué demuestra

El concepto central del post: el pipeline de Fluentd (entrada -> filtro -> buffering -> salida) con enrutamiento basado en tags, tomando como base la configuración avanzada del post (`record_transformer`, `grep` y `copy` a dos stores para eventos críticos), pero sin depender de Elasticsearch ni Kubernetes:

- Fluentd corre en Docker con el plugin `in_http` como entrada (en vez de `tail` sobre logs de contenedores), para poder disparar eventos con un simple `curl`.
- Un filtro `record_transformer` enriquece cada evento con `hostname` y `environment`, igual que en el post se agrega metadata de Kubernetes.
- Un filtro `grep` descarta eventos de health-check, replicando el filtro anti-ruido del post.
- Los eventos con tag `app.critical.*` se procesan con `<match>` + `@type copy`, que los duplica hacia **dos destinos simultáneos**: un archivo (`log-out/critical`) y `stdout` (equivalente al patrón Elasticsearch + Slack del post).
- El resto de eventos con tag `app.*` van a un único destino de archivo (`log-out/general`) con buffer en disco, tal como recomienda el post para cargas no críticas.

## Requisitos

- Docker y Docker Compose (`docker compose version`).
- `curl`.
- Puerto `9880` libre en localhost.

## Cómo correrlo

```bash
cd fluentd-agregacion-logs
docker compose up -d
```

Esperá unos 5 segundos a que Fluentd termine de arrancar, y después disparás los eventos de ejemplo:

```bash
chmod +x demo.sh
./demo.sh
```

Revisá los tres destinos que definió el pipeline:

```bash
# 1. Eventos críticos, duplicados a archivo por el store "file" del copy
find log-out -name 'critical*' -type f -exec cat {} \;

# 2. Los mismos eventos críticos también salieron por stdout (el store "stdout")
docker compose logs fluentd | grep app.critical

# 3. Eventos generales (el health-check NO debe aparecer, fue descartado por el grep)
find log-out -name 'general*' -type f -exec cat {} \;
```

Para detener y limpiar todo:

```bash
docker compose down -v
rm -rf log-out/*
```

## Salida esperada

En `log-out/critical...log` y en `docker compose logs fluentd` vas a ver los dos eventos críticos, con `hostname` y `environment` agregados por el `record_transformer`:

```
2026-08-20T12:00:01+00:00	app.critical.disk	{"message":"disk usage above 90% on node-3","level":"critical","hostname":"...","environment":"demo"}
2026-08-20T12:00:03+00:00	app.critical.payments	{"message":"payment service unreachable","level":"critical","hostname":"...","environment":"demo"}
```

En `log-out/general...log` vas a ver únicamente el evento `request completed in 120ms` (el `health-check ok` fue descartado por el filtro `grep`, tal como en el post se filtran los health-checks para reducir ruido).

## Notas

- No hay secretos ni cuentas involucradas: todo corre local en contenedores Docker.
- El plugin `@type file` de salida escribe archivos con nombres generados automáticamente (timestamp + hash del buffer), por eso el comando de verificación usa `find ... -exec cat` en vez de un nombre de archivo fijo.
- Si preferís ver el archivo de configuración completo, está en `conf/fluentd.conf`.
