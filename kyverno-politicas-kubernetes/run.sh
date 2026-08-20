#!/usr/bin/env bash
# Demo de Kyverno: crea un cluster kind, instala Kyverno, aplica una ClusterPolicy
# que exige limites de CPU/memoria, y prueba un Pod conforme y uno no conforme.
set -euo pipefail

CLUSTER_NAME="kyverno-demo"
NAMESPACE="demo-kyverno"
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

for bin in kind kubectl helm; do
  if ! command -v "$bin" >/dev/null 2>&1; then
    echo "ERROR: falta '$bin' en el PATH. Instalalo antes de correr este script." >&2
    exit 1
  fi
done

echo "== 1/6: creando cluster kind '${CLUSTER_NAME}' (si no existe) =="
if ! kind get clusters 2>/dev/null | grep -qx "${CLUSTER_NAME}"; then
  kind create cluster --name "${CLUSTER_NAME}"
else
  echo "El cluster '${CLUSTER_NAME}' ya existe, se reutiliza."
fi
kubectl config use-context "kind-${CLUSTER_NAME}"

echo "== 2/6: instalando Kyverno via Helm =="
helm repo add kyverno https://kyverno.github.io/kyverno/ >/dev/null
helm repo update >/dev/null
helm upgrade --install kyverno kyverno/kyverno \
  --namespace kyverno --create-namespace \
  --wait --timeout 5m

echo "== 3/6: esperando a que los pods de Kyverno esten Ready =="
kubectl wait --for=condition=Ready pods --all -n kyverno --timeout=180s

echo "== 4/6: aplicando la ClusterPolicy require-resource-limits =="
kubectl apply -f "${SCRIPT_DIR}/require-resource-limits.yaml"
echo "Esperando a que la policy quede lista..."
for i in $(seq 1 30); do
  # Kyverno 1.11-1.13 exponia status.ready (bool). Versiones actuales (1.14+)
  # lo reemplazaron por status.conditions[type=Ready].status. Se chequean
  # ambos para soportar cualquiera de las dos versiones del CRD.
  ready="$(kubectl get clusterpolicy require-resource-limits -o jsonpath='{.status.ready}' 2>/dev/null || true)"
  ready_cond="$(kubectl get clusterpolicy require-resource-limits -o jsonpath='{.status.conditions[?(@.type=="Ready")].status}' 2>/dev/null || true)"
  if [ "$ready" = "true" ] || [ "$ready_cond" = "True" ]; then
    break
  fi
  sleep 2
done

echo "== 5/6: creando namespace de prueba '${NAMESPACE}' =="
kubectl create namespace "${NAMESPACE}" --dry-run=client -o yaml | kubectl apply -f -

echo "== 6/6: probando los dos Pods =="
echo
echo "--- Pod CONFORME (tiene resources.limits): se espera que se cree ---"
if kubectl apply -f "${SCRIPT_DIR}/pod-conforme.yaml"; then
  echo "OK: el pod conforme fue aceptado, como se esperaba."
else
  echo "FALLO INESPERADO: el pod conforme deberia haber sido aceptado." >&2
  exit 1
fi

echo
echo "--- Pod NO CONFORME (sin resources.limits): se espera que Kyverno lo rechace ---"
if kubectl apply -f "${SCRIPT_DIR}/pod-no-conforme.yaml" 2>/tmp/kyverno-demo-error.txt; then
  echo "FALLO INESPERADO: el pod no conforme deberia haber sido rechazado." >&2
  exit 1
else
  echo "OK: el admission webhook de Kyverno rechazo el Pod, como se esperaba:"
  grep -i "resource" /tmp/kyverno-demo-error.txt || cat /tmp/kyverno-demo-error.txt
fi

echo
echo "== Demo completada. Para limpiar: kind delete cluster --name ${CLUSTER_NAME} =="
