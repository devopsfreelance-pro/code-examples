#!/usr/bin/env bash
# Demuestra el "automatic discovery" de Traefik: levanta un contenedor nuevo
# en caliente, con las labels correctas, y lo consulta sin reiniciar Traefik
# ni tocar ningún archivo de configuración.
set -euo pipefail

cd "$(dirname "$0")/.."

echo "== 1. Servicios a.localhost y b.localhost (ya definidos en docker-compose.yml) =="
curl -s -H "Host: a.localhost" http://localhost/ | head -n 5
echo "---"
curl -s -H "Host: b.localhost" http://localhost/ | head -n 5

echo
echo "== 2. Levantando whoami-c EN CALIENTE con 'docker run', sin editar compose ni reiniciar Traefik =="
docker run -d --rm \
  --name whoami-c \
  --network traefik-contenedores_default \
  --label "traefik.enable=true" \
  --label "traefik.http.routers.whoami-c.rule=Host(\`c.localhost\`)" \
  --label "traefik.http.routers.whoami-c.entrypoints=web" \
  --label "traefik.http.services.whoami-c.loadbalancer.server.port=80" \
  traefik/whoami:v1.10 >/dev/null

echo "Esperando a que Traefik detecte el nuevo contenedor (descubrimiento automático)..."
sleep 3

echo
echo "== 3. c.localhost ya responde, sin haber tocado la configuración de Traefik =="
curl -s -H "Host: c.localhost" http://localhost/ | head -n 5

echo
echo "== 4. Limpieza del contenedor de la demo =="
docker stop whoami-c >/dev/null
echo "Listo."
