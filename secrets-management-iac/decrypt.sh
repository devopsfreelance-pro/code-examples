#!/usr/bin/env bash
# decrypt.sh - descifra demo-values.enc.yaml usando la clave age local.
# Simula lo que haria un pipeline de CI o una app en el arranque: tiene la
# clave privada (via SOPS_AGE_KEY_FILE) y con eso recupera los valores.
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
KEY_FILE="$SCRIPT_DIR/keys/age-key.txt"
ENC_FILE="$SCRIPT_DIR/demo-values.enc.yaml"

if ! command -v sops >/dev/null 2>&1; then
  echo "Error: 'sops' no esta instalado. Ver README.md, seccion Requisitos." >&2
  exit 1
fi

if [ ! -f "$KEY_FILE" ]; then
  echo "Error: no se encontro $KEY_FILE. Corre ./encrypt.sh primero." >&2
  exit 1
fi

if [ ! -f "$ENC_FILE" ]; then
  echo "Error: no se encontro $ENC_FILE. Corre ./encrypt.sh primero." >&2
  exit 1
fi

export SOPS_AGE_KEY_FILE="$KEY_FILE"

echo "==> Descifrando $ENC_FILE con la clave privada local"
sops --decrypt "$ENC_FILE"
