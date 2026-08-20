# Distributed Systems Observability: tracing and correlation IDs in practice

Related post: [Distributed Tracing: A Practical Observability Guide](https://www.devopsfreelance.pro/blog/en/posts/distributed-tracing-observability-guide/)

## What this example demonstrates

Two FastAPI microservices (`service-a` and `service-b`) instrumented with
**OpenTelemetry**, illustrating the heart of the post: distributed tracing and
context propagation.

- `service-a` exposes `/checkout/{sku}` and calls `service-b` internally.
- `service-b` exposes `/inventory/{sku}` and simulates a query to a
  warehouse/database.
- When calling `service-b`, `service-a` automatically propagates the
  `traceparent` HTTP header (instrumentation from the `requests` library), so
  both services generate spans that end up **linked under the same
  trace_id**.
- That same `trace_id` is used as a **correlation ID** in the logs of both
  services (`logger.info("correlation_id=%s ...")`), exactly the
  mechanism described in the post for connecting telemetry across
  services.
- Traces are exported via OTLP/HTTP to **Jaeger**, where you can see the
  full trace of a checkout crossing both services.

## Requirements

- Docker and Docker Compose (`docker compose version`).
- Free ports on your machine: `8000`, `8001`, `16686`, `4318`.

## How to run it

```bash
cd observabilidad-sistemas-distribuidos

# 1. Levantar Jaeger + los dos servicios
docker compose up --build
```

Wait until you see something like this in the logs:

```
service-a  | INFO:     Uvicorn running on http://0.0.0.0:8000
service-b  | INFO:     Uvicorn running on http://0.0.0.0:8001
```

In another terminal, generate a distributed trace by doing a checkout:

```bash
curl http://localhost:8000/checkout/SKU-123
```

Expected output (`status` may vary between `confirmed` and `rejected`
because `service-b` simulates stock availability randomly):

```json
{"correlation_id":"4b1f2a...e9c3","sku":"SKU-123","status":"confirmed"}
```

Repeat the `curl` a few times to generate several traces:

```bash
for i in $(seq 1 5); do curl -s http://localhost:8000/checkout/SKU-$i; echo; done
```

Check the logs of both services: the same `correlation_id` shows up in
`service-a` and `service-b` for each request:

```bash
docker compose logs service-a service-b | grep correlation_id
```

Expected output (same `correlation_id` on both lines):

```
service-a  | ... correlation_id=4b1f2a...e9c3 inicia checkout sku=SKU-123
service-b  | ... correlation_id=4b1f2a...e9c3 recibida consulta de inventario sku=SKU-123
service-a  | ... correlation_id=4b1f2a...e9c3 sku=SKU-123 checkout confirmado
```

## View the distributed trace in Jaeger

1. Open http://localhost:16686
2. Under "Service", select `service-a`.
3. Click "Find Traces".
4. Open any trace: you'll see the `checkout` span from `service-a`
   containing the `check-warehouse-stock` span from `service-b`, with the
   real duration of each stage. That's distributed tracing: a single
   request, visualized across two services.

## Shutting down the environment

```bash
docker compose down
```

## Notes

- No paid accounts or services required: Jaeger runs 100% locally in a
  container.
- The code is intentionally minimal (2 endpoints, no real database)
  to focus on the context propagation and correlation ID mechanism,
  which is the central concept of the post.

---

## 🇪🇸 Versión en español

# Observabilidad en Sistemas Distribuidos: tracing y correlation IDs en la práctica

Post relacionado: [Distributed Observability: Guía Práctica para Sistemas Modernos](https://www.devopsfreelance.pro/blog/posts/observabilidad-sistemas-distribuidos/)

## Qué demuestra este ejemplo

Dos microservicios FastAPI (`service-a` y `service-b`) instrumentados con
**OpenTelemetry**, que ilustran el corazón del post: tracing distribuido y
context propagation.

- `service-a` expone `/checkout/{sku}` y llama internamente a `service-b`.
- `service-b` expone `/inventory/{sku}` y simula una consulta a un
  almacén/base de datos.
- Al llamar a `service-b`, `service-a` propaga automáticamente el header
  HTTP `traceparent` (instrumentación de la librería `requests`), por lo que
  ambos servicios generan spans que quedan **vinculados bajo el mismo
  trace_id**.
- Ese mismo `trace_id` se usa como **correlation ID** en los logs de ambos
  servicios (`logger.info("correlation_id=%s ...")`), exactamente el
  mecanismo que describe el post para conectar telemetría a través de
  servicios.
- Las trazas se exportan vía OTLP/HTTP a **Jaeger**, donde se puede ver la
  traza completa de un checkout atravesando los dos servicios.

## Requisitos

- Docker y Docker Compose (`docker compose version`).
- Puertos libres en tu máquina: `8000`, `8001`, `16686`, `4318`.

## Cómo correrlo

```bash
cd observabilidad-sistemas-distribuidos

# 1. Levantar Jaeger + los dos servicios
docker compose up --build
```

Esperá a ver en los logs algo como:

```
service-a  | INFO:     Uvicorn running on http://0.0.0.0:8000
service-b  | INFO:     Uvicorn running on http://0.0.0.0:8001
```

En otra terminal, generá una traza distribuida haciendo un checkout:

```bash
curl http://localhost:8000/checkout/SKU-123
```

Salida esperada (el `status` puede variar entre `confirmed` y `rejected`
porque `service-b` simula disponibilidad de stock al azar):

```json
{"correlation_id":"4b1f2a...e9c3","sku":"SKU-123","status":"confirmed"}
```

Repetí el `curl` unas cuantas veces para generar varias trazas:

```bash
for i in $(seq 1 5); do curl -s http://localhost:8000/checkout/SKU-$i; echo; done
```

Revisá los logs de ambos servicios: el mismo `correlation_id` aparece en
`service-a` y en `service-b` para cada request:

```bash
docker compose logs service-a service-b | grep correlation_id
```

Salida esperada (mismo `correlation_id` en ambas líneas):

```
service-a  | ... correlation_id=4b1f2a...e9c3 inicia checkout sku=SKU-123
service-b  | ... correlation_id=4b1f2a...e9c3 recibida consulta de inventario sku=SKU-123
service-a  | ... correlation_id=4b1f2a...e9c3 sku=SKU-123 checkout confirmado
```

## Ver la traza distribuida en Jaeger

1. Abrí http://localhost:16686
2. En "Service", elegí `service-a`.
3. Click en "Find Traces".
4. Abrí cualquier traza: vas a ver el span `checkout` de `service-a`
   conteniendo el span `check-warehouse-stock` de `service-b`, con la
   duración real de cada etapa. Eso es tracing distribuido: una sola
   solicitud, visualizada a través de dos servicios.

## Apagar el entorno

```bash
docker compose down
```

## Notas

- No requiere cuentas ni servicios pagos: Jaeger corre 100% local en un
  contenedor.
- El código es intencionalmente mínimo (2 endpoints, sin base de datos real)
  para enfocarse en el mecanismo de propagación de contexto y correlation
  IDs, que es el concepto central del post.
