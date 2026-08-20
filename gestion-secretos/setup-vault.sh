#!/usr/bin/env bash
# Crea un secreto de ejemplo (credenciales de base de datos) en Vault,
# tal como haria una app o un pipeline CI/CD al arrancar.
set -euo pipefail

VAULT_ADDR="http://127.0.0.1:8200"
VAULT_TOKEN="root-token-demo"

echo "Esperando a que Vault este disponible en ${VAULT_ADDR}..."
for i in $(seq 1 20); do
  if curl -fsS "${VAULT_ADDR}/v1/sys/health?standbyok=true" >/dev/null 2>&1; then
    echo "Vault esta arriba."
    break
  fi
  if [ "$i" -eq 20 ]; then
    echo "Vault no respondio a tiempo." >&2
    exit 1
  fi
  sleep 1
done

echo "Habilitando el motor de secretos KV v2 en 'secret/' (si no existe)..."
curl -fsS \
  --header "X-Vault-Token: ${VAULT_TOKEN}" \
  --request POST \
  --data '{"type":"kv-v2"}' \
  "${VAULT_ADDR}/v1/sys/mounts/secret" >/dev/null 2>&1 || true

echo "Escribiendo credenciales de ejemplo en secret/data/myapp/db..."
curl -fsS \
  --header "X-Vault-Token: ${VAULT_TOKEN}" \
  --request POST \
  --data '{"data":{"username":"app_user","password":"S3cr3tP4ss!"}}' \
  "${VAULT_ADDR}/v1/data/myapp/db" >/dev/null

echo "Listo. Podes leer las credenciales con:"
echo "  ./fetch_credentials.py"
