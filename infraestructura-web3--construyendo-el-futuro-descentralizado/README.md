# Monitoreo de un nodo Ethereum local con Prometheus

Ejemplo de código para el post [Infraestructura Web3: Construyendo el Futuro Descentralizado](https://www.devopsfreelance.pro/blog/posts/infraestructura-web3--construyendo-el-futuro-descentralizado/).

## Qué demuestra

El post describe un stack de monitoreo para nodos blockchain (Geth + Prysm + Prometheus + Grafana). Levantar ese stack completo requiere sincronizar un nodo real de Ethereum mainnet, lo cual tarda horas o días y no es viable como ejemplo ejecutable.

Este ejemplo reproduce el mismo patrón de infraestructura a escala mínima y 100% local:

1. Un nodo Ethereum de desarrollo (**Anvil**, parte de Foundry) que arranca instantáneamente y produce bloques cada 5 segundos, sin sincronizar nada externo.
2. Un **exporter en Python** que consulta el nodo por JSON-RPC (`eth_blockNumber`, `eth_chainId`, `net_peerCount`) y expone esas métricas en formato Prometheus, igual que hace `geth` con su flag `--metrics`.
3. **Prometheus** scrapeando el exporter, tal como en la sección "Stack de Monitoreo Completo" del post.

Con esto podés ver en minutos el ciclo completo: nodo → métricas → scraping, sin necesidad de un nodo Ethereum real ni de ETH.

## Requisitos

- Docker y Docker Compose (plugin `docker compose`, no el binario viejo `docker-compose`).
- Sin cuentas ni servicios pagos. No se necesita ETH, RPC provider externo (Infura/Alchemy) ni claves privadas.

## Pasos para correrlo

```bash
cd infraestructura-web3--construyendo-el-futuro-descentralizado

# 1. Levantar el stack (anvil + exporter + prometheus)
docker compose up -d --build

# 2. Verificar que el nodo Anvil responde
curl -s -X POST http://localhost:8545 \
  -H "Content-Type: application/json" \
  -d '{"jsonrpc":"2.0","id":1,"method":"eth_blockNumber","params":[]}'

# 3. Ver las métricas crudas que expone el exporter
curl -s http://localhost:9100 | grep web3_

# 4. Consultar la métrica vía Prometheus (API HTTP)
curl -s 'http://localhost:9090/api/v1/query?query=web3_block_number' | python3 -m json.tool
```

También podés abrir `http://localhost:9090` en el navegador y buscar `web3_block_number`, `web3_chain_id` o `web3_rpc_up` en el explorador de Prometheus.

Para bajar el stack:

```bash
docker compose down
```

## Salida esperada

Paso 2 (respuesta del nodo, el número de bloque en hexadecimal, va incrementando cada 5s):

```json
{"jsonrpc":"2.0","id":1,"result":"0x3"}
```

Paso 3 (métricas Prometheus servidas por el exporter):

```
web3_block_number 3.0
web3_chain_id 31337.0
web3_peer_count 0.0
web3_rpc_up 1.0
```

Paso 4 (Prometheus ya scrapeó el exporter y responde con el valor actual):

```json
{
    "status": "success",
    "data": {
        "resultType": "vector",
        "result": [
            {
                "metric": {"__name__": "web3_block_number", "instance": "exporter:9100", "job": "web3-exporter"},
                "value": [1700000000, "3"]
            }
        ]
    }
}
```

`web3_chain_id` en `31337` es el chain ID por defecto de Anvil (red de desarrollo local). `web3_rpc_up` en `1` indica que el exporter pudo hablar con el nodo.

## Archivos

- `docker-compose.yml` — orquesta el nodo Anvil, el exporter y Prometheus.
- `exporter/exporter.py` — consulta el nodo por JSON-RPC y expone métricas Prometheus en `:9100`.
- `exporter/Dockerfile` — imagen del exporter.
- `exporter/requirements.txt` — dependencias Python del exporter.
- `prometheus/prometheus.yml` — configuración de scraping de Prometheus.
