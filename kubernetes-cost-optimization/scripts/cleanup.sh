#!/usr/bin/env bash
# Borra el cluster kind creado por setup.sh.
set -euo pipefail

CLUSTER_NAME="cost-opt"

if kind get clusters 2>/dev/null | grep -qx "${CLUSTER_NAME}"; then
  kind delete cluster --name "${CLUSTER_NAME}"
  echo "Cluster '${CLUSTER_NAME}' eliminado."
else
  echo "El cluster '${CLUSTER_NAME}' no existe, nada que borrar."
fi
