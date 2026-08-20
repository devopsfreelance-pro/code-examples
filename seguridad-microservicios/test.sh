#!/usr/bin/env bash
# Ejercita el flujo completo de autenticacion/autorizacion zero-trust:
#  1. login como "luis" (rol user) -> obtiene JWT
#  2. luis consulta su propio pedido (200 OK)
#  3. luis intenta ver el pedido de otro usuario (403 Forbidden)
#  4. login como "ana" (rol admin) -> puede ver cualquier pedido (200 OK)
#  5. request sin token directo al backend (401) -> el backend NO confia
#     en que el trafico venga del gateway, valida siempre
#  6. request con token manipulado (403)
set -euo pipefail

GATEWAY_URL="${GATEWAY_URL:-http://localhost:3000}"
BACKEND_URL="${BACKEND_URL:-http://localhost:4000}"

echo "== 1. Login como luis (rol user) =="
LUIS_TOKEN=$(curl -s -X POST "$GATEWAY_URL/login" \
  -H 'Content-Type: application/json' \
  -d '{"username":"luis","password":"luis123"}' | python3 -c 'import json,sys; print(json.load(sys.stdin)["access_token"])')
echo "Token obtenido (truncado): ${LUIS_TOKEN:0:20}..."

echo
echo "== 2. luis consulta su propio pedido (1) -> esperado 200 =="
curl -s -o /dev/null -w "HTTP %{http_code}\n" "$GATEWAY_URL/api/orders/1" \
  -H "Authorization: Bearer $LUIS_TOKEN"

echo
echo "== 3. luis intenta ver el pedido de ana (2) -> esperado 403 =="
curl -s -o /dev/null -w "HTTP %{http_code}\n" "$GATEWAY_URL/api/orders/2" \
  -H "Authorization: Bearer $LUIS_TOKEN"

echo
echo "== 4. Login como ana (rol admin) y ver pedido de luis (1) -> esperado 200 =="
ANA_TOKEN=$(curl -s -X POST "$GATEWAY_URL/login" \
  -H 'Content-Type: application/json' \
  -d '{"username":"ana","password":"ana123"}' | python3 -c 'import json,sys; print(json.load(sys.stdin)["access_token"])')
curl -s -o /dev/null -w "HTTP %{http_code}\n" "$GATEWAY_URL/api/orders/1" \
  -H "Authorization: Bearer $ANA_TOKEN"

echo
echo "== 5. Request directo al backend SIN token -> esperado 401 (el servicio no confia en el gateway) =="
curl -s -o /dev/null -w "HTTP %{http_code}\n" "$BACKEND_URL/orders/1"

echo
echo "== 6. Request con token manipulado -> esperado 403 =="
curl -s -o /dev/null -w "HTTP %{http_code}\n" "$GATEWAY_URL/api/orders/1" \
  -H "Authorization: Bearer ${LUIS_TOKEN}tampered"

echo
echo "Listo."
