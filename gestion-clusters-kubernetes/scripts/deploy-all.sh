#!/usr/bin/env bash
# Despliega el mismo manifest en todos los clusters (prod y staging),
# etiquetando el namespace con el entorno correspondiente en cada uno.
# Simula la propagacion de recursos que hacen herramientas como
# Rancher Fleet, Karmada o ArgoCD ApplicationSets en un escenario multi-cluster.
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
MANIFESTS_DIR="$(cd "${SCRIPT_DIR}/../manifests" && pwd)"

CLUSTERS=("prod" "staging")

for cluster in "${CLUSTERS[@]}"; do
  context="kind-${cluster}"
  echo "=== Desplegando en cluster '${cluster}' (contexto: ${context}) ==="

  kubectl --context "${context}" create namespace demo \
    --dry-run=client -o yaml | kubectl --context "${context}" apply -f -

  kubectl --context "${context}" label namespace demo \
    environment="${cluster}" team=platform --overwrite

  kubectl --context "${context}" apply -f "${MANIFESTS_DIR}/app-deployment.yaml"

  kubectl --context "${context}" -n demo rollout status deployment/demo-app --timeout=90s
  echo
done

echo "Despliegue completado en todos los clusters."
