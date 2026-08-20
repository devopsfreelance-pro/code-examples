#!/usr/bin/env bash
# Dispara dos eventos que las reglas por defecto de Falco (motor eBPF)
# detectan en tiempo real, sin haber instrumentado el proceso objetivo:
#   1. Lectura de un archivo sensible del host (/etc/shadow) desde un
#      contenedor sin confianza -> regla "Read sensitive file untrusted".
#   2. Apertura de una shell interactiva dentro de un contenedor en
#      ejecucion -> regla "Terminal shell in container".
set -euo pipefail

echo "== 1) Leyendo /etc/shadow desde un contenedor busybox =="
docker run --rm busybox sh -c "cat /etc/shadow > /dev/null" || true

echo
echo "== 2) Abriendo una shell dentro de un contenedor nginx =="
CID=$(docker run -d --rm nginx:alpine)
sleep 2
docker exec "$CID" sh -c "echo hola desde una shell inesperada" || true
docker stop "$CID" >/dev/null

echo
echo "Listo. Revisa las alertas con:"
echo "  docker logs falco-ebpf-demo --tail 50"
