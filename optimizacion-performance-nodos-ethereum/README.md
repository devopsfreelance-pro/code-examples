# Optimización de performance en nodos Ethereum

Post: https://www.devopsfreelance.pro/blog/posts/optimizacion-performance-nodos-ethereum/

## Qué demuestra este ejemplo

El post describe cómo configurar un cliente de ejecución Ethereum (Geth) con
parámetros orientados a performance (`--cache`, `--maxpeers`, `--syncmode`,
`--db.engine`) y cómo exponer y scrapear sus métricas con Prometheus para
monitorear altura de bloque, peers conectados y uso de recursos.

Sincronizar un nodo Ethereum real contra mainnet toma horas y cientos de GB,
así que este ejemplo no lo hace. En cambio, levanta Geth en modo `--dev`
(nodo local instantáneo, sin red P2P real) con las mismas flags de
producción que menciona el post, y arma el mismo pipeline de observabilidad:

- `docker-compose.yml`: levanta Geth con `--cache`, `--maxpeers`, `--db.engine=pebble`
  y métricas Prometheus habilitadas, más un Prometheus que las scrapea.
- `prometheus.yml`: la misma configuración de scraping (`/debug/metrics/prometheus`)
  que aparece en el post.
- `check_node_health.sh`: consulta por RPC la altura de bloque y los peers
  conectados, y verifica que el endpoint de métricas responda; son las
  métricas clave que el post recomienda monitorear.

No cubre benchmarking real de I/O de disco, red ni multi-cliente (Erigon,
Nethermind): eso requiere hardware e infraestructura de producción, fuera
del alcance de un ejemplo ejecutable en minutos.

## Requisitos

- Docker y Docker Compose (plugin `docker compose`)
- `curl` (para el script de chequeo)

No hace falta cuenta ni credenciales de ningún servicio externo.

## Pasos para correrlo

1. Levantar Geth (modo dev) y Prometheus:

```bash
docker compose up -d
```

2. Esperar unos segundos a que el healthcheck de Geth pase, y correr el
   chequeo de salud:

```bash
./check_node_health.sh
```

Salida esperada (aproximada, los valores exactos varían):

```
== Chequeo de salud del nodo Ethereum ==
RPC: http://localhost:8545

-- Altura de bloque --
Bloque actual: 0

-- Peers conectados --
Peers: 0
(En modo --dev el nodo es standalone, 0 peers es esperado)

-- Metricas Prometheus disponibles --
OK: http://localhost:6060/debug/metrics/prometheus responde
Muestra de metricas relevantes:
chain_head_block 0
p2p_peers 0
eth_db_chaindata_disk_size ...
```

3. (Opcional) Abrir Prometheus en el navegador y consultar las métricas
   scrapeadas:

```
http://localhost:9090
```

Buscar por ejemplo `chain_head_block` o `p2p_peers` en el campo de query.

4. Frenar todo:

```bash
docker compose down
```

## Llevar esto a producción

- Cambiar `--dev` por `--syncmode snap` contra la red real (mainnet o una
  testnet) y ajustar `--cache` según la RAM disponible, como se explica en
  el post.
- Nunca exponer los puertos 8545 (RPC) ni 8546 (WebSocket) directamente a
  Internet; el `docker-compose.yml` de este ejemplo los publica solo para
  pruebas locales.
- Sumar el job de Prometheus de `prometheus.yml` al stack de observabilidad
  real (Grafana, Alertmanager) en vez de correr Prometheus standalone.
