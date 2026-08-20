#!/usr/bin/env bash
# Levanta un cluster kind local, instala Istio (perfil demo) e implementa
# el ejemplo de enrutamiento del post: reviews-v1 / reviews-v2 + VirtualService
# que dirige al usuario "jason" a v2 y al resto a v1.
#
# Requisitos: docker, kind, kubectl, istioctl (ver README.md para instalarlos).
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
CLUSTER_NAME="istio-demo"

command -v kind >/dev/null 2>&1 || { echo "Falta kind. Ver README.md."; exit 1; }
command -v kubectl >/dev/null 2>&1 || { echo "Falta kubectl. Ver README.md."; exit 1; }
command -v istioctl >/dev/null 2>&1 || { echo "Falta istioctl. Ver README.md."; exit 1; }

echo "==> Creando cluster kind '${CLUSTER_NAME}' (si no existe)"
if ! kind get clusters | grep -qx "${CLUSTER_NAME}"; then
  kind create cluster --config "${SCRIPT_DIR}/kind-config.yaml"
else
  echo "El cluster '${CLUSTER_NAME}' ya existe, se reutiliza."
fi

kubectl config use-context "kind-${CLUSTER_NAME}"

echo "==> Instalando Istio (perfil demo)"
istioctl install --set profile=demo -y

echo "==> Habilitando inyeccion automatica de sidecars en el namespace default"
kubectl label namespace default istio-injection=enabled --overwrite

echo "==> Desplegando reviews-v1, reviews-v2 y el pod cliente 'sleep'"
kubectl apply -f "${SCRIPT_DIR}/reviews-app.yaml"

echo "==> Esperando a que los pods esten listos (con sidecar inyectado)"
kubectl rollout status deployment/reviews-v1 --timeout=180s
kubectl rollout status deployment/reviews-v2 --timeout=180s
kubectl wait --for=condition=Ready pod/sleep --timeout=180s

echo "==> Aplicando DestinationRule y VirtualService"
kubectl apply -f "${SCRIPT_DIR}/istio-routing.yaml"

echo "==> Prueba 1: request sin header 'end-user' -> debe responder reviews-v1"
kubectl exec sleep -c curl -- curl -s reviews | grep Hostname

echo "==> Prueba 2: request con header 'end-user: jason' -> debe responder reviews-v2"
kubectl exec sleep -c curl -- curl -s -H "end-user: jason" reviews | grep Hostname

echo "==> Listo. Repeti los dos curl de arriba para confirmar el enrutamiento."
