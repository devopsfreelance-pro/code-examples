# Monitoreo de un nodo Ethereum Layer 2 con Prometheus

Post: [Guía Definitiva de Infraestructura para Ethereum Layer 2](https://www.devopsfreelance.pro/blog/posts/infraestructura-ethereum-layer-2/)

## Qué demuestra este ejemplo

El post explica que operar nodos L2 (OP Stack, Arbitrum, Base) requiere
monitorear métricas que no existen en L1, como el lag de sincronización
entre el `unsafe head` y el `safe head`, el retraso en la publicación de
batches en L1, y la cantidad de peers conectados. También incluye las
reglas de alerting de Prometheus para esas métricas.

Levantar un nodo real de Optimism o Arbitrum requiere cientos de GB de
disco y acceso a un nodo L1 completo, así que no es viable en una
máquina de lector en minutos. En su lugar, este ejemplo levanta:

- **`l2-exporter`**: un exportador Prometheus en Python que simula las
  métricas de un nodo L2 (`l2_unsafe_head`, `l2_safe_head`,
  `l2_last_batch_submission_timestamp`, `l2_p2p_peer_count`), con un
  `safe_head` deliberadamente más lento que el `unsafe_head` para que el
  lag crezca con el tiempo.
- **`prometheus`**: scrapea el exportador y evalúa las mismas reglas de
  alerting (`L2SyncLag`, `L2BatchSubmissionDelay`, `L2PeerCount`) que
  aparecen en el post, en `alerts.yml`.

Así se puede ver en minutos, sobre datos simulados pero con las mismas
reglas del post, cómo se dispara una alerta de lag de sincronización L2
en Prometheus.

Nota: los `for:` de las reglas se acortaron a `1m` (el post usa `10m` y
`5m`) para que las alertas pasen a estado `firing` en minutos en vez de
horas. La lógica de los `expr` es idéntica a la del post.

## Requisitos

- Docker y Docker Compose (`docker compose version`)
- Puertos libres en el host: `9090` (Prometheus) y `9101` (exportador)

## Pasos para correrlo

```bash
cd infraestructura-ethereum-layer-2

# 1. Levantar el exportador simulado y Prometheus
docker compose up -d --build

# 2. Ver las métricas simuladas del nodo L2
curl -s http://localhost:9101/metrics

# 3. Confirmar que Prometheus scrapea el target correctamente
curl -s http://localhost:9090/api/v1/targets | grep -o '"health":"[a-z]*"'

# 4. Ver el lag de sincronizacion L2 (unsafe_head - safe_head) via Prometheus
curl -s 'http://localhost:9090/api/v1/query?query=l2_unsafe_head-l2_safe_head'

# 5. Esperar ~1-2 minutos y ver el estado de las alertas
curl -s http://localhost:9090/api/v1/alerts | python3 -m json.tool
```

También se puede abrir `http://localhost:9090/alerts` en el navegador
para ver el estado (`inactive` -> `pending` -> `firing`) de las tres
reglas: `L2SyncLag`, `L2BatchSubmissionDelay` y `L2PeerCount`.

Para bajar todo:

```bash
docker compose down
```

## Salida esperada

Al consultar `/metrics` del exportador (paso 2) se ve algo como:

```
l2_unsafe_head 1000042
l2_safe_head 1000038
l2_last_batch_submission_timestamp 1755640000
l2_p2p_peer_count 2
```

El target en Prometheus (paso 3) debe reportar `"health":"up"`.

Pasados 1-2 minutos, el paso 5 debe mostrar las tres alertas en estado
`"state": "firing"`, por ejemplo:

```json
{
  "status": "success",
  "data": {
    "alerts": [
      {
        "labels": {"alertname": "L2SyncLag", "severity": "warning"},
        "annotations": {"summary": "Nodo L2 con lag de sincronizacion"},
        "state": "firing",
        ...
      },
      {
        "labels": {"alertname": "L2PeerCount", "severity": "warning"},
        "annotations": {"summary": "Pocos peers conectados en nodo L2"},
        "state": "firing",
        ...
      }
    ]
  }
}
```

`L2BatchSubmissionDelay` recién pasa a `firing` cuando el contenedor
lleva más de una hora corriendo (`time() - l2_last_batch_submission_timestamp > 3600`),
ya que el timestamp del último batch se fija al arrancar el exportador.
Las otras dos (`L2SyncLag`, `L2PeerCount`) disparan en el primer minuto.
