#!/usr/bin/env bash
# Dispara N requests JSON-RPC contra el load balancer y cuenta cuántas
# respondió cada nodo del pool, para verificar que la carga se distribuye
# (escalabilidad horizontal) en vez de recaer siempre sobre un solo nodo.

set -uo pipefail

LB_URL="${LB_URL:-http://localhost:8080/rpc}"
REQUESTS="${1:-30}"

echo "Enviando $REQUESTS requests eth_blockNumber a $LB_URL ..."
echo

declare -A counts
errors=0

for i in $(seq 1 "$REQUESTS"); do
    body=$(curl -s -X POST "$LB_URL" \
        -H "Content-Type: application/json" \
        -d '{"jsonrpc":"2.0","method":"eth_blockNumber","params":[],"id":1}')

    node=$(echo "$body" | grep -o '"_served_by":"[^"]*"' | cut -d'"' -f4 || true)

    if [ -n "$node" ]; then
        counts["$node"]=$(( ${counts["$node"]:-0} + 1 ))
    else
        errors=$(( errors + 1 ))
    fi
done

if [ "$errors" -gt 0 ]; then
    echo "($errors requests sin respuesta válida, ej. rate limit del $LB_URL)"
    echo
fi

echo "Distribución de requests por nodo:"
for node in "${!counts[@]}"; do
    echo "  $node: ${counts[$node]}"
done
