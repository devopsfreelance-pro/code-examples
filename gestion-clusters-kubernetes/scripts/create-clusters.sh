#!/usr/bin/env bash
# Crea dos clusters locales con kind (prod y staging) para simular
# un escenario de gestion multi-cluster tipo hub-and-spoke.
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
KIND_DIR="$(cd "${SCRIPT_DIR}/../kind" && pwd)"

for cluster in prod staging; do
  if kind get clusters | grep -qx "${cluster}"; then
    echo "Cluster '${cluster}' ya existe, se omite creacion."
  else
    echo "Creando cluster '${cluster}'..."
    kind create cluster --config "${KIND_DIR}/cluster-${cluster}.yaml"
  fi
done

echo
echo "Clusters disponibles:"
kind get clusters

echo
echo "Contextos de kubectl generados:"
kubectl config get-contexts | grep -E "kind-(prod|staging)" || true
