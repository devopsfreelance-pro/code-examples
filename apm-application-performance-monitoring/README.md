# APM Monitoreo: ejemplo ejecutable

Post: [APM Monitoreo: Optimizando el Rendimiento de tus Aplicaciones](https://www.devopsfreelance.pro/blog/posts/apm-application-performance-monitoring/)

## Qué demuestra este ejemplo

Un stack local minimo con los tres pilares de APM que describe el post:

- **Instrumentación automática y manual** con OpenTelemetry en una app Node.js/Express (`app/instrumentation.js` + spans manuales en `app/server.js`).
- **Trazabilidad distribuida**: cada request genera spans (incluyendo sub-spans hijos) visibles en Jaeger, igual que el ejemplo JSON de traza del post. El endpoint `/api/checkout` simula a propósito un cuello de botella (`chargePayment`) para que se vea claramente en la traza, análogo al ejemplo de profiling del artículo.
- **Monitoreo de infraestructura/métricas**: la app expone `/metrics` en formato Prometheus (latencia por ruta con histogramas, igual que las queries `histogram_quantile` de los ejemplos de alertas del post), y Prometheus las scrapea.

No incluye dashboards de Grafana ni las reglas de alerta completas del post (serían overkill para un mini-ejemplo); las queries PromQL de latencia/errores del post funcionan tal cual contra las métricas expuestas acá si querés agregar Grafana después.

## Requisitos

- Docker y Docker Compose (`docker compose version`)
- Puertos libres en tu máquina: `3000`, `9090`, `16686`, `4318`

## Cómo correrlo

```bash
cd apm-application-performance-monitoring
docker compose up --build
```

Esperá a ver en los logs: `apm-demo-app escuchando en puerto 3000`.

En otra terminal, generá tráfico (endpoint rápido, endpoint lento con cuello de botella, y un endpoint que falla):

```bash
for i in $(seq 1 20); do curl -s http://localhost:3000/api/orders > /dev/null; done
for i in $(seq 1 10); do curl -s http://localhost:3000/api/checkout > /dev/null; done
curl -s http://localhost:3000/api/payment-fail
```

### Ver las trazas distribuidas (Jaeger)

Abrí http://localhost:16686 , elegí el servicio `apm-demo-app` en "Service", click en "Find Traces". Vas a ver:

- Trazas de `GET /api/orders` con duración corta (~20-80ms).
- Trazas de `GET /api/checkout` con dos spans hijos (`validateCart`, `chargePayment`), donde `chargePayment` domina el tiempo total (~300-600ms), igual que el `updateInventory` del ejemplo de profiling del post.
- Una traza de `GET /api/payment-fail` marcada con el ícono de error (span con excepción registrada).

### Ver las métricas crudas (formato Prometheus)

```bash
curl -s http://localhost:3000/metrics | grep http_request_duration_seconds
```

### Ver las métricas en Prometheus

Abrí http://localhost:9090 , pestaña "Graph", y ejecutá por ejemplo:

```
histogram_quantile(0.95, sum(rate(http_request_duration_seconds_bucket{route="/api/checkout"}[5m])) by (le))
```

Esa es la misma query (adaptada al label `route` de este ejemplo) que usa el post en la alerta `HighLatency` de Prometheus.

## Salida esperada

- `docker compose up` levanta 3 contenedores: `apm-demo-app`, `apm-demo-jaeger`, `apm-demo-prometheus`.
- Jaeger UI (`localhost:16686`) muestra trazas del servicio `apm-demo-app` con spans padre/hijo.
- `curl localhost:3000/metrics` devuelve métricas en texto plano, incluyendo `http_request_duration_seconds_bucket`.
- Prometheus (`localhost:9090`, pestaña "Status > Targets") muestra el target `apm-demo-app` en estado `UP`.

## Limpieza

```bash
docker compose down
```

No hay secretos ni cuentas externas involucradas: todo corre local, sin API keys de New Relic/Datadog/Dynatrace (a diferencia de la app real del post, que sí las requiere).
