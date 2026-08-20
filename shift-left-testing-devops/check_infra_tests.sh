#!/usr/bin/env bash
#
# "Test driven infrastructure" del post: valida main.tf ANTES de aplicarlo,
# igual que la startup de fintech del ejemplo del artículo. No hace apply,
# no necesita credenciales de AWS: solo sintaxis + políticas básicas.
#
# Uso:
#   ./check_infra_tests.sh
#
# Sale con código 1 y detalla cada hallazgo si encuentra un problema,
# igual que un gate de calidad en el pipeline de CI/CD bloquearía el merge.

set -euo pipefail

TF_FILE="main.tf"
FALLOS=0

echo "== 1/3: terraform validate (sintaxis y sanidad del código) =="
if command -v terraform >/dev/null 2>&1; then
  terraform init -backend=false -input=false >/dev/null
  if terraform validate; then
    echo "OK: sintaxis de Terraform válida"
  else
    echo "FALLO: terraform validate encontró errores"
    FALLOS=$((FALLOS + 1))
  fi
else
  echo "AVISO: terraform no está instalado, se omite este check (ver README)"
fi

echo
echo "== 2/3: puertos administrativos expuestos a internet =="
if grep -qE 'from_port\s*=\s*22' "$TF_FILE" && \
   grep -A5 'from_port\s*=\s*22' "$TF_FILE" | grep -q '0\.0\.0\.0/0'; then
  echo "FALLO: puerto 22 (SSH) abierto a 0.0.0.0/0 en $TF_FILE"
  FALLOS=$((FALLOS + 1))
else
  echo "OK: no se encontró SSH abierto a todo internet"
fi

echo
echo "== 3/3: credenciales hardcodeadas =="
if grep -qE 'password\s*=\s*"[^$"][^"]*"' "$TF_FILE"; then
  echo "FALLO: se encontró una credencial hardcodeada en $TF_FILE"
  FALLOS=$((FALLOS + 1))
else
  echo "OK: no se encontraron credenciales hardcodeadas"
fi

echo
if [ "$FALLOS" -gt 0 ]; then
  echo "RESULTADO: $FALLOS problema(s) encontrado(s). Gate de calidad BLOQUEADO."
  exit 1
fi

echo "RESULTADO: todos los checks pasaron. Gate de calidad OK."
