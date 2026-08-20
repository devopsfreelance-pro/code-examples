#!/bin/bash
# Elimina el cluster kind creado por setup.sh
set -euo pipefail

CLUSTER_NAME="gitops-argocd-demo"

echo "==> Eliminando cluster kind '${CLUSTER_NAME}'..."
kind delete cluster --name "${CLUSTER_NAME}"
echo "Listo."
