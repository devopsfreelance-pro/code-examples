#!/usr/bin/env bash
# Consulta el estado (nodos, capacidad de CPU/memoria, pods de la app demo)
# de todos los clusters gestionados, simulando la vista centralizada que
# ofrecería un dashboard tipo Grafana con federacion de Prometheus.
set -euo pipefail

CLUSTERS=("prod" "staging")

for cluster in "${CLUSTERS[@]}"; do
  context="kind-${cluster}"
  echo "==================================================="
  echo " Cluster: ${cluster}  (contexto: ${context})"
  echo "==================================================="

  echo "-- Nodos y capacidad --"
  kubectl --context "${context}" get nodes \
    -o custom-columns='NAME:.metadata.name,CPU:.status.capacity.cpu,MEMORY:.status.capacity.memory'

  echo
  echo "-- Pods de la app demo (namespace demo) --"
  kubectl --context "${context}" -n demo get pods -o wide 2>/dev/null \
    || echo "(namespace 'demo' aun no existe en este cluster; corre deploy-all.sh primero)"

  echo
done
