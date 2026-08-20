#!/usr/bin/env bash
# Elimina el cluster kind usado por la demo de Crossplane.
set -euo pipefail

CLUSTER_NAME="crossplane-demo"

echo "==> Borrando cluster kind '${CLUSTER_NAME}'"
kind delete cluster --name "${CLUSTER_NAME}"
echo "Listo."
