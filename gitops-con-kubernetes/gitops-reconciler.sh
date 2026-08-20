#!/usr/bin/env bash
# gitops-reconciler.sh
#
# Mini "operador GitOps" educativo: implementa el loop de reconciliacion
# que describe el post (comparar estado deseado en Git vs estado real en
# el cluster, y corregir divergencias automaticamente). No reemplaza a
# Flux ni ArgoCD, solo ilustra el concepto con kubectl diff/apply.
set -euo pipefail

MANIFESTS_DIR="${1:-manifests}"
NAMESPACE="${2:-demo-app}"
INTERVAL="${3:-5}"

if ! command -v kubectl >/dev/null 2>&1; then
  echo "Error: kubectl no esta instalado o no esta en el PATH." >&2
  exit 1
fi

if [ ! -d "$MANIFESTS_DIR" ]; then
  echo "Error: no existe el directorio de manifests '$MANIFESTS_DIR'." >&2
  exit 1
fi

kubectl get namespace "$NAMESPACE" >/dev/null 2>&1 || kubectl create namespace "$NAMESPACE"

echo "GitOps reconciler iniciado."
echo "Fuente de verdad (Git): $MANIFESTS_DIR"
echo "Namespace destino: $NAMESPACE"
echo "Intervalo de sincronizacion: ${INTERVAL}s"
echo "Presiona Ctrl+C para detener."
echo

while true; do
  DIFF="$(kubectl diff -k "$MANIFESTS_DIR" 2>/dev/null || true)"
  if [ -n "$DIFF" ]; then
    echo "[$(date '+%H:%M:%S')] Drift detectado respecto al estado declarado en Git. Reconciliando..."
    kubectl apply -k "$MANIFESTS_DIR"
  else
    echo "[$(date '+%H:%M:%S')] Estado del cluster == estado en Git. Sin cambios."
  fi
  sleep "$INTERVAL"
done
