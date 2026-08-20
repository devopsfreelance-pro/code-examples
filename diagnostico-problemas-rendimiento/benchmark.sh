#!/usr/bin/env bash
# Reproduce el flujo de diagnostico del post:
#   1. Medir tiempos de respuesta de un endpoint "lento" (sintoma).
#   2. Medir el mismo endpoint con caching en Redis aplicado (solucion).
#   3. Comparar resultados para confirmar la mejora.

set -euo pipefail

HOST="http://localhost:8090"
REQUESTS=5

echo "== Diagnostico: endpoint SIN cache (/slow) =="
echo "Cada request ejecuta la operacion costosa completa (~300ms esperado)."
for i in $(seq 1 "$REQUESTS"); do
  curl -s "$HOST/slow" | python3 -c "import json,sys; d=json.load(sys.stdin); print(f'  request {$i}: {d[\"elapsed_ms\"]} ms')"
done

echo
echo "== Solucion: endpoint CON cache en Redis (/slow-cached) =="
echo "La primera request paga el costo completo; las siguientes deberian bajar a pocos ms."
for i in $(seq 1 "$REQUESTS"); do
  curl -s "$HOST/slow-cached" | python3 -c "import json,sys; d=json.load(sys.stdin); print(f'  request {$i}: {d[\"elapsed_ms\"]} ms')"
done

echo
echo "Conclusion esperada: /slow se mantiene siempre ~300ms (cuello de botella"
echo "sin resolver); /slow-cached baja a pocos ms desde la segunda request en"
echo "adelante (cache en Redis absorbiendo el costo)."
