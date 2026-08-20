#!/usr/bin/env bash
# Elimina los clusters kind creados para este ejemplo.
set -euo pipefail

for cluster in prod staging; do
  if kind get clusters | grep -qx "${cluster}"; then
    echo "Eliminando cluster '${cluster}'..."
    kind delete cluster --name "${cluster}"
  else
    echo "Cluster '${cluster}' no existe, se omite."
  fi
done
