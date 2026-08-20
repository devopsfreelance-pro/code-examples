# Escalabilidad de nodos blockchain: balanceo de carga horizontal

Post del blog: https://www.devopsfreelance.pro/blog/posts/escalabilidad-nodos-blockchain/

## Qué demuestra este ejemplo

El post explica que la escalabilidad horizontal de nodos blockchain se logra
distribuyendo las solicitudes de lectura (JSON-RPC) entre un pool de nodos de
consulta detrás de un balanceador de carga, tal como muestra el bloque de
configuración NGINX del artículo (`upstream blockchain_nodes { least_conn; ... }`).

Este ejemplo levanta:

- **3 nodos mock** (`node1`, `node2`, `node3`): contenedores Python/Flask que
  simulan un nodo Ethereum respondiendo `eth_blockNumber` y `net_peerCount`
  vía JSON-RPC 2.0, cada uno con su propio `NODE_ID` y avanzando de altura de
  bloque de forma independiente (como nodos reales sincronizados a la misma red).
- **1 NGINX** como balanceador de carga (`least_conn`, `max_fails`,
  `fail_timeout`, `limit_req`), usando exactamente la misma configuración
  del post.
- **Un script (`test_balanceo.sh`)** que dispara N requests contra el
  balanceador y cuenta cuántas atendió cada nodo, para comprobar que la
  carga efectivamente se reparte (escalabilidad horizontal) y no recae
  siempre en un único nodo.

No se levanta un nodo Ethereum real (sincronizar uno tarda horas/días y
requiere cientos de GB de disco); el mock reproduce el comportamiento
relevante para el concepto de infraestructura (balanceo, failover) sin esa
dependencia.

## Requisitos

- Docker y Docker Compose (`docker compose version` >= v2)
- `curl` y `bash` (para el script de prueba)
- Puerto `8080` libre en localhost

No requiere cuentas, API keys ni servicios pagos.

## Pasos para correrlo

1. Levantar el stack (nodos + balanceador):

```bash
cd escalabilidad-nodos-blockchain
docker compose up --build -d
```

2. Esperar ~10 segundos a que los healthchecks pasen y hacer una consulta manual:

```bash
curl -s -X POST http://localhost:8080/rpc \
  -H "Content-Type: application/json" \
  -d '{"jsonrpc":"2.0","method":"eth_blockNumber","params":[],"id":1}'
```

Salida esperada (el `_served_by` puede variar entre node1/node2/node3):

```json
{"_requests_served_by_this_node":1,"_served_by":"node1","id":1,"jsonrpc":"2.0","result":"0x112a880"}
```

3. Verificar la distribución de carga entre los 3 nodos:

```bash
chmod +x test_balanceo.sh
./test_balanceo.sh 30
```

Salida esperada (los números exactos varían, pero ningún nodo debería
quedarse en 0 con `least_conn` y 30 requests):

```
Enviando 30 requests eth_blockNumber a http://localhost:8080/rpc ...

Distribución de requests por nodo:
  node1: 10
  node2: 10
  node3: 10
```

4. Simular la caída de un nodo y comprobar el failover automático
   (`max_fails=3 fail_timeout=30s` en `nginx.conf`):

```bash
docker compose stop node2
./test_balanceo.sh 15
# node2 no debería aparecer en la distribución: NGINX lo saca del pool
docker compose start node2
```

5. Apagar todo:

```bash
docker compose down
```

## Estructura

```
escalabilidad-nodos-blockchain/
├── docker-compose.yml       # 3 nodos mock + NGINX
├── mock-node/
│   ├── app.py                # Nodo blockchain mock (Flask, JSON-RPC)
│   ├── requirements.txt
│   └── Dockerfile
├── nginx/
│   └── nginx.conf            # Balanceo least_conn, igual que en el post
└── test_balanceo.sh          # Verifica distribución de carga y failover
```
