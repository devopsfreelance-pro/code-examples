#!/usr/bin/env bash
# Demo: Pod Security Admission (built-in) + NetworkPolicy en un cluster kind.
# Crea un namespace con perfil "restricted", intenta desplegar un pod
# inseguro (debe ser RECHAZADO por el API server) y luego uno seguro que
# cumple los requisitos del post (debe ser ACEPTADO).
set -euo pipefail

CLUSTER_NAME="secure-demo"
DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

echo "==> Verificando herramientas requeridas (kind, kubectl)..."
command -v kind >/dev/null 2>&1 || { echo "ERROR: falta kind. Instalar: https://kind.sigs.k8s.io/docs/user/quick-start/#installation"; exit 1; }
command -v kubectl >/dev/null 2>&1 || { echo "ERROR: falta kubectl."; exit 1; }

if kind get clusters 2>/dev/null | grep -qx "${CLUSTER_NAME}"; then
  echo "==> Cluster kind '${CLUSTER_NAME}' ya existe, reutilizando."
else
  echo "==> Creando cluster kind '${CLUSTER_NAME}'..."
  kind create cluster --name "${CLUSTER_NAME}"
fi

kubectl config use-context "kind-${CLUSTER_NAME}" >/dev/null

echo "==> Aplicando namespace con Pod Security Admission (perfil restricted)..."
kubectl apply -f "${DIR}/namespace-restricted.yaml"

echo
echo "==> Intentando desplegar el Pod INSEGURO (se espera RECHAZO)..."
if kubectl apply -f "${DIR}/insecure-pod.yaml"; then
  echo "!! ATENCION: el pod inseguro fue aceptado. Esto no deberia pasar."
else
  echo "OK: el API server rechazo el pod inseguro, tal como se espera."
fi

echo
echo "==> Desplegando el Pod SEGURO (se espera ACEPTACION)..."
kubectl apply -f "${DIR}/secure-pod.yaml"

echo "==> Esperando a que el pod seguro este Ready..."
kubectl wait --for=condition=Ready pod/secure-app -n secure-demo --timeout=90s

echo
echo "==> Aplicando NetworkPolicy de microsegmentacion..."
kubectl apply -f "${DIR}/network-policy.yaml"

echo
echo "==> Estado final:"
kubectl get pods -n secure-demo -o wide
kubectl get networkpolicy -n secure-demo

echo
echo "==> Para limpiar todo:"
echo "    kind delete cluster --name ${CLUSTER_NAME}"
