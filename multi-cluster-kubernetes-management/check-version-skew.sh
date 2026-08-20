#!/usr/bin/env bash
# Chequeo previo a una "ola" de upgrade (ver seccion "Estrategia de upgrades
# por olas" del post): lista la version de control plane de cada cluster de
# la flota para detectar skew antes de decidir el orden de actualizacion.
set -euo pipefail

CONTEXTS=$(kubectl config get-contexts -o name | grep '^kind-' || true)

if [ -z "$CONTEXTS" ]; then
  echo "No hay clusters kind-*. Corre primero ./create-clusters.sh" >&2
  exit 1
fi

printf "%-25s %s\n" "CLUSTER" "VERSION SERVER"
printf "%-25s %s\n" "-------" "--------------"
for ctx in $CONTEXTS; do
  version=$(kubectl --context "$ctx" version -o json 2>/dev/null \
    | python3 -c 'import json,sys; print(json.load(sys.stdin)["serverVersion"]["gitVersion"])' 2>/dev/null || echo "N/A")
  printf "%-25s %s\n" "$ctx" "$version"
done
