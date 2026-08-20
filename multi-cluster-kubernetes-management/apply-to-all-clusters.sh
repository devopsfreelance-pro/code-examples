#!/usr/bin/env bash
# Simula la propagacion de configuracion "fleet" (GitOps): la misma politica
# se aplica a todos los contextos kind-* detectados, uno por uno, y se verifica
# que quedo idéntica en cada cluster (deteccion de drift trivial).
set -euo pipefail

POLICY_FILE="$(dirname "$0")/policies/resource-limits.yaml"
CONTEXTS=$(kubectl config get-contexts -o name | grep '^kind-' || true)

if [ -z "$CONTEXTS" ]; then
  echo "No hay clusters kind-*. Corre primero ./create-clusters.sh" >&2
  exit 1
fi

for ctx in $CONTEXTS; do
  echo "=== Aplicando politica en contexto: $ctx ==="
  kubectl --context "$ctx" apply -f "$POLICY_FILE"
done

echo
echo "=== Verificacion de consistencia entre clusters ==="
for ctx in $CONTEXTS; do
  echo "--- $ctx ---"
  kubectl --context "$ctx" get resourcequota resource-limits -n workloads \
    -o jsonpath='{.spec.hard}' 2>/dev/null
  echo
done
