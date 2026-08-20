# Edge Computing: nodo edge con Prometheus + federacion

Post relacionado: [Guía Completa de Edge computing](https://www.devopsfreelance.pro/blog/posts/edge-computing/)

## Qué demuestra este ejemplo

El post explica que en edge computing conviene procesar los datos donde se
generan y enviar a la nube central solo información agregada, en lugar de
transmitir todo el flujo crudo. Este ejemplo monta esa arquitectura en
miniatura con Docker:

- **`sensor-exporter`**: simula un nodo edge (gateway de una línea de
  producción) que lee sensores de vibración/temperatura, ejecuta
  **detección de anomalías localmente** (umbral simple) y expone las
  métricas resultantes en formato Prometheus.
- **`prometheus-edge`**: Prometheus corriendo en el propio nodo edge,
  scrapea el exporter local cada 5s.
- **`prometheus-central`**: Prometheus "central" que **no** scrapea
  sensores directamente; en cambio hace `federate` contra el Prometheus
  edge y trae solo las métricas ya agregadas, tal como describe la sección
  de "Patrones de Comunicación y Sincronización" y "Monitoreo y
  Observabilidad" del post.

Esto reproduce en pequeño el patrón de federación Prometheus que aparece
en el post (`prometheus-central.yml` es una versión mínima del bloque
`federate-to-central` del artículo).

## Requisitos

- Docker y Docker Compose (plugin `docker compose`, v2+)
- Puertos libres en el host: `9090`, `9091`, `9100`

## Cómo correrlo

```bash
cd edge-computing
docker compose up -d --build
```

Esperar unos segundos a que el exporter genere las primeras lecturas y
verificar cada pieza:

```bash
# 1. Métricas crudas del nodo edge (sensor + anomalías detectadas localmente)
curl -s localhost:9100/metrics | grep edge_

# 2. Prometheus edge: el target del exporter debe estar "up"
curl -s localhost:9090/api/v1/targets | python3 -c \
  "import json,sys; d=json.load(sys.stdin); print([(t['labels']['job'], t['health']) for t in d['data']['activeTargets']])"

# 3. Prometheus central: el target de federación debe estar "up"
curl -s localhost:9091/api/v1/targets | python3 -c \
  "import json,sys; d=json.load(sys.stdin); print([(t['labels']['job'], t['health']) for t in d['data']['activeTargets']])"

# 4. Las métricas del sensor deben verse en el Prometheus CENTRAL,
#    sin que este haya scrapeado el sensor directamente
curl -s 'localhost:9091/api/v1/query?query=edge_sensor_vibration_mm_s' | python3 -m json.tool
```

También se puede navegar la UI de Prometheus en el navegador:

- Edge: http://localhost:9090
- Central: http://localhost:9091

Para ver las anomalías detectadas y resueltas localmente:

```bash
curl -s 'localhost:9091/api/v1/query?query=edge_anomalies_detected_total' | python3 -m json.tool
docker compose logs -f sensor-exporter   # imprime "anomalia detectada localmente" cuando ocurre
```

Apagar todo:

```bash
docker compose down
```

## Salida esperada

En el paso 1, algo como:

```
edge_sensor_vibration_mm_s{machine_id="line-01"} 2.23
edge_sensor_vibration_mm_s{machine_id="line-02"} 1.86
edge_sensor_temperature_celsius{machine_id="line-01"} 43.55
edge_anomalies_detected_total{machine_id="line-01"} 0.0
edge_readings_processed_total{machine_id="line-01"} 12.0
```

En los pasos 2 y 3, el job correspondiente debe reportar `'up'`:

```
[('edge-sensors', 'up')]
[('federate-edge', 'up')]
```

En el paso 4, el Prometheus central debe devolver resultados con
`__name__: edge_sensor_vibration_mm_s` y las labels `region`/`cluster`
heredadas del Prometheus edge (gracias a `honor_labels: true`), aunque
nunca haya scrapeado el exporter directamente. Esto confirma que la
"nube central" solo recibe datos agregados del nodo edge, no el flujo
crudo de sensores.

Después de un par de minutos, `edge_anomalies_detected_total` debería
incrementar ocasionalmente (probabilidad de anomalía simulada del 8% por
lectura), visible tanto en el edge como, federado, en el central.
