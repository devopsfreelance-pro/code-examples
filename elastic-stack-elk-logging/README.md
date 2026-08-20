# Elastic Stack (ELK) para logging: ejemplo minimo con Docker Compose

Ejemplo de código para el post: [Elasticsearch: Guía completa del stack ELK para logging](https://www.devopsfreelance.pro/blog/posts/elastic-stack-elk-logging/)

## Qué demuestra

El post explica el flujo de datos del Elastic Stack: **recolección → procesamiento →
indexación → visualización**, con Logstash parseando logs crudos, Elasticsearch
indexándolos y Kibana exponiéndolos para búsqueda y dashboards.

Este ejemplo reproduce ese pipeline completo en tu máquina, sin cuentas cloud:

- **Elasticsearch** (nodo único, sin seguridad, heap limitado a 512 MB) actúa como
  motor de indexación y búsqueda, tal como describe la sección "Componentes
  principales y sus roles" del post.
- **Logstash** lee un archivo de logs de acceso estilo Apache
  (`sample-logs/access.log`), lo parsea con un filtro `grok` usando el patrón
  `COMBINEDAPACHELOG` (exactamente el ejemplo que menciona el artículo: "extraer
  automáticamente campos como IP del cliente, código de respuesta HTTP, tiempo de
  respuesta, y URL solicitada"), tipa los campos `response`/`bytes` como enteros y
  los envía a Elasticsearch.
- **Kibana** queda disponible para explorar esos datos en `http://localhost:5601`,
  cumpliendo el rol de capa de visualización que describe el post.
- `query-logs.sh` reproduce por API HTTP lo que harías en Kibana Discover: ver los
  últimos eventos, filtrar errores 5xx y agregar por código de respuesta, tal como
  ilustra la sección "Centralización y búsqueda unificada".

No se activa X-Pack security (usuarios/TLS) porque es un demo local de un solo
nodo; el post explica en la sección "Seguridad y control de acceso" por qué en
producción sí hay que habilitarlo.

## Requisitos

- Docker y Docker Compose (plugin `docker compose`, v2)
- `curl` (para `query-logs.sh`)
- ~2.5 GB de RAM libres (Elasticsearch + Logstash + Kibana) y los puertos `9200` y
  `5601` disponibles en tu máquina

No hay secretos, API keys ni cuentas cloud involucradas.

## Pasos para correrlo

1. Levantar el stack (Elasticsearch, Logstash y Kibana):

   ```bash
   docker compose up -d
   ```

2. Esperar a que Elasticsearch reporte estado saludable (puede tardar 30-60
   segundos la primera vez, mientras descarga las imágenes):

   ```bash
   docker compose ps
   ```

   Logstash arranca automáticamente después (`depends_on: service_healthy`), lee
   `sample-logs/access.log` una sola vez (`exit_after_read => true`) y termina su
   ejecución tras indexar los eventos. Podés seguir su salida con:

   ```bash
   docker compose logs -f logstash
   ```

   Cuando veas líneas `rubydebug` con los campos parseados (`clientip`, `verb`,
   `request`, `response`, etc.), el pipeline terminó de indexar.

3. Consultar los logs centralizados desde la terminal:

   ```bash
   chmod +x query-logs.sh
   ./query-logs.sh
   ```

4. (Opcional) Explorar los datos en Kibana:

   - Abrir `http://localhost:5601`
   - Ir a **Stack Management → Index Patterns / Data Views** y crear un data view
     con el patrón `elk-demo-logs-*`, usando `@timestamp` como campo de tiempo
   - Ir a **Discover** para ver y filtrar los 15 eventos indexados

5. Apagar todo:

   ```bash
   docker compose down -v
   ```

## Salida esperada

`query-logs.sh` debería mostrar algo similar a esto (resumido):

```
== Salud del cluster ==
{
  "cluster_name" : "docker-cluster",
  "status" : "green",
  ...
}

== Documentos indexados en elk-demo-logs-* ==
{
  "count" : 15,
  ...
}

== Ultimos 5 eventos (por timestamp) ==
...
"clientip" : "203.0.113.24",
"verb" : "GET",
"request" : "/api/products",
"response" : 200
...

== Requests con respuesta 5xx (busqueda de errores) ==
...
"request" : "/api/checkout",
"response" : 500
...
(3 resultados: las 3 líneas de /api/checkout en access.log)

== Conteo de requests agrupado por codigo de respuesta ==
...
"buckets" : [
  { "key" : 200, "doc_count" : 6 },
  { "key" : 500, "doc_count" : 3 },
  { "key" : 404, "doc_count" : 2 },
  ...
]
```

## Archivos

- `docker-compose.yml` - stack de tres servicios (Elasticsearch, Logstash, Kibana)
- `logstash/pipeline/logstash.conf` - pipeline input (file) → filter (grok + date) →
  output (elasticsearch)
- `logstash/config/logstash.yml` - configuración mínima de Logstash
- `sample-logs/access.log` - 15 líneas de log estilo Apache combined, con algunos
  errores 404/500 y 401 para poder filtrar
- `query-logs.sh` - consultas de ejemplo contra la API de Elasticsearch (salud,
  conteo, últimos eventos, filtro por errores, agregación)
