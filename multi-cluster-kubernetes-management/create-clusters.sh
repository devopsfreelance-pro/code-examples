#!/usr/bin/env bash
# Crea dos clusters kind que simulan dos "regiones" de una flota multi-cluster
# (hub-and-spoke simplificado: este script hace de "hub" que registra los spokes).
set -euo pipefail

CLUSTERS=("region-us-east" "region-eu-west")

for name in "${CLUSTERS[@]}"; do
  if kind get clusters 2>/dev/null | grep -qx "$name"; then
    echo "[skip] cluster '$name' ya existe"
    continue
  fi
  echo "[create] cluster '$name'..."
  kind create cluster --name "$name"
done

echo
echo "Clusters disponibles:"
kind get clusters

echo
echo "Contextos kubectl generados:"
kubectl config get-contexts -o name | grep '^kind-' || true
