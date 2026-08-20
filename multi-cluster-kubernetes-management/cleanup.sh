#!/usr/bin/env bash
# Elimina los clusters kind creados por create-clusters.sh
set -euo pipefail

CLUSTERS=("region-us-east" "region-eu-west")

for name in "${CLUSTERS[@]}"; do
  if kind get clusters 2>/dev/null | grep -qx "$name"; then
    echo "[delete] cluster '$name'..."
    kind delete cluster --name "$name"
  else
    echo "[skip] cluster '$name' no existe"
  fi
done
