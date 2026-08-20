#!/usr/bin/env bash
# debug.sh - Recorre las técnicas de kubernetes debugging del post
# aplicadas sobre un mini clúster kind con dos deployments rotos a propósito:
#   - crashy-app: entra en CrashLoopBackOff (falla al arrancar)
#   - notready-app: queda NotReady (readiness probe apunta a un puerto que no existe)
#     y su Service se queda sin endpoints (selector mal configurado)
#
# Requisitos: docker, kind, kubectl
set -euo pipefail

CLUSTER_NAME="debug-demo"
NAMESPACE="debug-demo"
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

section() {
  echo
  echo "=== $1 ==="
}

section "1. Creando clúster kind (si no existe)"
if ! kind get clusters | grep -qx "${CLUSTER_NAME}"; then
  kind create cluster --config "${SCRIPT_DIR}/kind-cluster.yaml"
else
  echo "Clúster ${CLUSTER_NAME} ya existe, se reutiliza."
fi

kubectl cluster-info --context "kind-${CLUSTER_NAME}"

section "2. Aplicando manifiestos rotos a propósito"
kubectl apply -f "${SCRIPT_DIR}/manifests/broken-app.yaml"

section "3. Esperando que Kubernetes intente arrancar los pods (15s)"
sleep 15

section "4. kubectl get pods -o wide"
kubectl get pods -n "${NAMESPACE}" -o wide

section "5. Diagnóstico de crashy-app: describe + logs --previous"
POD_CRASHY=$(kubectl get pods -n "${NAMESPACE}" -l app=crashy-app -o jsonpath='{.items[0].metadata.name}')
echo "--- kubectl describe pod ${POD_CRASHY} (eventos al final) ---"
kubectl describe pod "${POD_CRASHY}" -n "${NAMESPACE}" | tail -n 20
echo
echo "--- kubectl logs ${POD_CRASHY} --previous (log del intento fallido anterior) ---"
kubectl logs "${POD_CRASHY}" -n "${NAMESPACE}" --previous || \
  kubectl logs "${POD_CRASHY}" -n "${NAMESPACE}"

section "6. Diagnóstico de notready-app: probe fallando"
POD_NOTREADY=$(kubectl get pods -n "${NAMESPACE}" -l app=notready-app -o jsonpath='{.items[0].metadata.name}')
echo "--- kubectl describe pod ${POD_NOTREADY} (eventos de readiness) ---"
kubectl describe pod "${POD_NOTREADY}" -n "${NAMESPACE}" | tail -n 20

section "7. Service sin endpoints (selector mal configurado)"
echo "--- kubectl get endpoints notready-app-svc ---"
kubectl get endpoints notready-app-svc -n "${NAMESPACE}"
echo "(vacío = ningún pod coincide con el selector del Service, ver manifests/broken-app.yaml)"

section "8. Ephemeral container para inspeccionar crashy-app in situ"
echo "kubectl debug ${POD_CRASHY} -n ${NAMESPACE} -it --image=busybox --target=crashy-app"
echo "(se omite ejecución interactiva en este script; correr manualmente para explorar)"

section "Listo. Para limpiar todo: kind delete cluster --name ${CLUSTER_NAME}"
