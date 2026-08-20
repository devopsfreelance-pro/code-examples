#!/bin/bash
# health-check.sh
# Health check de un nodo Ethereum (cliente de ejecucion + cliente de consenso).
# Adaptado del post para correr contra cualquier host:puerto via variables de entorno.
#
# Uso:
#   EXEC_RPC=http://execution-healthy:8545 \
#   BEACON_API=http://consensus-healthy:5052 \
#   ./health-check.sh <nombre-nodo>

set -u

NODE_NAME="${1:-nodo}"
EXEC_RPC="${EXEC_RPC:-http://localhost:8545}"
BEACON_API="${BEACON_API:-http://localhost:5052}"
MIN_PEERS="${MIN_PEERS:-3}"

check_execution() {
  RESPONSE=$(curl -s -m 5 -X POST "$EXEC_RPC" \
    -H "Content-Type: application/json" \
    -d '{"jsonrpc":"2.0","method":"eth_syncing","params":[],"id":1}')

  if [ -z "$RESPONSE" ]; then
    echo "CRITICAL [$NODE_NAME]: cliente de ejecucion no responde ($EXEC_RPC)"
    return 1
  fi

  PEERS_HEX=$(curl -s -m 5 -X POST "$EXEC_RPC" \
    -H "Content-Type: application/json" \
    -d '{"jsonrpc":"2.0","method":"net_peerCount","params":[],"id":1}' \
    | jq -r '.result')

  PEERS=$((PEERS_HEX))

  if [ "$PEERS" -lt "$MIN_PEERS" ]; then
    echo "WARNING [$NODE_NAME]: solo $PEERS peers conectados (minimo: $MIN_PEERS)"
    return 1
  fi

  echo "OK [$NODE_NAME]: cliente de ejecucion con $PEERS peers"
  return 0
}

check_consensus() {
  HEALTH=$(curl -s -m 5 -o /dev/null -w "%{http_code}" "$BEACON_API/eth/v1/node/health")

  if [ "$HEALTH" != "200" ]; then
    echo "CRITICAL [$NODE_NAME]: beacon node reporta estado no saludable (HTTP $HEALTH)"
    return 1
  fi

  SYNC=$(curl -s -m 5 "$BEACON_API/eth/v1/node/syncing" | jq -r '.data.is_syncing')
  if [ "$SYNC" = "true" ]; then
    echo "WARNING [$NODE_NAME]: beacon node aun sincronizando"
    return 1
  fi

  echo "OK [$NODE_NAME]: beacon node saludable y sincronizado"
  return 0
}

ERRORS=0
check_execution || ERRORS=$((ERRORS + 1))
check_consensus || ERRORS=$((ERRORS + 1))

if [ "$ERRORS" -gt 0 ]; then
  echo "$(date '+%Y-%m-%d %H:%M:%S') - [$NODE_NAME] health check fallido con $ERRORS errores"
  exit 1
fi

echo "$(date '+%Y-%m-%d %H:%M:%S') - [$NODE_NAME] todos los checks pasaron"
exit 0
