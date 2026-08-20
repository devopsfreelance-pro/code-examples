#!/usr/bin/env bash
# Despliega un nodo Ethereum (geth --dev) en un cluster kind local y
# verifica que el endpoint RPC responde. Demuestra el patron del post:
# StatefulSet + almacenamiento persistente + probes + NetworkPolicy.
set -euo pipefail

CLUSTER_NAME="ethereum-demo"
DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

command -v kind >/dev/null 2>&1 || { echo "Falta 'kind'. Instalar: https://kind.sigs.k8s.io/docs/user/quick-start/"; exit 1; }
command -v kubectl >/dev/null 2>&1 || { echo "Falta 'kubectl'."; exit 1; }

if ! kind get clusters 2>/dev/null | grep -qx "${CLUSTER_NAME}"; then
  echo "==> Creando cluster kind '${CLUSTER_NAME}'..."
  kind create cluster --name "${CLUSTER_NAME}"
else
  echo "==> Cluster kind '${CLUSTER_NAME}' ya existe, reutilizando."
fi

kubectl config use-context "kind-${CLUSTER_NAME}"

echo "==> Aplicando manifests..."
kubectl apply -f "${DIR}/namespace.yaml"
kubectl apply -f "${DIR}/statefulset.yaml"
kubectl apply -f "${DIR}/service.yaml"
kubectl apply -f "${DIR}/networkpolicy.yaml"

echo "==> Esperando a que el pod este Ready (puede tardar por el pull de la imagen)..."
kubectl -n ethereum rollout status statefulset/geth-node --timeout=180s

echo "==> Port-forward a 127.0.0.1:8545 (Ctrl+C para cortar)..."
kubectl -n ethereum port-forward statefulset/geth-node 8545:8545 >/tmp/geth-port-forward.log 2>&1 &
PF_PID=$!
trap 'kill ${PF_PID} 2>/dev/null || true' EXIT

sleep 3

echo "==> Consultando eth_blockNumber via RPC..."
curl -s -X POST -H "Content-Type: application/json" \
  --data '{"jsonrpc":"2.0","method":"eth_blockNumber","params":[],"id":1}' \
  http://127.0.0.1:8545

echo
echo "==> Listo. Para borrar todo: kind delete cluster --name ${CLUSTER_NAME}"
