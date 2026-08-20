# Arquitectura de métricas para blockchain

Ejemplo ejecutable del post [Guía Completa de Arquitectura de métricas para blockchain](https://www.devopsfreelance.pro/blog/posts/arquitectura-metricas-blockchain/).

## Qué demuestra

El post describe un pipeline de métricas de tres capas (recolección → almacenamiento a largo plazo → KPIs de negocio). Este ejemplo levanta esas tres capas con componentes reales, apuntando a un **exporter simulado** que expone las mismas métricas de un nodo Ethereum que usa el post (`chain_transactions_total`, `beacon_head_slot`, `beacon_finalized_epoch`, `validator_attestation_hit_percentage`, `node_filesystem_*`), sin necesidad de sincronizar un nodo real:

- **Recolección**: Prometheus scrapea el exporter simulado (`prometheus/prometheus.yml`), igual que scrapearía un nodo `geth`/`lighthouse` real.
- **Almacenamiento a largo plazo**: Prometheus reenvía cada muestra a VictoriaMetrics vía `remote_write`, tal como plantea el post como alternativa a Thanos para retención extendida.
- **KPIs de negocio**: `prometheus/recording_rules.yml` pre-calcula exactamente los cuatro KPIs del post: TPS, finality time (gap de epochs), attestation effectiveness y uso de disco por nodo.

No incluye Grafana ni Thanos (el foco es el pipeline recolección → storage remoto → KPIs, no el dashboarding); las queries se corren directo contra la API de Prometheus/VictoriaMetrics.

## Requisitos

- Docker y Docker Compose (`docker compose version`).
- Puertos libres en el host: `8000` (mock-exporter), `9090` (Prometheus), `8428` (VictoriaMetrics).

## Pasos para correrlo

```bash
cd arquitectura-metricas-blockchain

# 1. Levantar el stack completo
docker compose up -d --build

# 2. Ver las metricas simuladas que expone el "nodo"
curl -s http://localhost:8000/metrics

# 3. Confirmar que Prometheus scrapea el exporter como "up"
curl -s http://localhost:9090/api/v1/targets | grep -o '"health":"[a-z]*"'

# 4. Esperar ~1 minuto para que corran las recording rules y consultar el TPS
curl -s 'http://localhost:9090/api/v1/query?query=blockchain:tps:rate5m' | python3 -m json.tool

# 5. Consultar el finality gap y la attestation effectiveness
curl -s 'http://localhost:9090/api/v1/query?query=blockchain:finality_gap:epochs' | python3 -m json.tool
curl -s 'http://localhost:9090/api/v1/query?query=blockchain:attestation_effectiveness:avg' | python3 -m json.tool

# 6. Confirmar que las mismas series llegaron a VictoriaMetrics via remote_write
curl -s 'http://localhost:8428/api/v1/query?query=chain_transactions_total' | python3 -m json.tool
```

Salida esperada del paso 2 (los valores concretos varían, es una simulación con datos aleatorios):

```
chain_transactions_total{node_id="node-01",region="us-east-1",client="geth"} 1500014
beacon_head_slot{node_id="node-01",region="us-east-1",client="geth"} 9600033
beacon_finalized_epoch{node_id="node-01",region="us-east-1",client="geth"} 300000
validator_attestation_hit_percentage{node_id="node-01",region="us-east-1",client="geth"} 97.42
validator_attestation_inclusion_distance{node_id="node-01",region="us-east-1",client="geth"} 1.34
node_filesystem_size_bytes{node_id="node-01",region="us-east-1",client="geth",mountpoint="/data"} 2000000000000
node_filesystem_avail_bytes{node_id="node-01",region="us-east-1",client="geth",mountpoint="/data"} 499999999...
p2p_peers{node_id="node-01",region="us-east-1",client="geth"} 31
```

Salida esperada del paso 4 (`status: "success"` con un vector que trae `blockchain:tps:rate5m` y un valor entre ~10 y ~20):

```json
{
    "status": "success",
    "data": {
        "resultType": "vector",
        "result": [
            {
                "metric": {"__name__": "blockchain:tps:rate5m"},
                "value": [1755600000, "15.333333"]
            }
        ]
    }
}
```

## Apagar el stack

```bash
docker compose down
```

## Nota sobre credenciales

Ninguno de los componentes usa credenciales: es un stack 100% local sin cuentas externas (a diferencia del `telegraf.conf` del post, que sí requeriría un `INFLUX_TOKEN` real contra un InfluxDB gestionado).
