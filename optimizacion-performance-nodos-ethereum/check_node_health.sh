#!/usr/bin/env bash
#
# check_node_health.sh
#
# Consulta las metricas clave de un nodo Ethereum (Geth) mencionadas en el
# post: altura de bloque, peers conectados y disponibilidad del RPC.
# Pensado para correr contra el nodo local levantado con docker-compose.yml.
#
set -euo pipefail

RPC_URL="${RPC_URL:-http://localhost:8545}"
METRICS_URL="${METRICS_URL:-http://localhost:6060/debug/metrics/prometheus}"

rpc_call() {
  local method="$1"
  curl -s -X POST "$RPC_URL" \
    -H "Content-Type: application/json" \
    --data "{\"jsonrpc\":\"2.0\",\"method\":\"$method\",\"params\":[],\"id\":1}"
}

echo "== Chequeo de salud del nodo Ethereum =="
echo "RPC: $RPC_URL"
echo

echo "-- Altura de bloque --"
BLOCK_HEX=$(rpc_call eth_blockNumber | grep -o '"result":"[^"]*"' | cut -d'"' -f4)
if [ -z "$BLOCK_HEX" ]; then
  echo "ERROR: no se pudo consultar eth_blockNumber. ¿Esta el nodo corriendo? (docker compose up -d)"
  exit 1
fi
echo "Bloque actual: $((BLOCK_HEX))"

echo
echo "-- Peers conectados --"
PEER_HEX=$(rpc_call net_peerCount | grep -o '"result":"[^"]*"' | cut -d'"' -f4)
echo "Peers: $((PEER_HEX))"
echo "(En modo --dev el nodo es standalone, 0 peers es esperado)"

echo
echo "-- Metricas Prometheus disponibles --"
if curl -sf "$METRICS_URL" > /dev/null; then
  echo "OK: $METRICS_URL responde"
  echo "Muestra de metricas relevantes:"
  curl -s "$METRICS_URL" | grep -E '^(chain_head_block|p2p_peers|eth_db_chaindata_disk_size)' || \
    echo "(las metricas de ejemplo aun no aparecen, esperar unos segundos tras el arranque)"
else
  echo "ERROR: no se pudo consultar $METRICS_URL"
  exit 1
fi
