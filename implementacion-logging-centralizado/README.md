# Logging centralizado con Fluent Bit + Loki + Grafana

Ejemplo de código para el post: [Centralización de Logs: ELK vs Fluentd vs Graylog (Guía 2026)](https://www.devopsfreelance.pro/blog/posts/implementacion-logging-centralizado/)

## Qué demuestra

El post compara ELK, Fluentd/Fluent Bit y Graylog para centralizar logs. Este ejemplo
implementa el patrón de tres capas descrito en el artículo (recolección, procesamiento,
almacenamiento y consulta) usando componentes livianos que corren en tu máquina sin
licencias ni cuentas cloud:

- **Dos apps de ejemplo** (`app-payments`, `app-orders`) que emiten logs **estructurados
  en JSON** a stdout, tal como recomienda la sección "Logging estructurado: la base de
  todo" del post.
- **Fluent Bit** como capa de recolección y procesamiento: recibe los logs via el
  driver `fluentd` de Docker, los parsea con un `PARSER` de tipo JSON y los reenvía
  a Loki.
- **Loki** como backend de almacenamiento e indexación (la alternativa liviana a
  Elasticsearch que menciona el post en la capa de almacenamiento).
- **Grafana** como interfaz de consulta y dashboards, cumpliendo el mismo rol que
  Kibana o la UI de Graylog en el artículo.
- `query-logs.sh` reproduce por API HTTP lo que harías en Discover (Kibana) o en el
  buscador de Graylog: ver los últimos logs, filtrar por `level=ERROR` y listar los
  labels/streams disponibles.

No incluye ELK completo (Elasticsearch + Logstash + Kibana) ni Graylog porque ambos
requieren varios GB de RAM para un demo local; Fluent Bit + Loki ilustra el mismo
patrón arquitectónico con una huella mínima.

## Requisitos

- Docker y Docker Compose (plugin `docker compose`, v2)
- `curl` y `python3` (ya vienen en la mayoría de las distros; se usan solo para
  formatear la salida de `query-logs.sh`)
- ~600 MB de RAM libres y los puertos `3000`, `3100` y `24224` disponibles en tu
  máquina

No hay secretos, API keys ni cuentas cloud involucradas.

## Pasos para correrlo

1. Levantar el stack (Loki, Fluent Bit, Grafana y las dos apps generadoras de logs):

   ```bash
   docker compose up -d
   ```

2. Esperar unos 15-20 segundos a que Loki y Fluent Bit terminen de arrancar y las
   apps generen las primeras líneas de log:

   ```bash
   sleep 20
   ```

3. Consultar los logs centralizados desde la terminal:

   ```bash
   ./query-logs.sh
   ```

4. (Opcional) Explorar los logs de forma visual en Grafana:

   ```bash
   # abrir en el navegador
   xdg-open http://localhost:3000/explore 2>/dev/null || echo "Abrí http://localhost:3000/explore"
   ```

   Grafana ya tiene el datasource de Loki provisto automáticamente (login anónimo
   habilitado solo para este demo local). En **Explore**, elegí el datasource
   `Loki` y ejecutá la query:

   ```
   {job="demo-logs"}
   ```

5. Apagar y limpiar todo:

   ```bash
   docker compose down -v
   ```

## Salida esperada

Al correr `./query-logs.sh` deberías ver algo similar a esto (los valores concretos
de timestamp, latencia y trace_id van a variar):

```
== Ultimos 20 logs (todos los servicios, job=demo-logs) ==
{
    "status": "success",
    "data": {
        "resultType": "streams",
        "result": [
            {
                "stream": {
                    "job": "demo-logs",
                    "service": "payments-api",
                    "level": "INFO"
                },
                "values": [
                    [
                        "1755000000000000000",
                        "{\"timestamp\":\"2026-08-20T11:42:10-03:00\",\"level\":\"INFO\",\"service\":\"payments-api\",\"trace_id\":\"tr-12345\",\"message\":\"Payment processed successfully\",\"latency_ms\":187}"
                    ]
                ]
            }
        ]
    }
}
...

== Solo logs con level=ERROR (busqueda filtrada, tipo Discover/Search) ==
{
    "status": "success",
    "data": {
        "resultType": "streams",
        "result": [
            {
                "stream": {
                    "job": "demo-logs",
                    "service": "payments-api",
                    "level": "ERROR"
                },
                "values": [
                    [
                        "1755000010000000000",
                        "{\"timestamp\":\"2026-08-20T11:42:20-03:00\",\"level\":\"ERROR\",\"service\":\"payments-api\",\"trace_id\":\"tr-12350\",\"message\":\"Failed to process payment\",\"latency_ms\":342}"
                    ]
                ]
            }
        ]
    }
}

== Labels detectados (equivalente a los 'streams' de Graylog) ==
{
    "status": "success",
    "data": [
        "job",
        "level",
        "service"
    ]
}
```

`app-payments` emite un `ERROR` cada 5 líneas ("Failed to process payment") y
`app-orders` emite un `WARN` cada 7 líneas ("Order queue backlog detected"); el resto
son logs `INFO` normales. Si la segunda consulta (`level=ERROR`) devuelve
`"result": []`, esperá unos segundos más: recién vas a tener un ERROR después de la
quinta línea que emite `app-payments` (~10 segundos desde que arrancó).

## Estructura de archivos

- `docker-compose.yml` – orquesta Loki, Fluent Bit, Grafana y las dos apps demo.
- `fluent-bit.conf` – pipeline de Fluent Bit: input `forward` (recibe logs de
  Docker), filtro `parser` (JSON) y outputs a `stdout` y a Loki.
- `parsers.conf` – definición del parser JSON usado por Fluent Bit.
- `grafana-datasources.yml` – provisioning automático del datasource Loki en Grafana.
- `query-logs.sh` – consultas de ejemplo contra la API HTTP de Loki.
