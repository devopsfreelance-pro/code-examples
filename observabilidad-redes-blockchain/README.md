# Observabilidad en redes blockchain

Ejemplo ejecutable para el post [Observabilidad en redes blockchain](https://www.devopsfreelance.pro/blog/posts/observabilidad-redes-blockchain/).

## Qué demuestra

El post explica que la observabilidad de una red blockchain requiere mirar el
comportamiento de **varios nodos a la vez** (no solo un servicio aislado) y
detectar anomalías como divergencia de altura de bloque, nodos con pocos
peers o latencia alta de propagación de bloques.

Este ejemplo levanta una red simulada de 3 nodos, cada uno exponiendo
métricas Prometheus (`block_height`, `peer_count`, `mempool_size`,
`block_propagation_seconds`). El nodo `node3` se simula con problemas de
sincronización a propósito, para poder ver en Prometheus cómo se dispara la
alerta `BlockHeightDivergence` cuando un nodo se atrasa respecto al resto de
la red, exactamente el caso de uso que describe el post.

Componentes:

- `node_metrics_exporter.py`: exportador Prometheus que simula un nodo de
  blockchain (uno por contenedor, parametrizado por variables de entorno).
- `prometheus.yml`: scrapea los 3 nodos y carga las reglas de alerta.
- `alert_rules.yml`: reglas de alerta (`BlockHeightDivergence`,
  `NodeLowPeerCount`, `HighBlockPropagationLatency`).
- `docker-compose.yml`: orquesta los 3 nodos + Prometheus + Grafana.

## Requisitos

- Docker y Docker Compose (`docker compose version`).
- Puertos libres en el host: 8001, 8002, 8003, 9090, 3000.

## Cómo correrlo

```bash
cd observabilidad-redes-blockchain
docker compose up --build
```

Esperar unos 20-30 segundos a que los nodos generen algunos bloques.

### 1. Ver las métricas crudas de un nodo

```bash
curl -s http://localhost:8003/metrics | grep blockchain_node
```

Salida esperada (valores exactos varían, `node3` tendrá `peer_count` bajo y
`block_propagation_seconds` alto por estar simulado como "lagging"):

```
blockchain_node_block_height{node_id="node-3"} 1004.0
blockchain_node_peer_count{node_id="node-3"} 3.0
blockchain_node_mempool_size{node_id="node-3"} 210.0
blockchain_node_block_propagation_seconds{node_id="node-3"} 5.87
```

### 2. Ver la alerta disparada en Prometheus

Abrir http://localhost:9090/alerts en el navegador. Después de ~1-2 minutos
de ejecución, `BlockHeightDivergence` y `NodeLowPeerCount` deberían aparecer
en estado `firing` (color rojo), porque `node3` se va atrasando respecto a
`node1` y `node2`.

También se puede consultar directamente la diferencia de altura entre nodos
en http://localhost:9090/graph con la query:

```
max(blockchain_node_block_height) - min(blockchain_node_block_height)
```

### 3. Ver un dashboard en Grafana (opcional)

1. Abrir http://localhost:3000 (usuario `admin`, contraseña `admin`, o
   entrar como anónimo, ya habilitado en el compose).
2. Agregar un datasource Prometheus apuntando a `http://prometheus:9090`
   (Configuration > Data sources > Add data source > Prometheus).
3. Crear un panel con la query `blockchain_node_block_height` agrupado por
   `node_id` para ver visualmente cómo `node-3` se atrasa respecto a los
   otros dos.

### 4. Apagar todo

```bash
docker compose down
```

## Notas

- Los exportadores no se conectan a una blockchain real: generan métricas
  simuladas para poder correr el ejemplo sin sincronizar un nodo completo.
  El objetivo es ilustrar la arquitectura de observabilidad (scrape
  multi-nodo + reglas de alerta), no simular consenso real.
- No requiere credenciales ni cuentas de terceros.
