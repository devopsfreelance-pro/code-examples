#!/usr/bin/env bash
set -euo pipefail

echo "Levantando servicios (postgres, redis) para pruebas de integracion..."
docker compose up -d

cleanup() {
  echo "Bajando servicios..."
  docker compose down -v
}
trap cleanup EXIT

wait_for_port() {
  local host=$1
  local port=$2
  local name=$3
  for _ in $(seq 1 30); do
    if (exec 3<>"/dev/tcp/${host}/${port}") >/dev/null 2>&1; then
      exec 3<&- 3>&-
      echo "[OK] ${name} listo en ${host}:${port}"
      return 0
    fi
    sleep 1
  done
  echo "[FAIL] ${name} no respondio en ${host}:${port}"
  exit 1
}

wait_for_port localhost 5432 postgres
wait_for_port localhost 6379 redis

echo "Pruebas de integracion simuladas: conectividad con postgres y redis OK"
