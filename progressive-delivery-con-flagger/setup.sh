#!/bin/bash
# Levanta un cluster kind, instala Flagger (provider "kubernetes", sin
# service mesh) con un Prometheus propio, y despliega podinfo + el
# recurso Canary que gestiona su progressive delivery, tal como se
# describe en el post "Progressive Delivery: Guía Completa con Flagger".
set -euo pipefail

CLUSTER_NAME="flagger-demo"
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

echo "==> Creando cluster kind '${CLUSTER_NAME}'..."
if kind get clusters 2>/dev/null | grep -qx "${CLUSTER_NAME}"; then
  echo "El cluster ya existe, se reutiliza."
else
  kind create cluster --config "${SCRIPT_DIR}/kind-config.yaml"
fi

echo "==> Agregando el repo Helm de Flagger..."
helm repo add flagger https://flagger.app > /dev/null
helm repo update > /dev/null

echo "==> Instalando Flagger en el namespace 'flagger-system' (con Prometheus propio)..."
kubectl create namespace flagger-system --dry-run=client -o yaml | kubectl apply -f -
helm upgrade -i flagger flagger/flagger \
  --namespace flagger-system \
  --set prometheus.install=true \
  --set meshProvider=kubernetes

echo "==> Esperando a que Flagger y su Prometheus estén listos..."
kubectl wait --for=condition=available --timeout=180s deployment/flagger -n flagger-system
kubectl wait --for=condition=available --timeout=180s deployment/flagger-prometheus -n flagger-system

echo "==> Creando namespace 'test' para la app de ejemplo..."
kubectl create namespace test --dry-run=client -o yaml | kubectl apply -f -

echo "==> Desplegando podinfo (versión inicial) y el loadtester..."
kubectl apply -f "${SCRIPT_DIR}/podinfo.yaml"
kubectl apply -f "${SCRIPT_DIR}/canary.yaml"

echo "==> Esperando a que podinfo y el loadtester estén listos..."
kubectl wait --for=condition=available --timeout=180s deployment/podinfo -n test
kubectl wait --for=condition=available --timeout=180s deployment/flagger-loadtester -n test

echo "==> Esperando a que Flagger genere podinfo-primary a partir del Canary..."
for i in $(seq 1 30); do
  STATUS="$(kubectl get canary podinfo -n test -o jsonpath='{.status.phase}' 2>/dev/null || true)"
  echo "  intento ${i}: phase=${STATUS:-desconocido}"
  if [ "${STATUS}" = "Initialized" ]; then
    break
  fi
  sleep 10
done

echo ""
echo "==> Estado final del Canary:"
kubectl get canary podinfo -n test

echo ""
echo "Listo. La app 'podinfo' está corriendo en modo estable (sin canary"
echo "activo). Para disparar un despliegue progresivo, corré:"
echo "  ./trigger-canary.sh"
