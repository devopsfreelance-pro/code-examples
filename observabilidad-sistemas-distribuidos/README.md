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
