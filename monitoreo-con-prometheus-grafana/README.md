# Monitoreo con Prometheus y Grafana

Ejemplo ejecutable del post [Monitoreo con Prometheus y Grafana](https://www.devopsfreelance.pro/blog/posts/monitoreo-con-prometheus-grafana/).

## Que demuestra

Un stack minimo de observabilidad con Docker Compose:

- **demo_app**: una app Python sin dependencias externas que expone dos endpoints, `/work` (simula requests con latencia variable y ~5% de fallos) y `/metrics` (metricas en formato Prometheus: contador de requests por status y suma/cantidad de duraciones).
- **Prometheus**: scrapea `demo_app` cada 5 segundos (`prometheus.yml`) y evalua una regla de alerta de latencia y otra de tasa de error (`alert-rules.yml`).
- **Grafana**: viene provisionado automaticamente con el datasource de Prometheus y un dashboard ("Demo App - Prometheus") con paneles de requests por segundo, latencia promedio y tasa de error, tal como se describe en el post.

Es el mismo flujo que explica el articulo: la app expone metricas -> Prometheus las recolecta y evalua reglas de alerta -> Grafana las consulta con PromQL y las visualiza.

## Requisitos

- Docker y Docker Compose (`docker compose version`)
- `curl` (para generar trafico de prueba, ya viene en la mayoria de distros)

No requiere cuentas ni servicios pagos: todo corre local en contenedores.

## Pasos para correrlo

1. Levantar el stack:

```bash
cd monitoreo-con-prometheus-grafana
docker compose up -d --build
```

2. Generar trafico contra la demo app para que haya metricas que ver:

```bash
chmod +x load.sh
./load.sh
```

Dejalo corriendo en una terminal aparte unos 20-30 segundos y despues cortalo con `Ctrl+C`.

3. Abrir Prometheus y verificar el target `demo_app` en estado `UP`:

```
http://localhost:9090/targets
```

Tambien podes probar una consulta PromQL directamente, por ejemplo:

```
http://localhost:9090/graph?g0.expr=sum(rate(app_requests_total[1m]))%20by%20(status)&g0.tab=0
```

4. Ver las reglas de alerta cargadas:

```
http://localhost:9090/alerts
```

5. Abrir Grafana (usuario `admin`, password `admin`, se pide cambiarla en el primer login pero se puede omitir):

```
http://localhost:3000
```

El datasource de Prometheus y el dashboard "Demo App - Prometheus" ya estan provisionados: apenas entres a Grafana, andá a **Dashboards** y abrí "Demo App - Prometheus" para verlo con datos en vivo.

6. Para apagar todo:

```bash
docker compose down
```

## Salida esperada

- En `http://localhost:9090/targets`: el job `demo_app` con estado `UP` y el job `prometheus` (scrape de si mismo) tambien `UP`.
- Con `load.sh` corriendo, la consulta `sum(rate(app_requests_total[1m])) by (status)` en Prometheus muestra dos series (`success` y `error`), con `error` en general cerca del 5% del total.
- En Grafana, el dashboard "Demo App - Prometheus" muestra tres paneles actualizandose cada 5 segundos: requests por segundo por status, latencia promedio en segundos, y tasa de error en porcentaje.
- Si detenes `load.sh` un rato largo, la alerta `HighRequestLatency` no deberia dispararse (la app responde rapido cuando no hay contencion); si generas trafico muy agresivo (varios `load.sh` en paralelo) vas a poder ver en `http://localhost:9090/alerts` como las alertas pasan de `inactive` a `pending`/`firing` cuando se cumplen las condiciones.

## Notas

- Este ejemplo no incluye Alertmanager (no hay notificaciones reales por email/Slack/etc); el foco es mostrar la evaluacion de reglas de alerta en Prometheus, que es la parte central para entender el flujo. Si queres notificaciones reales, se agrega un contenedor de `prom/alertmanager` y se apunta `alerting.alertmanagers` en `prometheus.yml` a el.
- Las credenciales de Grafana (`admin`/`admin`) son solo para este entorno local descartable. No usar en un entorno real sin cambiarlas.
