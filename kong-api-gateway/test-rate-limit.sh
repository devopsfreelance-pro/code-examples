#!/usr/bin/env bash
# Dispara 6 peticiones seguidas contra la ruta expuesta por Kong para
# mostrar el plugin rate-limiting (5 peticiones/minuto) en accion.
# La 6ta peticion debe devolver HTTP 429.

set -euo pipefail

URL="http://localhost:8000/httpbin/get"

for i in $(seq 1 6); do
  status=$(curl -s -o /dev/null -w "%{http_code}" "$URL")
  echo "Peticion $i -> HTTP $status"
done
