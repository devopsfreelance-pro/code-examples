#!/usr/bin/env bash
# Crea un cluster kind de 3 nodos, instala metrics-server y despliega los
# manifiestos "production-ready" (resources, probes, HPA, NetworkPolicy, PDB).
set -euo pipefail

CLUSTER_NAME="k8s-produccion-demo"
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

if ! command -v kind >/dev/null 2>&1; then
  echo "ERROR: falta 'kind'. Instalación: https://kind.sigs.k8s.io/docs/user/quick-start/" >&2
  exit 1
fi
if ! command -v kubectl >/dev/null 2>&1; then
  echo "ERROR: falta 'kubectl'." >&2
  exit 1
fi

if kind get clusters 2>/dev/null | grep -qx "${CLUSTER_NAME}"; then
  echo "El cluster ${CLUSTER_NAME} ya existe, reutilizándolo."
else
  echo "==> Creando cluster kind (1 control-plane + 2 workers)..."
  kind create cluster --config "${SCRIPT_DIR}/kind-cluster.yaml"
fi

kubectl cluster-info --context "kind-${CLUSTER_NAME}"

echo "==> Instalando metrics-server (requerido por el HPA)..."
kubectl apply -f https://github.com/kubernetes-sigs/metrics-server/releases/latest/download/components.yaml

# En kind los kubelets usan certificados self-signed: metrics-server necesita
# --kubelet-insecure-tls para poder leer las métricas de CPU/memoria.
kubectl patch deployment metrics-server -n kube-system --type=json \
  -p='[{"op":"add","path":"/spec/template/spec/containers/0/args/-","value":"--kubelet-insecure-tls"}]'

echo "==> Esperando a metrics-server..."
kubectl rollout status deployment/metrics-server -n kube-system --timeout=180s

echo "==> Aplicando manifiestos (namespace, LimitRange, Deployment, Service, HPA, NetworkPolicy, PDB)..."
kubectl apply -f "${SCRIPT_DIR}/manifests.yaml"

echo "==> Esperando a que el Deployment esté listo..."
kubectl rollout status deployment/api-demo -n production --timeout=180s

echo
echo "Listo. Estado actual:"
kubectl get deployment,pods,hpa,pdb,networkpolicy -n production
