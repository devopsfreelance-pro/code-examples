#!/usr/bin/env bash
# Simula el flujo de despliegue del post:
#   1. Construir la nueva golden image (Green) sin tocar la que esta viva (Blue)
#   2. Levantar Green al lado de Blue y esperar su health check
#   3. Mover el trafico del balanceador de Blue a Green (equivalente a
#      apuntar el ALB al nuevo Target Group / nueva AMI en el ASG)
#   4. Apagar Blue (equivalente a terminar las instancias viejas del ASG)
#
# En ningun momento se edita un contenedor corriendo: si algo esta mal en
# Green, se destruye y se vuelve a construir. Blue nunca se modifica
# in-place, solo se reemplaza.

set -euo pipefail
cd "$(dirname "$0")"

NGINX_CONF="nginx.conf"
GREEN_HEALTH_RETRIES=15

echo "==> [1/5] Construyendo golden image Green (docker compose build green)"
docker compose build green

echo "==> [2/5] Desplegando Green junto a Blue"
docker compose --profile green up -d green

echo "==> [3/5] Esperando health check de Green"
ok=false
for i in $(seq 1 "$GREEN_HEALTH_RETRIES"); do
    if docker compose exec -T green python3 -c \
        "import urllib.request; urllib.request.urlopen('http://127.0.0.1:8080/health')" \
        >/dev/null 2>&1; then
        ok=true
        break
    fi
    echo "    intento $i/$GREEN_HEALTH_RETRIES: Green todavia no responde, esperando..."
    sleep 2
done

if [ "$ok" != "true" ]; then
    echo "ERROR: Green nunca paso el health check. Abortando, Blue sigue sirviendo trafico."
    docker compose stop green
    exit 1
fi

echo "==> [4/5] Moviendo el trafico de nginx: blue -> green"
sed -i.bak 's/server blue:8080;/server green:8080;/' "$NGINX_CONF"
docker compose exec -T nginx nginx -s reload

echo "==> [5/5] Apagando Blue (instancia vieja del pool)"
docker compose stop blue

echo ""
echo "Deploy completo. Verificar con: curl -s http://localhost:8080 | python3 -m json.tool"
echo "Para volver atras (rollback trivial, como describe el post):"
echo "  cp ${NGINX_CONF}.bak ${NGINX_CONF} && docker compose start blue && docker compose exec -T nginx nginx -s reload && docker compose stop green"
