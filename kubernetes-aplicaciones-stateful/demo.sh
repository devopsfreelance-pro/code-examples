#!/usr/bin/env bash
# Demo: identidad estable + persistencia de datos en un StatefulSet.
#
# 1. Crea un cluster kind (si no existe).
# 2. Aplica el StatefulSet + Headless Service de statefulset.yaml.
# 3. Muestra los nombres de pod estables (web-0, web-1, web-2) y sus PVC.
# 4. Escribe un dato único en el pod web-0.
# 5. Borra el pod web-0 y espera que Kubernetes lo recree.
# 6. Verifica que el dato escrito antes SIGUE ahí: el PVC sobrevivió
#    al borrado del pod porque volumeClaimTemplates es persistente.
set -euo pipefail

CLUSTER_NAME="stateful-demo"

echo "==> 1. Creando cluster kind '${CLUSTER_NAME}' (si no existe)..."
if ! kind get clusters | grep -q "^${CLUSTER_NAME}$"; then
  kind create cluster --name "${CLUSTER_NAME}"
else
  echo "    Cluster ya existe, reutilizando."
fi

kubectl config use-context "kind-${CLUSTER_NAME}"

echo "==> 2. Aplicando StatefulSet + Headless Service..."
kubectl apply -f "$(dirname "$0")/statefulset.yaml"

echo "==> 3. Esperando a que los 3 pods estén Ready..."
kubectl rollout status statefulset/web --timeout=120s

echo
echo "==> Pods con nombre estable (no hash aleatorio como en un Deployment):"
kubectl get pods -l app=web -o wide

echo
echo "==> PVCs creados a partir de volumeClaimTemplates (uno por pod):"
kubectl get pvc -l app=web

echo
echo "==> 4. Escribiendo un dato único en web-0..."
MARCA="dato-critico-$(date +%s)"
kubectl exec web-0 -- sh -c "echo '${MARCA}' > /usr/share/nginx/html/marca.txt"
kubectl exec web-0 -- cat /usr/share/nginx/html/marca.txt

echo
echo "==> 5. Borrando el pod web-0 (Kubernetes lo va a recrear con el mismo nombre y el mismo PVC)..."
kubectl delete pod web-0
kubectl wait --for=condition=Ready pod/web-0 --timeout=90s

echo
echo "==> 6. Verificando que el dato sigue ahí después de recrear el pod..."
RESULTADO=$(kubectl exec web-0 -- cat /usr/share/nginx/html/marca.txt)
echo "    Contenido leído: ${RESULTADO}"

if [ "${RESULTADO}" = "${MARCA}" ]; then
  echo
  echo "OK: el dato sobrevivió al borrado del pod. El PVC quedó ligado a web-0 (identidad estable + storage persistente)."
else
  echo
  echo "FALLO: el dato no coincide, algo salió mal." >&2
  exit 1
fi

echo
echo "==> Para limpiar todo:"
echo "    kind delete cluster --name ${CLUSTER_NAME}"
