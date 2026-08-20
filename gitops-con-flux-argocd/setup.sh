#!/bin/bash
# Levanta un cluster kind, instala ArgoCD y despliega la app "guestbook"
# via GitOps (Application con syncPolicy.automated), tal como se describe
# en el post "GitOps con Flux y ArgoCD".
set -euo pipefail

CLUSTER_NAME="gitops-argocd-demo"
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

echo "==> Creando cluster kind '${CLUSTER_NAME}'..."
if kind get clusters 2>/dev/null | grep -qx "${CLUSTER_NAME}"; then
  echo "El cluster ya existe, se reutiliza."
else
  kind create cluster --config "${SCRIPT_DIR}/kind-config.yaml"
fi

echo "==> Instalando ArgoCD en el namespace 'argocd'..."
kubectl create namespace argocd --dry-run=client -o yaml | kubectl apply -f -
kubectl apply -n argocd -f https://raw.githubusercontent.com/argoproj/argo-cd/stable/manifests/install.yaml

echo "==> Esperando a que los pods de ArgoCD esten listos (puede tardar unos minutos)..."
kubectl wait --for=condition=available --timeout=300s deployment/argocd-server -n argocd
kubectl wait --for=condition=available --timeout=300s deployment/argocd-repo-server -n argocd
kubectl wait --for=condition=available --timeout=300s deployment/argocd-applicationset-controller -n argocd || true

echo "==> Aplicando la Application 'guestbook' (esto dispara el sync GitOps)..."
kubectl apply -f "${SCRIPT_DIR}/argocd-application.yaml"

echo "==> Esperando a que ArgoCD sincronice y despliegue 'guestbook'..."
for i in $(seq 1 30); do
  SYNC_STATUS="$(kubectl get application guestbook -n argocd -o jsonpath='{.status.sync.status}' 2>/dev/null || true)"
  HEALTH_STATUS="$(kubectl get application guestbook -n argocd -o jsonpath='{.status.health.status}' 2>/dev/null || true)"
  echo "  intento ${i}: sync=${SYNC_STATUS:-desconocido} health=${HEALTH_STATUS:-desconocido}"
  if [ "${SYNC_STATUS}" = "Synced" ] && [ "${HEALTH_STATUS}" = "Healthy" ]; then
    break
  fi
  sleep 10
done

echo ""
echo "==> Estado final de la Application:"
kubectl get application guestbook -n argocd

echo ""
echo "==> Pods desplegados via GitOps en el namespace 'guestbook':"
kubectl get pods -n guestbook

echo ""
echo "==> Password inicial del admin de ArgoCD:"
kubectl -n argocd get secret argocd-initial-admin-secret -o jsonpath="{.data.password}" | base64 -d
echo ""
echo ""
echo "Listo. Para ver la app desplegada:"
echo "  kubectl port-forward svc/guestbook-ui -n guestbook 8081:80"
echo "  curl -s localhost:8081 | head -n 5"
echo ""
echo "Para ver la UI de ArgoCD:"
echo "  kubectl port-forward svc/argocd-server -n argocd 8080:443"
echo "  usuario: admin / password: el impreso arriba"
