#!/usr/bin/env bash
# Demo de Pod Security Standards (nivel "restricted") en un cluster
# local con kind. Muestra como el API server rechaza un pod inseguro
# y admite un pod endurecido en el mismo namespace.
set -euo pipefail

CLUSTER_NAME="pss-demo"
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

command -v kind >/dev/null 2>&1 || { echo "Falta kind. Instalar: https://kind.sigs.k8s.io/docs/user/quick-start/#installation"; exit 1; }
command -v kubectl >/dev/null 2>&1 || { echo "Falta kubectl. Instalar: https://kubernetes.io/docs/tasks/tools/"; exit 1; }

if kind get clusters 2>/dev/null | grep -qx "${CLUSTER_NAME}"; then
  echo "== Cluster kind '${CLUSTER_NAME}' ya existe, lo reutilizo =="
else
  echo "== Creando cluster kind '${CLUSTER_NAME}' =="
  kind create cluster --name "${CLUSTER_NAME}"
fi

kubectl config use-context "kind-${CLUSTER_NAME}" >/dev/null

echo
echo "== Aplicando namespace 'secure-demo' con Pod Security Standard 'restricted' =="
kubectl apply -f "${SCRIPT_DIR}/namespace.yaml"

echo
echo "== Intentando crear el pod INSEGURO (se espera que sea RECHAZADO) =="
if kubectl apply -f "${SCRIPT_DIR}/insecure-pod.yaml"; then
  echo "INESPERADO: el pod inseguro fue admitido. Revisa la version de Kubernetes del cluster."
else
  echo "OK: el API server rechazo el pod inseguro por violar el nivel 'restricted'."
fi

echo
echo "== Creando el pod SEGURO (se espera que sea ADMITIDO) =="
kubectl apply -f "${SCRIPT_DIR}/secure-pod.yaml"

echo
echo "== Esperando a que 'secure-pod' este Ready (timeout 60s) =="
kubectl wait --for=condition=Ready pod/secure-pod -n secure-demo --timeout=60s

echo
echo "== Estado final de los pods en el namespace secure-demo =="
kubectl get pods -n secure-demo -o wide

echo
echo "Demo completa. Para limpiar todo:"
echo "  kind delete cluster --name ${CLUSTER_NAME}"
