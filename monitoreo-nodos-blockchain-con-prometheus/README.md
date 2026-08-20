# Monitoreo de nodos blockchain con Prometheus

Ejemplo ejecutable del post [Guía Completa de Monitoreo de nodos blockchain con Prometheus](https://www.devopsfreelance.pro/blog/posts/monitoreo-nodos-blockchain-con-prometheus/).

## Qué demuestra

Levanta el stack de observabilidad completo descrito en el post (Prometheus + Alertmanager + node_exporter) apuntando a un **exporter simulado** que expone las mismas métricas que un cliente Ethereum real (`ethereum_blockchain_height`, `chain_head_block`, `p2p_peers`, `txpool_pending`, `beacon_head_slot`, `beacon_finalized_epoch`), sin necesidad de sincronizar un nodo real.

Con esto se puede ver funcionando de punta a punta:

- El scrape de métricas estilo Prometheus (`prometheus/prometheus.yml`).
- Las reglas de alerta del post (`prometheus/alerts/blockchain.yml`): `NodeOutOfSync`, `LowPeerCount`, `DiskSpaceLow`, `MempoolOverflow`.
- El ruteo de alertas críticas vs. warning en Alertmanager (`alertmanager/alertmanager.yml`).
- Cómo forzar cada escenario de alerta con variables de entorno del exporter simulado.

No incluye Grafana ni un cliente Ethereum real (serían gigabytes de sincronización); el foco es la mecánica de scrape + reglas + alerting.

## Requisitos

- Docker y Docker Compose (`docker compose version`).
- Puertos libres en el host: `9090` (Prometheus), `9093` (Alertmanager), `9100` (node_exporter), `8000` (mock-exporter).

## Pasos para correrlo

```bash
cd monitoreo-nodos-blockchain-con-prometheus

# 1. Levantar el stack
docker compose up -d

# 2. Ver las metricas simuladas del "nodo"
curl -s http://localhost:8000/metrics

# 3. Verificar que Prometheus scrapea ambos targets como "UP"
curl -s http://localhost:9090/api/v1/targets | grep -o '"health":"[a-z]*"'

# 4. Abrir la UI de Prometheus y correr una query
#    http://localhost:9090/graph?g0.expr=p2p_peers
```

Salida esperada del paso 2 (los valores concretos varían, es una simulación):

```
ethereum_blockchain_height 21004213
chain_head_block 21004212
p2p_peers 27
txpool_pending 312
beacon_head_slot 12345
beacon_finalized_epoch 383
```

### Forzar una alerta

Editá `docker-compose.yml`, descomentá una de las variables de entorno del servicio `mock-exporter` (por ejemplo `SIMULATE_LOW_PEERS: "1"`), y reiniciá:

```bash
docker compose up -d mock-exporter
```

Después de ~1 minuto (el `for:` de la regla), la alerta pasa a estado `firing`:

```bash
curl -s http://localhost:9090/api/v1/alerts | grep -o '"alertname":"[A-Za-z]*"'
```

O visualmente en `http://localhost:9093` (Alertmanager) y `http://localhost:9090/alerts` (Prometheus).

Escenarios disponibles:

| Variable | Alerta que dispara |
|---|---|
| `SIMULATE_OUT_OF_SYNC=1` | `NodeOutOfSync` |
| `SIMULATE_LOW_PEERS=1` | `LowPeerCount` |
| `SIMULATE_MEMPOOL_FULL=1` | `MempoolOverflow` |

`DiskSpaceLow` usa las métricas reales de `node_exporter` sobre el filesystem del host, así que solo dispara si el disco del host donde corrés Docker realmente está por debajo del 10% libre.

### Apagar el stack

```bash
docker compose down
```

## Notas sobre el receiver de Alertmanager

`alertmanager/alertmanager.yml` define los receivers `devops-team` y `devops-critical` **sin integraciones** (sin `slack_configs` ni `pagerduty_configs`), a diferencia del post donde se ilustran con webhooks de Slack/PagerDuty. Es intencional: así el ejemplo corre sin depender de credenciales externas. Las alertas se ven igual en la UI de Alertmanager. Para conectarlo a Slack real, agregar `slack_configs` con la URL del webhook como se muestra en el post, y guardarla en un secret manager (nunca en el repo).
