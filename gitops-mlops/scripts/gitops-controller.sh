#!/usr/bin/env bash
# gitops-controller.sh
#
# Mini "operador GitOps": vigila un repo Git local (el "source of truth") y,
# cada vez que detecta un commit nuevo, aplica el contenido de manifests/
# al cluster de Kubernetes. Es una versión minimalista del loop de
# reconciliación que hacen ArgoCD o FluxCD en el post.
#
# Uso:
#   NAMESPACE=mlops-demo ./gitops-controller.sh /ruta/al/gitops-repo
set -euo pipefail

REPO_DIR="${1:?Uso: gitops-controller.sh <ruta-al-repo-gitops>}"
NAMESPACE="${NAMESPACE:-mlops-demo}"
INTERVAL="${INTERVAL:-5}"

if [ ! -d "${REPO_DIR}/.git" ]; then
  echo "Error: ${REPO_DIR} no es un repositorio Git." >&2
  exit 1
fi

kubectl create namespace "${NAMESPACE}" --dry-run=client -o yaml | kubectl apply -f - >/dev/null

echo "[controller] Reconciliando ${REPO_DIR} -> namespace/${NAMESPACE} (cada ${INTERVAL}s)"

LAST_COMMIT=""
while true; do
  CURRENT_COMMIT="$(git -C "${REPO_DIR}" rev-parse HEAD)"
  if [ "${CURRENT_COMMIT}" != "${LAST_COMMIT}" ]; then
    echo "[controller] $(date '+%H:%M:%S') Nuevo commit detectado: ${CURRENT_COMMIT}"
    kubectl apply -n "${NAMESPACE}" -f "${REPO_DIR}/manifests/"
    LAST_COMMIT="${CURRENT_COMMIT}"
    echo "[controller] $(date '+%H:%M:%S') Estado reconciliado."
  fi
  sleep "${INTERVAL}"
done
