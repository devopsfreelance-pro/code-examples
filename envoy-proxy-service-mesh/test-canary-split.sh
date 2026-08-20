#!/usr/bin/env bash
# Envía N requests a Envoy (puerto 10000) y cuenta cuántas cayeron
# en pagos-v1 vs pagos-v2, para verificar el split ponderado 90/10
# definido en envoy.yaml (weighted_clusters).
set -euo pipefail

N="${1:-50}"
URL="http://localhost:10000/"

v1=0
v2=0

echo "Enviando $N requests a $URL ..."
for _ in $(seq 1 "$N"); do
  body="$(curl -s "$URL")"
  case "$body" in
    *v1*) v1=$((v1 + 1)) ;;
    *v2*) v2=$((v2 + 1)) ;;
    *) echo "Respuesta inesperada: $body" >&2 ;;
  esac
done

echo ""
echo "Resultado del split de tráfico:"
echo "  pagos-v1: $v1 requests"
echo "  pagos-v2: $v2 requests"
echo ""
echo "Esperado (aprox, weighted_clusters 90/10): v1 ~90%, v2 ~10%"
