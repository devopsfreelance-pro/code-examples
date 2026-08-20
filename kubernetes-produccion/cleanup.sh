#!/usr/bin/env bash
# Borra el cluster kind creado por deploy.sh
set -euo pipefail

CLUSTER_NAME="k8s-produccion-demo"

if kind get clusters 2>/dev/null | grep -qx "${CLUSTER_NAME}"; then
  kind delete cluster --name "${CLUSTER_NAME}"
  echo "Cluster ${CLUSTER_NAME} eliminado."
else
  echo "No existe el cluster ${CLUSTER_NAME}, nada que borrar."
fi
