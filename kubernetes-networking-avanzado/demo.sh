#!/usr/bin/env bash
# Demo de NetworkPolicies en Kubernetes con enforcement real (Calico).
# Levanta un cluster kind de 3 zonas (frontend/backend/database) y prueba
# que frontend->backend funciona, backend->database funciona, pero
# frontend->database queda bloqueado por la policy de deny-all + whitelist.
set -euo pipefail

CLUSTER_NAME="netpol-demo"
CALICO_VERSION="v3.27.3"
CALICO_MANIFEST="https://raw.githubusercontent.com/projectcalico/calico/${CALICO_VERSION}/manifests/calico.yaml"
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

command -v kind >/dev/null 2>&1 || { echo "Falta kind. Instalar: https://kind.sigs.k8s.io/docs/user/quick-start/#installation"; exit 1; }
command -v kubectl >/dev/null 2>&1 || { echo "Falta kubectl. Instalar: https://kubernetes.io/docs/tasks/tools/"; exit 1; }

if kind get clusters 2>/dev/null | grep -qx "${CLUSTER_NAME}"; then
  echo "== Cluster kind '${CLUSTER_NAME}' ya existe, lo reutilizo =="
else
  echo "== Creando cluster kind '${CLUSTER_NAME}' (sin CNI por defecto) =="
  kind create cluster --name "${CLUSTER_NAME}" --config "${SCRIPT_DIR}/kind-config.yaml"
fi

kubectl config use-context "kind-${CLUSTER_NAME}" >/dev/null

echo
echo "== Instalando Calico ${CALICO_VERSION} (CNI con enforcement de NetworkPolicy) =="
kubectl apply -f "${CALICO_MANIFEST}"

echo
echo "== Esperando a que los pods de Calico esten Ready (puede tardar 1-2 min) =="
kubectl wait --for=condition=Ready pods -l k8s-app=calico-node -n kube-system --timeout=180s
kubectl wait --for=condition=Ready pods -l k8s-app=calico-kube-controllers -n kube-system --timeout=180s

echo
echo "== Aplicando namespaces frontend/backend/database =="
kubectl apply -f "${SCRIPT_DIR}/01-namespaces.yaml"

echo
echo "== Desplegando un pod servidor por capa (frontend, backend, database) =="
kubectl apply -f "${SCRIPT_DIR}/02-workloads.yaml"

echo
echo "== Esperando a que los 3 deployments esten disponibles =="
kubectl wait --for=condition=Available deployment/frontend -n frontend --timeout=120s
kubectl wait --for=condition=Available deployment/backend -n backend --timeout=120s
kubectl wait --for=condition=Available deployment/database -n database --timeout=120s

echo
echo "== PASO 1: probando conectividad ANTES de aplicar NetworkPolicies (deberia funcionar todo) =="
FRONTEND_POD="$(kubectl get pod -n frontend -l app=frontend -o jsonpath='{.items[0].metadata.name}')"
BACKEND_POD="$(kubectl get pod -n backend -l app=backend -o jsonpath='{.items[0].metadata.name}')"

echo "-- frontend -> database (sin policies, deberia responder) --"
kubectl exec -n frontend "${FRONTEND_POD}" -- wget -qO- --timeout=3 http://database.database.svc.cluster.local >/dev/null \
  && echo "OK: frontend llega a database (esperado, todavia no hay policies)" \
  || echo "ADVERTENCIA: fallo inesperado antes de aplicar policies"

echo
echo "== PASO 2: aplicando NetworkPolicies (deny-all + whitelist por zona) =="
kubectl apply -f "${SCRIPT_DIR}/03-network-policies.yaml"

echo
echo "Esperando unos segundos a que Calico programe las policies..."
sleep 10

echo
echo "== PASO 3: re-probando conectividad DESPUES de aplicar NetworkPolicies =="

echo "-- frontend -> backend (debe seguir permitido) --"
if kubectl exec -n frontend "${FRONTEND_POD}" -- wget -qO- --timeout=3 http://backend.backend.svc.cluster.local >/dev/null; then
  echo "OK: frontend -> backend permitido, como se espera."
else
  echo "FALLO: frontend -> backend deberia estar permitido y fue bloqueado."
fi

echo
echo "-- backend -> database (debe seguir permitido) --"
if kubectl exec -n backend "${BACKEND_POD}" -- wget -qO- --timeout=3 http://database.database.svc.cluster.local >/dev/null; then
  echo "OK: backend -> database permitido, como se espera."
else
  echo "FALLO: backend -> database deberia estar permitido y fue bloqueado."
fi

echo
echo "-- frontend -> database (debe quedar BLOQUEADO por la policy) --"
if kubectl exec -n frontend "${FRONTEND_POD}" -- wget -qO- --timeout=3 http://database.database.svc.cluster.local >/dev/null 2>&1; then
  echo "FALLO: frontend -> database deberia estar bloqueado y paso."
else
  echo "OK: frontend -> database bloqueado, tal como define la NetworkPolicy 'default-deny-ingress' + whitelist en database."
fi

echo
echo "Demo completa. Para limpiar todo:"
echo "  kind delete cluster --name ${CLUSTER_NAME}"
