#!/usr/bin/env bash
# Crea un cluster kind, instala metrics-server (adaptado para kind) y
# despliega el namespace + ResourceQuota + Deployment sobredimensionado.
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ROOT_DIR="$(cd "${SCRIPT_DIR}/.." && pwd)"
CLUSTER_NAME="cost-opt"

echo "=== 1. Creando cluster kind '${CLUSTER_NAME}' ==="
if kind get clusters 2>/dev/null | grep -qx "${CLUSTER_NAME}"; then
  echo "El cluster '${CLUSTER_NAME}' ya existe, se reutiliza."
else
  kind create cluster --config "${ROOT_DIR}/kind/cluster.yaml"
fi

kubectl config use-context "kind-${CLUSTER_NAME}"

echo ""
echo "=== 2. Instalando metrics-server ==="
kubectl apply -f https://github.com/kubernetes-sigs/metrics-server/releases/latest/download/components.yaml

# kind usa certificados de kubelet self-signed: metrics-server necesita
# --kubelet-insecure-tls para poder scrapear en un cluster local.
kubectl patch deployment metrics-server -n kube-system --type=json \
  -p '[{"op":"add","path":"/spec/template/spec/containers/0/args/-","value":"--kubelet-insecure-tls"}]'

echo "Esperando a que metrics-server este listo..."
kubectl rollout status deployment/metrics-server -n kube-system --timeout=120s

echo ""
echo "=== 3. Desplegando namespace + ResourceQuota + Deployment ==="
kubectl apply -f "${ROOT_DIR}/manifests/app.yaml"
kubectl rollout status deployment/api-catalogo -n cost-demo --timeout=120s

echo ""
echo "Listo. Corre ./scripts/check-rightsizing.sh para ver requests vs uso real."
