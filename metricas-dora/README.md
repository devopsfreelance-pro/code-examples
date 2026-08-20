# Métricas DORA: alertando para reducir el MTTR

Ejemplo de código para el post [Métricas DORA: Las 4 KPIs Clave para Medir DevOps](https://www.devopsfreelance.pro/blog/posts/metricas-dora/).

## Qué demuestra este ejemplo

El post explica las cuatro DORA metrics (deployment frequency, lead time for
changes, MTTR y change failure rate). El cálculo de las tres primeras a partir
de datos de despliegues ya está resuelto con un script Python ejecutable en
[`../metricas-kpis-devops/`](../metricas-kpis-devops/) — no tiene sentido
duplicarlo aquí.

Este ejemplo se enfoca en la pieza que el post de DORA cubre y el otro no: el
**MTTR**, y concretamente en la regla de alertas de Prometheus (`PrometheusRule`)
que aparece en la sección "Mean Time to Recovery" del artículo. Levanta un
mini laboratorio con:

1. Un servicio HTTP de juguete (`demo-app`) que expone `/metrics` en formato
   Prometheus con un contador `http_requests_total{status=...}`.
2. Un endpoint `/toggle-errors` para simular el inicio y el fin de un
   incidente (pasa de ~2% de errores a ~35% y viceversa).
3. Prometheus, con una regla de alerta `HighErrorRate` equivalente a la del
   post (adaptada de `PrometheusRule` de Prometheus Operator al formato de
   reglas de Prometheus standalone, ya que este demo corre en Docker, no en
   Kubernetes).

Al provocar el incidente y mirar el timestamp en que la alerta pasa a
`firing` y luego vuelve a `inactive` en la UI de Prometheus, se ve en vivo el
intervalo que en producción correspondería al MTTR: el tiempo entre que el
sistema detecta la degradación y que se recupera.

## Requisitos

- Docker y Docker Compose (`docker compose version`).
- Ningún otro requisito: `demo-app` usa solo la librería estándar de Python.

## Cómo correrlo

```bash
cd metricas-dora
docker compose up -d --build
```

Esperá unos segundos a que Prometheus haga el primer scrape, y generá tráfico
normal contra el servicio:

```bash
for i in $(seq 1 20); do curl -s http://localhost:8080/work; sleep 0.5; done
```

Abrí la UI de Prometheus y confirmá que la alerta está inactiva:

```
http://localhost:9090/alerts
```

Ahora simulá el inicio de un incidente (sube la tasa de error al ~35%) y
seguí generando tráfico:

```bash
curl -s http://localhost:8080/toggle-errors
for i in $(seq 1 40); do curl -s http://localhost:8080/work >/dev/null; sleep 0.5; done
```

En `http://localhost:9090/alerts` la regla `HighErrorRate` debería pasar de
`inactive` a `pending` y, unos 15 segundos después, a `firing`. Ese timestamp
de "firing" es el momento en que, en un entorno real, se dispararía el
`runbook_url` de la alerta y empezaría a contar el reloj del MTTR.

Cerrá el incidente y confirmá la recuperación:

```bash
curl -s http://localhost:8080/toggle-errors
for i in $(seq 1 20); do curl -s http://localhost:8080/work >/dev/null; sleep 0.5; done
```

La alerta vuelve a `inactive` en `http://localhost:9090/alerts` unos segundos
después de que la tasa de error baja del 5%. El tiempo entre el timestamp de
`firing` y el de vuelta a `inactive` es, en esencia, el MTTR que la métrica
DORA busca minimizar.

Para ver los contadores crudos que alimentan la regla:

```bash
curl -s http://localhost:8080/metrics
```

Salida esperada (los números varían según cuánto tráfico generaste):

```
# HELP http_requests_total Total de requests procesadas por status
# TYPE http_requests_total counter
http_requests_total{status="200"} 57
http_requests_total{status="500"} 23
```

Para bajar todo:

```bash
docker compose down
```

## Archivos

- `demo-app/app.py` - servicio HTTP mínimo (stdlib de Python) con `/work`,
  `/toggle-errors`, `/metrics` y `/health`.
- `demo-app/Dockerfile` - imagen `python:3.12-alpine` para `demo-app`.
- `prometheus.yml` - configuración de scraping de Prometheus, apunta a
  `demo-app:8080` cada 5s.
- `alerts.yml` - regla `HighErrorRate` (y `ServiceDown` de bonus) equivalente
  a la del post, adaptada a formato de reglas standalone de Prometheus.
- `docker-compose.yml` - levanta `demo-app` y `prometheus` en la misma red.

No hay secretos ni cuentas externas involucradas: todo corre localmente en
contenedores efímeros.
