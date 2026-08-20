# Monitoreo de microservicios: health checks, correlation ID y metricas RED

Ejemplo de código para el post [Monitoreo de microservicios](https://www.devopsfreelance.pro/blog/posts/monitoreo-microservicios/).

## Qué demuestra

Dos microservicios Flask (`order-service` e `inventory-service`) que ilustran los tres
mecanismos centrales que describe el post:

- **Health checks (liveness/readiness)**: cada servicio expone `/health/liveness` y
  `/health/readiness`; el readiness de `order-service` valida en vivo que
  `inventory-service` responde antes de reportarse como listo.
- **Correlation ID propagado entre servicios**: `order-service` genera (o reenvía) un
  `x-correlation-id`, lo propaga en la llamada HTTP a `inventory-service`, y ambos
  servicios lo incluyen en cada línea de log en formato JSON. Podés seguir una misma
  solicitud a través de los dos servicios buscando ese ID en los logs.
- **Métricas RED (Rate, Errors, Duration)** expuestas en `/metrics` con
  `prometheus_client`, scrapeadas por un Prometheus local definido en
  `prometheus.yml`, tal como se describe en la conclusión del post.

No incluye distributed tracing (Jaeger/OpenTelemetry) ni service mesh (Istio) porque
requieren infraestructura adicional; el objetivo de este mini-ejemplo es el flujo
health checks + correlation ID + métricas, que es reproducible en minutos con Docker
Compose solo.

## Requisitos

- Docker y Docker Compose (plugin `docker compose`)
- Puertos libres en el host: `5000`, `5001`, `9090`
- Sin cuentas ni credenciales externas (todo corre localmente)

## Cómo correrlo

```bash
cd monitoreo-microservicios
docker compose up --build
```

Esperá a ver en los logs que `order-service` y `inventory-service` quedaron arriba
(unos segundos, instalan sus dependencias de `requirements.txt` al iniciar).

En otra terminal, generá una orden de punta a punta:

```bash
curl http://localhost:5000/order
```

Salida esperada (el `order_id` y `correlation_id` van a variar):

```json
{
  "correlation_id": "3f1b2a4c-...",
  "inventory": {"available": true, "order_id": "9a3f2c1b"},
  "order_id": "9a3f2c1b",
  "status": "completed"
}
```

En los logs de `docker compose up` vas a ver, en `order-service` e
`inventory-service`, líneas JSON con el mismo `correlationId`, por ejemplo:

```
order-service     | {"service": "order-service", "correlationId": "3f1b2a4c-...", "event": "order_received", "order_id": "9a3f2c1b"}
inventory-service | {"service": "inventory-service", "correlationId": "3f1b2a4c-...", "event": "inventory_check", "order_id": "9a3f2c1b"}
order-service     | {"service": "order-service", "correlationId": "3f1b2a4c-...", "event": "order_completed", "order_id": "9a3f2c1b", "inventory_available": true}
```

Probá los health checks:

```bash
curl http://localhost:5000/health/liveness
curl http://localhost:5000/health/readiness
curl http://localhost:5001/health/liveness
```

Revisá las métricas RED en formato Prometheus:

```bash
curl http://localhost:5000/metrics | grep http_requests_total
```

Salida esperada (aumenta con cada request que hiciste):

```
http_requests_total{method="GET",path="/order",service="order-service",status_code="200"} 1.0
```

Abrí Prometheus en el navegador y confirmá que los dos targets están `UP`:

```
http://localhost:9090/targets
```

Para bajar todo:

```bash
docker compose down
```

## Estructura

```
monitoreo-microservicios/
├── docker-compose.yml       # orquesta order-service, inventory-service y Prometheus
├── prometheus.yml           # scrape config de los dos /metrics
├── requirements.txt         # dependencias compartidas (Flask, prometheus_client, requests)
├── order-service/app.py     # entrypoint: health checks + correlation ID + llamada downstream
└── inventory-service/app.py # servicio downstream: health checks + correlation ID recibido
```
