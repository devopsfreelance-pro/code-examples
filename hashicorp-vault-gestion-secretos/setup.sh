#!/bin/sh
# Demo de HashiCorp Vault: motor KV v2, politica de minimo privilegio y
# token de aplicacion con acceso restringido a una sola ruta de secretos.
# Pensado para correr DENTRO del contenedor vault-demo, con cwd en /demo
# (el docker-compose.yml monta este directorio ahi). Ver README.md.
set -euo pipefail

export VAULT_ADDR="http://127.0.0.1:8200"
export VAULT_TOKEN="root-demo-token"

echo "==> Esperando a que Vault este listo..."
until vault status >/dev/null 2>&1; do
  sleep 1
done
echo "Vault activo (dev mode, ya desellado) en ${VAULT_ADDR}"

echo
echo "==> Habilitando motor de secretos KV v2 en la ruta 'secret/'..."
if ! vault secrets list -format=json | grep -q '"secret/"'; then
  vault secrets enable -path=secret -version=2 kv
else
  echo "El motor 'secret/' ya estaba habilitado, se reutiliza."
fi

echo
echo "==> Guardando un secreto de ejemplo en secret/myapp/db..."
vault kv put secret/myapp/db username="app_user" password="S3cr3tP4ss!"

echo
echo "==> Cargando la politica de minimo privilegio (app-policy.hcl)..."
vault policy write myapp-policy ./app-policy.hcl

echo
echo "==> Creando un token de aplicacion limitado a la politica myapp-policy..."
APP_TOKEN=$(vault token create -policy="myapp-policy" -field=token)
echo "Token de aplicacion generado: ${APP_TOKEN}"

echo
echo "==> Verificando que el token de aplicacion SI puede leer secret/myapp/db..."
VAULT_TOKEN="${APP_TOKEN}" vault kv get secret/myapp/db

echo
echo "==> Verificando que el token de aplicacion NO puede leer secret/otraapp/db (esperado: error de permisos)..."
vault kv put secret/otraapp/db username="otra_app" password="OtraPass!" >/dev/null
if VAULT_TOKEN="${APP_TOKEN}" vault kv get secret/otraapp/db 2>/dev/null; then
  echo "ERROR: el token de aplicacion pudo leer un secreto fuera de su politica"
  exit 1
else
  echo "Correcto: acceso denegado (permission denied) como se esperaba."
fi

echo
echo "==> Demo completa. Resumen:"
echo " - Secreto propio (secret/myapp/db): acceso permitido"
echo " - Secreto ajeno (secret/otraapp/db): acceso denegado"
echo " - Token root: ${VAULT_TOKEN}"
echo " - Token de app (uso limitado): ${APP_TOKEN}"
