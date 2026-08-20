#!/usr/bin/env bash
# Demuestra el concepto central del post: eliminar puntos unicos de fallo
# mediante redundancia + failover automatico.
#
# 1. Hace varios requests contra el balanceador y muestra que instancia
#    respondio cada vez (deberian alternar entre web1 y web2).
# 2. Tumba una instancia (simulando un fallo real, no solo el healthcheck).
# 3. Vuelve a pedir: el trafico sigue sirviendose, ahora solo desde la
#    instancia sana, sin downtime visible para el cliente.

set -euo pipefail

URL="http://localhost:8080"

echo "== 1) Trafico normal contra las dos instancias =="
for i in $(seq 1 6); do
  curl -s "$URL" | tr -d '\n'
  echo "  (request $i)"
done

echo
echo "== 2) Simulando la caida de web1 (docker compose stop web1) =="
docker compose stop web1
sleep 3

echo
echo "== 3) Trafico despues del fallo: solo deberia responder web2 =="
for i in $(seq 1 6); do
  curl -s "$URL" | tr -d '\n'
  echo "  (request $i)"
done

echo
echo "== 4) Restaurando web1 =="
docker compose start web1
echo "Listo. Esperar unos segundos a que pase el healthcheck y volver a probar."
