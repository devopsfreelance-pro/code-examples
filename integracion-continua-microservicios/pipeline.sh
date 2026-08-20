#!/usr/bin/env bash
# Simula, en la maquina local, las etapas de un pipeline de CI para
# microservicios descritas en el post:
#   build -> unit-test -> integration-test -> contract-test
#
# Cada etapa aborta el pipeline si falla (set -e), igual que un pipeline real.
set -euo pipefail

cd "$(dirname "$0")"

echo "== Stage: build =="
docker compose build

echo "== Stage: unit-test (rapida, sin dependencias) =="
python3 -m venv .venv >/dev/null 2>&1 || true
source .venv/bin/activate
pip install --quiet -r <(echo "flask==3.0.3
psycopg2-binary==2.9.9
pytest==8.2.0
requests==2.32.3")
pytest -m unit -q

echo "== Stage: integration-test (servicio + Postgres reales) =="
docker compose up -d
echo "Esperando a que payment-service este listo..."
for i in $(seq 1 30); do
  if curl -sf http://localhost:8080/health >/dev/null 2>&1; then
    break
  fi
  sleep 1
done
curl -sf http://localhost:8080/health >/dev/null || {
  echo "payment-service no respondio a tiempo"
  docker compose logs
  docker compose down -v
  exit 1
}
pytest -m integration -q

echo "== Stage: contract-test (valida el contrato de /pay) =="
pytest -m contract -q

echo "== Pipeline OK: todas las etapas pasaron =="
docker compose down -v
