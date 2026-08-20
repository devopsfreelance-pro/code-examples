#!/usr/bin/env bash
# Crea un cluster kind local, aplica el RBAC de least-privilege del ejemplo
# y verifica con "kubectl auth can-i" que cada ServiceAccount solo puede
# hacer lo que su rol permite (principio de menor privilegio del post).
set -euo pipefail

CLUSTER_NAME="rbac-demo"
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

command -v kind >/dev/null 2>&1 || { echo "Falta 'kind'. Instalar: https://kind.sigs.k8s.io/docs/user/quick-start/"; exit 1; }
command -v kubectl >/dev/null 2>&1 || { echo "Falta 'kubectl'."; exit 1; }

if ! kind get clusters 2>/dev/null | grep -qx "${CLUSTER_NAME}"; then
  echo "==> Creando cluster kind '${CLUSTER_NAME}'..."
  kind create cluster --name "${CLUSTER_NAME}"
else
  echo "==> Reusando cluster kind '${CLUSTER_NAME}' existente"
fi

kubectl config use-context "kind-${CLUSTER_NAME}" >/dev/null

echo "==> Aplicando namespace, ServiceAccounts y RBAC..."
kubectl apply -f "${SCRIPT_DIR}/00-namespace-and-sa.yaml"
kubectl apply -f "${SCRIPT_DIR}/01-rbac.yaml"

echo
echo "==> Verificando permisos de 'developer-sa' (esperado: allow/deny mixto)"
DEV_USER="system:serviceaccount:development:developer-sa"

check() {
  local user="$1" verb="$2" resource="$3" expected="$4"
  local result
  result=$(kubectl auth can-i "${verb}" "${resource}" \
    --as="${user}" -n development 2>/dev/null || true)
  local status="OK"
  if [ "${result}" != "${expected}" ]; then
    status="FALLO"
  fi
  printf "  [%s] can-i %-8s %-12s -> %-3s (esperado: %s)\n" \
    "${status}" "${verb}" "${resource}" "${result}" "${expected}"
}

check "${DEV_USER}" get    pods        yes
check "${DEV_USER}" create deployments yes
check "${DEV_USER}" delete pods        no
check "${DEV_USER}" get    secrets     no

echo
echo "==> Verificando permisos de 'security-sa'"
SEC_USER="system:serviceaccount:development:security-sa"

check "${SEC_USER}" get    secrets     yes
check "${SEC_USER}" list   events      yes
check "${SEC_USER}" create deployments no
check "${SEC_USER}" delete pods        no

echo
echo "==> Listo. Para borrar el cluster de prueba:"
echo "    kind delete cluster --name ${CLUSTER_NAME}"
