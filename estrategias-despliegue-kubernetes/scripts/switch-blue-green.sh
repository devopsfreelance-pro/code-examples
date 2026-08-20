#!/usr/bin/env bash
# Cambia el trafico del Service demo-bluegreen entre las versiones blue y green
# parcheando su selector. Uso: ./switch-blue-green.sh blue|green
set -euo pipefail

COLOR="${1:-}"

if [[ "$COLOR" != "blue" && "$COLOR" != "green" ]]; then
  echo "Uso: $0 blue|green" >&2
  exit 1
fi

kubectl patch service demo-bluegreen \
  -p "{\"spec\":{\"selector\":{\"app\":\"demo-bluegreen\",\"version\":\"${COLOR}\"}}}"

echo "Service demo-bluegreen ahora apunta a la version: ${COLOR}"
kubectl get service demo-bluegreen -o jsonpath='{.spec.selector}'
echo
