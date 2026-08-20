#!/usr/bin/env bash
# demo.sh
#
# Orquesta la demo completa de GitOps para MLOps:
#   1. Crea un cluster kind local.
#   2. Inicializa un repo Git local que actúa como "source of truth".
#   3. Arranca gitops-controller.sh, que reconcilia el cluster contra ese repo.
#   4. Simula un despliegue nuevo de modelo (v1.0.0 -> v2.0.0) con un commit.
#   5. Muestra cómo el controlador lo detecta y lo aplica solo.
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
CLUSTER_NAME="mlops-gitops-demo"
NAMESPACE="mlops-demo"
WORK_DIR="$(mktemp -d)"
REPO_DIR="${WORK_DIR}/gitops-repo"

command -v kind >/dev/null 2>&1 || { echo "Falta 'kind'. Instalar: https://kind.sigs.k8s.io/docs/user/quick-start/"; exit 1; }
command -v kubectl >/dev/null 2>&1 || { echo "Falta 'kubectl'."; exit 1; }
command -v git >/dev/null 2>&1 || { echo "Falta 'git'."; exit 1; }

echo "==> Creando cluster kind '${CLUSTER_NAME}' (si no existe)"
if ! kind get clusters | grep -qx "${CLUSTER_NAME}"; then
  kind create cluster --name "${CLUSTER_NAME}"
else
  echo "Cluster ya existe, reutilizando."
fi
kubectl cluster-info --context "kind-${CLUSTER_NAME}" >/dev/null

echo "==> Inicializando repo Git local (simula el repo GitOps 'source of truth')"
mkdir -p "${REPO_DIR}/manifests"
cp "${SCRIPT_DIR}/../manifests/model-server.yaml" "${REPO_DIR}/manifests/"
git -C "${REPO_DIR}" init -q
git -C "${REPO_DIR}" config user.email "demo@example.com"
git -C "${REPO_DIR}" config user.name "GitOps Demo"
git -C "${REPO_DIR}" add manifests/
git -C "${REPO_DIR}" commit -q -m "Estado inicial: modelo v1.0.0"
echo "Repo GitOps en: ${REPO_DIR}"

echo "==> Arrancando el controlador de reconciliación en background"
NAMESPACE="${NAMESPACE}" "${SCRIPT_DIR}/gitops-controller.sh" "${REPO_DIR}" &
CONTROLLER_PID=$!
trap 'echo "==> Deteniendo controlador (PID ${CONTROLLER_PID})"; kill "${CONTROLLER_PID}" 2>/dev/null || true' EXIT

echo "==> Esperando primera reconciliación (10s)..."
sleep 10
kubectl -n "${NAMESPACE}" get deployment,pods,svc

echo ""
echo "==> Simulando un nuevo despliegue de modelo: commit v1.0.0 -> v2.0.0"
sed -i 's/v1\.0\.0/v2.0.0/' "${REPO_DIR}/manifests/model-server.yaml"
git -C "${REPO_DIR}" add manifests/
git -C "${REPO_DIR}" commit -q -m "Deploy modelo v2.0.0"

echo "==> Esperando a que el controlador detecte el commit y reconcilie (10s)..."
sleep 10
kubectl -n "${NAMESPACE}" get deployment,pods,svc

echo ""
echo "==> Verificando la versión de modelo que sirve el pod:"
kubectl -n "${NAMESPACE}" run curl-check --image=curlimages/curl:8.10.1 --rm -i --restart=Never -- \
  curl -s "http://ml-model-server.${NAMESPACE}.svc.cluster.local"

echo ""
echo "==> Demo terminada."
echo "Repo GitOps (source of truth) queda en: ${REPO_DIR}"
echo "Para destruir el cluster: kind delete cluster --name ${CLUSTER_NAME}"
