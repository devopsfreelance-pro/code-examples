#!/usr/bin/env bash
# Demo automatizada de gestion de servicios con systemd dentro de un
# contenedor Docker que corre systemd como PID 1.
#
# Ejecuta: start/enable/status, journalctl, y la politica Restart=on-failure.
set -euo pipefail

CONTAINER=systemd-demo

echo "== 1) Build + levantar contenedor con systemd como init =="
docker compose up -d --build

echo "== 2) Esperar a que systemd termine de arrancar (target multi-user) =="
for i in $(seq 1 30); do
    if docker exec "$CONTAINER" systemctl is-system-running 2>/dev/null | grep -qE "running|degraded"; then
        break
    fi
    sleep 1
done
docker exec "$CONTAINER" systemctl is-system-running || true

echo
echo "== 3) Estado del servicio (habilitado en el build, arrancado por multi-user.target) =="
docker exec "$CONTAINER" systemctl status webapp.service --no-pager || true

echo
echo "== 4) Probar el servicio HTTP =="
curl -s http://localhost:8080/ || echo "(si falla, esperar unos segundos y reintentar: curl http://localhost:8080/)"

echo
echo "== 5) systemctl is-active / is-enabled =="
docker exec "$CONTAINER" systemctl is-active webapp.service
docker exec "$CONTAINER" systemctl is-enabled webapp.service

echo
echo "== 6) Provocar un fallo y observar Restart=on-failure =="
curl -s http://localhost:8080/crash || true
sleep 4
docker exec "$CONTAINER" systemctl status webapp.service --no-pager || true

echo
echo "== 7) Logs estructurados con journalctl =="
docker exec "$CONTAINER" journalctl -u webapp.service --no-pager -n 30

echo
echo "== 8) systemd-analyze (tiempos de arranque) =="
docker exec "$CONTAINER" systemd-analyze || true

echo
echo "Demo completa. Para limpiar: docker compose down"
