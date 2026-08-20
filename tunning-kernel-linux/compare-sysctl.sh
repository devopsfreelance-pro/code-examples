#!/usr/bin/env bash
# compare-sysctl.sh
#
# Compara los parametros de sysctl entre el contenedor "nginx-default"
# (sin tuning) y "nginx-tuned" (con los parametros de sysctl.d/99-tuning-demo.conf
# aplicados via docker-compose). Sirve para ver, sin tocar el kernel del host,
# el efecto real de aplicar tuning a nivel de namespace de red del contenedor.

set -euo pipefail

PARAMS=(
  "net.core.somaxconn"
  "net.ipv4.tcp_fin_timeout"
  "net.ipv4.tcp_syncookies"
  "net.ipv4.ip_local_port_range"
)

for cmd in docker; do
  if ! command -v "$cmd" >/dev/null 2>&1; then
    echo "Error: falta el comando '$cmd' en el PATH." >&2
    exit 1
  fi
done

for container in nginx-default nginx-tuned; do
  if ! docker inspect "$container" >/dev/null 2>&1; then
    echo "Error: el contenedor '$container' no existe. Corre 'docker compose up -d' primero." >&2
    exit 1
  fi
done

printf "%-32s | %-20s | %-20s\n" "Parametro" "nginx-default" "nginx-tuned"
printf -- "-------------------------------------------------------------------\n"

for param in "${PARAMS[@]}"; do
  default_value=$(docker exec nginx-default sysctl -n "$param" 2>/dev/null || echo "N/D")
  tuned_value=$(docker exec nginx-tuned sysctl -n "$param" 2>/dev/null || echo "N/D")
  printf "%-32s | %-20s | %-20s\n" "$param" "$default_value" "$tuned_value"
done
