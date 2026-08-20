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
