#!/usr/bin/env bash
# Genera un secreto JWT para el engine API tal como recomienda el post,
# con entropia real y permisos restrictivos (equivalente a lo que geth
# espera en --authrpc.jwtsecret).
set -euo pipefail

OUT_DIR="${1:-./secrets}"
OUT_FILE="${OUT_DIR}/jwt.hex"

mkdir -p "$OUT_DIR"

if [ -f "$OUT_FILE" ]; then
  echo "Ya existe $OUT_FILE, no se sobreescribe. Borralo si queres regenerarlo." >&2
  exit 1
fi

openssl rand -hex 32 > "$OUT_FILE"
chmod 600 "$OUT_FILE"

echo "Secreto JWT generado en $OUT_FILE"
echo "Permisos:"
ls -l "$OUT_FILE"
