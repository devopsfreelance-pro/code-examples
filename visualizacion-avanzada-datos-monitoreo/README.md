# Visualización avanzada de datos de monitoreo

Ejemplo ejecutable del post [Guía Completa de Visualización avanzada de datos de monitoreo](https://www.devopsfreelance.pro/blog/posts/visualizacion-avanzada-datos-monitoreo/).

## Que demuestra

Un stack local con Docker Compose que arma, con Grafana provisionado automáticamente, el dashboard central que describe el post: un dashboard **RED** (Rate, Errors, Duration) combinado con un **dashboard de SLO** (error budget y burn rate), usando exactamente las mismas queries PromQL de la guía.

- **payment_service**: una app Python (solo librería estándar, sin dependencias externas) que simula un servicio con latencia **bimodal**: la mayoría de las requests son rápidas (5-80 ms) pero ~15% son lentas (300 ms a 1.2 s), y ~3% fallan con status 500. Expone `/metrics` con un histograma real (`http_request_duration_seconds_bucket`), no solo un promedio, para poder graficar percentiles y un heatmap de verdad.
- **Prometheus**: scrapea `payment_service` cada 5 segundos.
- **Grafana**: viene provisionado con el datasource de Prometheus y el dashboard `red-slo-dashboard.json`, que incluye:
  - **Rate**: panel time series con `sum(rate(http_requests_total[1m]))`.
  - **Errors**: panel stat con el porcentaje de error, con umbrales rojo/amarillo/verde.
  - **Duration p95**: panel time series con `histogram_quantile(0.95, ...)`.
  - **Heatmap de latencia**: panel heatmap con `sum(increase(http_request_duration_seconds_bucket[1m])) by (le)`, que revela la distribución bimodal (la cola pesada que un p95 solo no muestra).
  - **Error budget restante**: gauge con la query de error budget del post, adaptada a un SLO de 99% sobre una ventana de 15 minutos (en vez de 30 días, para que se vea en un demo local corto).
  - **Burn rate**: time series con la query de burn rate del post (ventana de 5 minutos); si sube por encima de 1x, se está consumiendo el error budget más rápido de lo sostenible.

Es el mismo flujo que explica el artículo: la app expone métricas con histogramas -> Prometheus las recolecta -> Grafana las consulta con PromQL siguiendo la metodología RED y visualiza el estado del SLO.

## Requisitos

- Docker y Docker Compose (`docker compose version`)
- `curl` (para generar tráfico de prueba, ya viene en la mayoría de distros)

No requiere cuentas ni servicios pagos: todo corre local en contenedores.

## Pasos para correrlo

1. Levantar el stack:

```bash
cd visualizacion-avanzada-datos-monitoreo
docker compose up -d --build
```

2. Generar tráfico contra la app para que haya datos que ver:

```bash
chmod +x load.sh
./load.sh
```

Dejalo corriendo en una terminal aparte 1-2 minutos (cuantos más datos, mejor se ve el heatmap y el error budget) y después cortalo con `Ctrl+C`.

3. Verificar que Prometheus tiene el target `payment-service` en estado `UP`:

```
http://localhost:9090/targets
```

También podés probar directamente una de las queries del post:

```
http://localhost:9090/graph?g0.expr=histogram_quantile(0.95%2C%20sum%20by%20(le)%20(rate(http_request_duration_seconds_bucket%7Bservice%3D%22payment%22%7D%5B1m%5D)))&g0.tab=0
```

4. Abrir Grafana (usuario `admin`, password `admin`; pide cambiarla en el primer login, se puede omitir con "Skip"):

```
http://localhost:3000
```

5. Ir a **Dashboards** y abrir **"Payment Service - RED + SLO (demo del post)"**. Ya está provisionado, no hace falta importarlo a mano.

6. Para apagar todo:

```bash
docker compose down
```

## Salida esperada

- En `http://localhost:9090/targets`: el job `payment-service` en estado `UP`.
- Con `load.sh` corriendo, en el dashboard de Grafana (esperá 15-20 segundos para que haya varios scrapes):
  - **Rate**: una línea que se mueve alrededor de las requests/seg que genera `load.sh` (~30 req/s con la configuración por defecto).
  - **Error Rate**: un valor cercano al 3%, en verde (por debajo del umbral amarillo de 2% solo si baja el tráfico; con tráfico sostenido va a estar cerca del límite amarillo/rojo, que es la idea: ver el umbral con significado).
  - **Duration p95**: una línea que se mantiene mayormente baja pero con picos, reflejando el 15% de requests lentas.
  - **Heatmap**: dos bandas de color bien diferenciadas, una en la franja de 5-80 ms (la mayoría) y otra en 300 ms-1.2 s (la cola pesada) — el patrón bimodal que el p95 por sí solo no revela.
  - **Error budget restante**: un gauge entre 0 y 1 (100%) que baja a medida que se acumulan errores dentro de la ventana de 15 minutos.
  - **Burn rate**: una línea que sube por encima de 1x cuando la tasa de error supera el 1% (el objetivo del SLO del 99%), señal de que el budget se está consumiendo más rápido de lo sostenible.

## Notas

- Las ventanas de la query de error budget (15m) y burn rate (5m) están acortadas respecto a las del post (30d / 1h) a propósito, para que el demo local muestre resultados sin esperar semanas. En producción usá las ventanas del artículo (30 días para el budget total, 1 hora para el burn rate a corto plazo).
- Las credenciales de Grafana (`admin`/`admin`) son solo para este entorno local descartable. No usar en un entorno real sin cambiarlas.
- Este ejemplo no cubre Grafonnet (dashboard-as-code): el dashboard acá se provisiona como JSON estático vía volumen, que es la forma más simple de versionar dashboards en Git y es la base sobre la que Grafonnet genera el mismo tipo de JSON de forma programática.
