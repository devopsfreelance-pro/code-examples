#!/usr/bin/env bash
# Demuestra la resiliencia de la infraestructura: mata uno de los 3 nodos
# blockchain a mitad del test y verifica que el balanceador siga
# respondiendo 200 usando los nodos que quedan sanos.
set -euo pipefail

LB_URL="http://localhost:8080"
TOTAL_REQUESTS=20
KILL_AFTER=8
FAILED=0

echo "== Test de resiliencia: infraestructura blockchain =="
echo "Enviando ${TOTAL_REQUESTS} requests al balanceador (${LB_URL})..."
echo

for i in $(seq 1 "$TOTAL_REQUESTS"); do
    if [ "$i" -eq "$KILL_AFTER" ]; then
        echo ">>> Simulando fallo: deteniendo node-a"
        docker compose stop node-a >/dev/null
    fi

    response=$(curl -s -o /tmp/resp_body.json -w "%{http_code}" "$LB_URL" || echo "000")
    node=$(python3 -c "import json;print(json.load(open('/tmp/resp_body.json'))['node'])" 2>/dev/null || echo "sin-respuesta")

    if [ "$response" = "200" ]; then
        echo "request ${i}: OK (200) atendido por ${node}"
    else
        echo "request ${i}: FALLO (http ${response})"
        FAILED=$((FAILED + 1))
    fi

    sleep 0.5
done

echo
echo ">>> Restaurando node-a"
docker compose start node-a >/dev/null

echo
if [ "$FAILED" -eq 0 ]; then
    echo "RESULTADO: ${TOTAL_REQUESTS}/${TOTAL_REQUESTS} requests exitosos pese a la caida de node-a."
else
    echo "RESULTADO: ${FAILED} requests fallaron de ${TOTAL_REQUESTS}."
fi
