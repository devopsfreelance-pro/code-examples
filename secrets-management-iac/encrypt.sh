#!/usr/bin/env bash
# encrypt.sh - genera un par de claves age local (solo para este demo) y cifra
# demo-values.plain.yaml con SOPS, produciendo demo-values.enc.yaml.
#
# Esto es el patron GitOps del post: el valor cifrado SI se puede comitear a
# git, el archivo en texto plano y la clave privada JAMAS.
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
KEY_DIR="$SCRIPT_DIR/keys"
KEY_FILE="$KEY_DIR/age-key.txt"
PLAIN_FILE="$SCRIPT_DIR/demo-values.plain.yaml"
ENC_FILE="$SCRIPT_DIR/demo-values.enc.yaml"

for cmd in sops age-keygen; do
  if ! command -v "$cmd" >/dev/null 2>&1; then
    echo "Error: '$cmd' no esta instalado. Ver README.md, seccion Requisitos." >&2
    exit 1
  fi
done

mkdir -p "$KEY_DIR"

if [ ! -f "$KEY_FILE" ]; then
  echo "==> Generando par de claves age (solo para este demo local)"
  age-keygen -o "$KEY_FILE"
else
  echo "==> Reutilizando clave age existente en $KEY_FILE"
fi

PUBLIC_KEY="$(grep 'public key:' "$KEY_FILE" | sed 's/.*: //')"
echo "==> Clave publica age: $PUBLIC_KEY"

echo "==> Cifrando $PLAIN_FILE -> $ENC_FILE"
sops --encrypt --age "$PUBLIC_KEY" "$PLAIN_FILE" > "$ENC_FILE"

echo
echo "==> Listo."
echo "    - $ENC_FILE es seguro de comitear a git (valores cifrados)."
echo "    - $PLAIN_FILE y $KEY_DIR/ NUNCA se comitean."
echo
echo "Vista previa del archivo cifrado:"
cat "$ENC_FILE"
