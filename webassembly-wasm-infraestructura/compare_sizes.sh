#!/usr/bin/env bash
# Compara el tamano del binario Wasm compilado contra una imagen Docker
# "equivalente" (un servidor HTTP minimo en un contenedor Alpine), para
# ilustrar la afirmacion del post: los binarios wasm son 10-100x mas
# pequenos que las imagenes de contenedor tradicionales.
set -euo pipefail

WASM_PATH="target/wasm32-wasip1/release/wasm_infra_demo.wasm"

if [[ ! -f "$WASM_PATH" ]]; then
  echo "No se encontro $WASM_PATH. Corre primero: spin build" >&2
  exit 1
fi

WASM_SIZE=$(stat -c%s "$WASM_PATH" 2>/dev/null || stat -f%z "$WASM_PATH")
WASM_SIZE_KB=$((WASM_SIZE / 1024))

echo "== Tamano del binario Wasm =="
echo "${WASM_PATH}: ${WASM_SIZE} bytes (~${WASM_SIZE_KB} KB)"
echo

if command -v docker >/dev/null 2>&1; then
  echo "== Tamano de una imagen Docker equivalente (nginx:alpine) =="
  docker pull nginx:alpine >/dev/null
  DOCKER_SIZE=$(docker image inspect nginx:alpine --format='{{.Size}}')
  DOCKER_SIZE_MB=$((DOCKER_SIZE / 1024 / 1024))
  echo "nginx:alpine: ${DOCKER_SIZE} bytes (~${DOCKER_SIZE_MB} MB)"
  echo
  echo "== Comparacion =="
  RATIO=$((DOCKER_SIZE / WASM_SIZE))
  echo "La imagen de contenedor es aproximadamente ${RATIO}x mas grande que el binario wasm."
else
  echo "Docker no esta disponible: se omite la comparacion con nginx:alpine." >&2
fi
