# SLI SLO SLA en la practica: burn rate del error budget con alerta real

Ejemplo de codigo que acompaña al post [Guía Completa de Slis, slos y slas en la práctica](https://www.devopsfreelance.pro/blog/posts/slis-slos-slas-practica/).

## Que demuestra

El post muestra dos fragmentos de codigo centrales: la instrumentacion de
una funcion con `prometheus_client.Histogram` para medir latencia (SLI), y
una regla de alerta de Prometheus que dispara sobre el **burn rate** del
error budget (`sum(rate(5xx)) / sum(rate(total)) > 0.001`) en vez de sobre
errores individuales. Este ejemplo levanta esa cadena completa y
ejecutable, hasta ver la alerta pasar a estado `firing`:

- `app.py`: servicio HTTP con un endpoint `/api/search`, instrumentado con
  las mismas metricas del post (`http_request_duration_seconds` como
  histograma, `http_requests_total` como contador por status). Expone un
  endpoint `/admin/error-rate` para subir la tasa de errores 5xx en
  caliente y simular un incidente, sin reiniciar el contenedor.
- `slo_alerts.yml`: la regla de burn rate literal del post (misma
  expresion PromQL), cargada por Prometheus.
- Prometheus (`prometheus.yml`) scrapeando el servicio y evaluando la
  regla, reenviando alertas a Alertmanager.
- Alertmanager (`alertmanager.yml`), configuracion minima para ver la
  alerta agrupada y en estado activo (sin receptor externo: no envia a
  Slack ni email, el objetivo es observar el ciclo de vida de la alerta).
- `load_test.sh`: genera trafico normal o, con `--incident`, sube la tasa
  de error por encima del umbral del SLO para forzar el burn rate alto que
  describe el post.

No incluye el contexto historico de SLAs, la comparativa AWS/Azure/GCP ni
la logica de creditos de servicio del post: son contenido contractual y
narrativo, no algo que tenga sentido simular en un mini-ejemplo.

## Requisitos

- Docker y Docker Compose
- `curl` (usado por `load_test.sh`)

## Como correrlo

### 1. Levantar el stack

```bash
cd slis-slos-slas-practica
docker compose up -d
```

Verificar que los tres contenedores esten arriba:

```bash
docker compose ps
```

### 2. Generar trafico normal (dentro del SLO)

```bash
chmod +x load_test.sh
./load_test.sh
```

Salida esperada:

```
Trafico normal: tasa de error 5xx en 0.05% (dentro del SLO).
Generando trafico durante 60s contra http://localhost:8080/api/search ...
Listo. 1180 solicitudes enviadas.
```

Confirmar que no hay alertas activas:

```bash
curl -s http://localhost:9090/api/v1/alerts | grep -o '"state":"[a-z]*"' || echo "sin alertas"
```

Deberia mostrar `sin alertas` o un estado distinto de `firing`.

### 3. Simular un incidente y ver el burn rate disparar la alerta

```bash
./load_test.sh --incident
```

Esto sube la tasa de error 5xx a 15% (muy por encima del umbral de 0.1%
del SLO), genera trafico durante 60 segundos y despues restaura la tasa
normal. La regla usa `for: 15s` (el post usa `for: 5m` en produccion; acá
se acorta solo para que la demo dispare rapido en una corrida local).

Revisar el estado de la alerta en Prometheus:

```bash
curl -s http://localhost:9090/api/v1/alerts | python3 -m json.tool
```

Salida esperada, con la alerta en `firing`:

```json
{
    "status": "success",
    "data": {
        "alerts": [
            {
                "labels": {
                    "alertname": "ErrorBudgetBurnRateHigh",
                    "severity": "warning"
                },
                "annotations": {
                    "summary": "Consumo elevado del error budget en ...",
                    "description": "La tasa de errores 5xx supera el umbral del SLO (0.1%) durante los ultimos 5 minutos. ..."
                },
                "state": "firing"
            }
        ]
    }
}
```

Tambien podés verla en la UI:

- Prometheus: `http://localhost:9090/alerts`
- Alertmanager: `http://localhost:9093/#/alerts`

Si `load_test.sh --incident` ya termino y restauro la tasa normal, la
alerta pasa de `firing` a `resolved` a los pocos minutos (el burn rate
vuelve a bajar de 0.1% a medida que la ventana de 5m del `rate()` deja
atras las muestras del incidente).

### 4. Apagar todo

```bash
docker compose down
```

## Notas

- No hay credenciales ni cuentas externas: todo corre local con Docker.
- `for: 15s` en `slo_alerts.yml` es un ajuste deliberado para la demo. En
  produccion usa `for: 5m` o mas, como recomienda el post, para no
  disparar por picos de segundos.
- Para inspeccionar las metricas crudas: `curl http://localhost:9100/metrics`.
- Para volver a probar desde cero: `docker compose restart prometheus alertmanager`
  limpia el estado de las alertas evaluadas.
