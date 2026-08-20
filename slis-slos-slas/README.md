# SLI SLO SLA: demo ejecutable con Prometheus

Ejemplo de codigo que acompaña al post [SLI SLO SLA: Guía Práctica para Medir Calidad de Servicio](https://www.devopsfreelance.pro/blog/posts/slis-slos-slas/).

## Que demuestra

El post explica la jerarquia SLI -> SLO -> SLA: los SLI son la medicion
objetiva (disponibilidad, latencia por percentil, excluyendo errores 4xx),
los SLO son el objetivo interno sobre esa medicion, y el SLA es un
compromiso externo mas conservador que el SLO. Este ejemplo levanta esa
cadena completa y ejecutable:

- Un servicio HTTP (`app.py`) instrumentado con las mismas metricas
  Prometheus que muestra el codigo del post (`http_request_duration_seconds`
  como histograma, `http_requests_total` como contador por status), que
  sirve un endpoint `/work` con latencia y errores realistas, y un
  endpoint `/admin/degrade` para simular un incidente que sube el 5xx.
- Prometheus (`prometheus.yml`) scrapeando esas metricas.
- `load_test.sh` generando trafico real contra el servicio.
- `sli_slo_report.py` consultando la API HTTP de Prometheus para calcular
  el SLI de disponibilidad (excluyendo 4xx, como recomienda el post) y el
  SLI de latencia p95, compararlos contra un SLO (99.9% / 200ms) y sugerir
  un SLA externo con colchon de seguridad, exactamente la logica que
  describe la seccion de SLA del post.

No incluye el contexto historico ni la comparativa de herramientas
comerciales (Datadog, Nobl9, Sloth) del post: son contenido narrativo, no
algo que tenga sentido simular en un mini-ejemplo.

## Requisitos

- Docker y Docker Compose
- `curl` (para `load_test.sh`)
- Python 3.9 o superior (solo libreria estandar, para `sli_slo_report.py`)

## Como correrlo

### 1. Levantar el servicio demo y Prometheus

```bash
cd slis-slos-slas
docker compose up -d
```

Verificar que ambos contenedores esten arriba:

```bash
docker compose ps
```

### 2. Generar trafico normal durante 60 segundos

```bash
./load_test.sh
```

Salida esperada (el numero exacto de solicitudes varia):

```
Generando trafico durante 60s contra http://localhost:8080/work ...
Listo. 1180 solicitudes enviadas.
```

### 3. Calcular el SLI y compararlo contra el SLO

Esperá unos segundos a que Prometheus haga scrape (`scrape_interval: 5s`) y
corré el reporte:

```bash
python3 sli_slo_report.py --window 5m
```

Salida esperada en trafico normal (SLI de disponibilidad por encima del
99.9% del SLO, ambos SLO cumplidos):

```
============================================================
REPORTE SLI / SLO / SLA
============================================================
Ventana evaluada:            5m
Solicitudes totales:         1180
Errores 5xx:                 4
SLI disponibilidad:          99.661%
SLI latencia p95:            187 ms
------------------------------------------------------------
SLO disponibilidad objetivo: 99.900%
SLO latencia p95 objetivo:   200 ms
Cumple SLO disponibilidad:   NO
Cumple SLO latencia:         SI
------------------------------------------------------------
SLA externo sugerido:        99.500% (colchon de 0.40pp bajo el SLO)
============================================================
```

(La tasa de error 5xx sintetica del ejemplo, 0.3%, es a proposito mas alta
que un SLO real de 99.9% para que el reporte muestre el caso "SLO
incumplido" sin tener que esperar horas de trafico limpio; ajustá
`error_rate_5xx` en `app.py` o el flag `--slo-availability` para ver el
caso "cumplido".)

El exit code es `0` si ambos SLO se cumplen y `1` si alguno falla (pensado
para un step de CI/CD tipo `slo_check`).

### 4. Ver el SLI caer con un incidente simulado

```bash
./load_test.sh --degrade
python3 sli_slo_report.py --window 5m
```

`load_test.sh --degrade` activa `/admin/degrade?on=1` antes de generar
trafico (sube el 5xx a 25%) y lo desactiva al terminar. El reporte
deberia mostrar la disponibilidad muy por debajo del SLO y `Cumple SLO
disponibilidad: NO`.

### 5. Apagar todo

```bash
docker compose down
```

## Opciones de `sli_slo_report.py`

```bash
python3 sli_slo_report.py --help
```

- `--prometheus-url`: default `http://localhost:9090`
- `--window`: ventana de evaluacion PromQL, default `5m`
- `--slo-availability`: SLO de disponibilidad como fraccion, default `0.999`
- `--slo-latency-p95`: SLO de latencia p95 en segundos, default `0.2`
- `--sla-margin`: colchon del SLA externo respecto al SLO, default `0.004`

## Notas

- No hay credenciales ni cuentas externas: todo corre local con Docker.
- El servicio demo genera trafico sintetico con `random`, no hay seed fija,
  asi que los numeros exactos van a variar levemente entre corridas.
- Para inspeccionar las metricas crudas: `curl http://localhost:9100/metrics`
  o la UI de Prometheus en `http://localhost:9090`.
