# Loki: Label-Indexed Logs, Prometheus-Style

Code example for the post [Grafana Loki Tutorial: Prometheus-Style Log Aggregation](https://www.devopsfreelance.pro/blog/en/posts/grafana-loki-tutorial/).

## What it demonstrates

The post explains Grafana Loki's core idea: instead of indexing the full content of every log line (like Elasticsearch or other systems do), Loki indexes only **labels**, the same way Prometheus indexes series by labels instead of by each metric's value. The log content stays compressed and is only read when a query actually needs it.

This example spins up:

- **Loki** in monolithic mode (single binary) with local filesystem storage.
- A **log generator** (`generate-logs.sh`) that pushes synthetic logs directly to Loki's HTTP API (`/loki/api/v1/push`), simulating what Promtail would do collecting logs from a real app. Each log carries the labels `job="demo-app"` and `level="info"` or `level="error"`.
- **Grafana** with the Loki datasource already provisioned, to explore the logs with LogQL from the UI.
- A `query-logs.sh` script that queries Loki from the command line using LogQL, showing how filtering happens **by label**, not by free text.

## Requirements

- Docker and Docker Compose (the `docker compose` plugin).
- `curl` and `python3` on the host (used only by `query-logs.sh` to pretty-print JSON).

## Steps to run it

1. Bring up the stack:

   ```bash
   docker compose up -d
   ```

2. Wait about 15-20 seconds for Loki to finish initializing and the generator to start sending logs:

   ```bash
   docker logs -f log-generator
   ```

   (Ctrl+C to stop following, no need to wait for it to finish).

3. Query the logs with LogQL from the terminal:

   ```bash
   ./query-logs.sh
   ```

4. (Optional) Explore in Grafana: open [http://localhost:3000](http://localhost:3000) (anonymous login enabled, you go straight in as Admin), go to **Explore**, pick the **Loki** datasource and run a LogQL query, for example:

   ```logql
   {job="demo-app"}
   ```

   or filtering only errors:

   ```logql
   {job="demo-app", level="error"}
   ```

5. Tear down the stack when you're done:

   ```bash
   docker compose down -v
   ```

## Expected output

`./query-logs.sh` first shows the labels Loki knows about (the system's actual "index"):

```json
{
    "status": "success",
    "data": [
        "job",
        "level"
    ]
}
```

Then, the latest logs from the `{job="demo-app"}` stream, grouped by label combination (`level="info"` and `level="error"` end up in separate streams):

```json
{
    "status": "success",
    "data": {
        "resultType": "streams",
        "result": [
            {
                "stream": { "job": "demo-app", "level": "error" },
                "values": [
                    ["1787238989000000000", "{\"level\":\"error\",\"msg\":\"request procesado #10\",\"path\":\"/api/orders\"}"]
                ]
            },
            {
                "stream": { "job": "demo-app", "level": "info" },
                "values": [
                    ["1787238986000000000", "{\"level\":\"info\",\"msg\":\"request procesado #9\",\"path\":\"/api/orders\"}"]
                ]
            }
        ]
    }
}
```

And finally, the same query but filtered to only `level="error"` (the equivalent of filtering a Prometheus metric by a label): only the stream with that label shows up, without having to scan the text of every line.

## Files

- `docker-compose.yml` - orchestrates Loki, the log generator, and Grafana.
- `loki-config.yml` - minimal Loki configuration in monolithic mode (filesystem storage, boltdb-shipper).
- `generate-logs.sh` - generates synthetic logs and pushes them to Loki via HTTP push, labeling them with `job` and `level`.
- `grafana-datasource.yml` - automatically provisions the Loki datasource in Grafana.
- `query-logs.sh` - queries Loki with LogQL from the terminal (available labels, all logs, errors only).

## Notes

- This example uses direct HTTP push instead of Promtail to keep it minimal and free of a Kubernetes cluster dependency. The `scrape_configs` configuration with `kubernetes_sd_configs` explained in the post is the real way to collect logs in a cluster; here it's replaced with a simple script that illustrates the same labeling concept.
- Loki's data is stored in a volume inside the container; `docker compose down -v` removes it. No credentials or secrets are involved: `GF_AUTH_ANONYMOUS_ENABLED=true` is only meant to simplify the local demo, not for production use.

---

## 🇪🇸 Versión en español

# Loki: logs indexados por etiquetas, estilo Prometheus

Ejemplo de código para el post [Guía Completa de Loki para logs estilo prometheus](https://www.devopsfreelance.pro/blog/posts/loki-logs-estilo-prometheus/).

## Qué demuestra

El post explica la idea central de Grafana Loki: en vez de indexar el contenido completo de cada línea de log (como hacen Elasticsearch u otros sistemas), Loki indexa únicamente **etiquetas (labels)**, igual que Prometheus indexa series por labels en vez de por el valor de cada métrica. El contenido del log queda comprimido y solo se lee cuando una consulta realmente lo necesita.

Este ejemplo levanta:

- **Loki** en modo monolítico (single binary) con almacenamiento local en filesystem.
- Un **generador de logs** (`generate-logs.sh`) que empuja logs sintéticos directo a la API HTTP de Loki (`/loki/api/v1/push`), simulando lo que haría Promtail al recolectar logs de una app real. Cada log lleva las etiquetas `job="demo-app"` y `level="info"` o `level="error"`.
- **Grafana** con el datasource de Loki ya provisionado, para explorar los logs con LogQL desde la UI.
- Un script `query-logs.sh` que consulta Loki por línea de comandos usando LogQL, mostrando cómo se filtra **por etiqueta**, no por texto libre.

## Requisitos

- Docker y Docker Compose (plugin `docker compose`).
- `curl` y `python3` en el host (usados solo por `query-logs.sh` para pretty-print de JSON).

## Pasos para correrlo

1. Levantar el stack:

   ```bash
   docker compose up -d
   ```

2. Esperar unos 15-20 segundos a que Loki termine de inicializar y el generador empiece a enviar logs:

   ```bash
   docker logs -f log-generator
   ```

   (Ctrl+C para salir del follow, no hace falta que termine).

3. Consultar los logs por LogQL desde la terminal:

   ```bash
   ./query-logs.sh
   ```

4. (Opcional) Explorar en Grafana: abrir [http://localhost:3000](http://localhost:3000) (login anónimo habilitado, entra directo como Admin), ir a **Explore**, elegir el datasource **Loki** y correr una query LogQL, por ejemplo:

   ```logql
   {job="demo-app"}
   ```

   o filtrando solo errores:

   ```logql
   {job="demo-app", level="error"}
   ```

5. Bajar el stack cuando termines:

   ```bash
   docker compose down -v
   ```

## Salida esperada

`./query-logs.sh` muestra primero las etiquetas que Loki conoce (el "índice" real del sistema):

```json
{
    "status": "success",
    "data": [
        "job",
        "level"
    ]
}
```

Después, los últimos logs del stream `{job="demo-app"}`, agrupados por combinación de etiquetas (`level="info"` y `level="error"` quedan en streams separados):

```json
{
    "status": "success",
    "data": {
        "resultType": "streams",
        "result": [
            {
                "stream": { "job": "demo-app", "level": "error" },
                "values": [
                    ["1787238989000000000", "{\"level\":\"error\",\"msg\":\"request procesado #10\",\"path\":\"/api/orders\"}"]
                ]
            },
            {
                "stream": { "job": "demo-app", "level": "info" },
                "values": [
                    ["1787238986000000000", "{\"level\":\"info\",\"msg\":\"request procesado #9\",\"path\":\"/api/orders\"}"]
                ]
            }
        ]
    }
}
```

Y por último, la misma consulta pero filtrando solo `level="error"` (el equivalente a filtrar una métrica de Prometheus por un label): solo aparece el stream con esa etiqueta, sin haber tenido que escanear el texto de cada línea.

## Archivos

- `docker-compose.yml` - orquesta Loki, el generador de logs y Grafana.
- `loki-config.yml` - configuración mínima de Loki en modo monolítico (storage filesystem, boltdb-shipper).
- `generate-logs.sh` - genera logs sintéticos y los empuja a Loki vía HTTP push, etiquetándolos con `job` y `level`.
- `grafana-datasource.yml` - provisiona el datasource de Loki en Grafana automáticamente.
- `query-logs.sh` - consulta Loki con LogQL desde la terminal (labels disponibles, todos los logs, solo errores).

## Notas

- Este ejemplo usa push HTTP directo en vez de Promtail para mantenerlo mínimo y sin depender de un cluster de Kubernetes. La configuración de `scrape_configs` con `kubernetes_sd_configs` que se explica en el post es la forma real de recolectar logs en un cluster; acá se reemplaza por un script simple que ilustra el mismo concepto de etiquetado.
- Los datos de Loki se guardan en un volumen dentro del contenedor; `docker compose down -v` los elimina. No hay credenciales ni secretos involucrados: `GF_AUTH_ANONYMOUS_ENABLED=true` es solo para simplificar el demo local, no usar en producción.
