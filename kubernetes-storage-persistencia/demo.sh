#!/usr/bin/env bash
# Demo: StorageClass -> PVC -> PV (aprovisionamiento dinamico) y como el
# almacenamiento persiste de forma INDEPENDIENTE del ciclo de vida del pod.
#
# 1. Crea un cluster kind (si no existe).
# 2. Aplica una StorageClass propia (fast-storage) sobre el mismo
#    provisioner que trae kind (rancher.io/local-path, equivalente a un
#    CSI driver dinamico).
# 3. Crea un PVC contra esa StorageClass y un Pod que lo monta.
# 4. Muestra el PV creado dinamicamente y el binding PVC <-> PV.
# 5. Escribe un dato en el volumen.
# 6. Borra el POD (no el PVC) y lo recrea: el dato sigue ahi porque el PV
#    vive independientemente del pod.
# 7. Borra el PVC y muestra como el PV pasa a estado Released y luego
#    desaparece por el reclaimPolicy: Delete.
set -euo pipefail

CLUSTER_NAME="storage-demo"
DIR="$(dirname "$0")"

echo "==> 1. Creando cluster kind '${CLUSTER_NAME}' (si no existe)..."
if ! kind get clusters | grep -q "^${CLUSTER_NAME}$"; then
  kind create cluster --name "${CLUSTER_NAME}"
else
  echo "    Cluster ya existe, reutilizando."
fi

kubectl config use-context "kind-${CLUSTER_NAME}"

echo
echo "==> 2. Aplicando StorageClass 'fast-storage'..."
kubectl apply -f "${DIR}/storageclass.yaml"
kubectl get storageclass

echo
echo "==> 3. Creando PVC y Pod que lo consume..."
kubectl apply -f "${DIR}/pvc.yaml"
kubectl apply -f "${DIR}/pod.yaml"

echo "    Esperando a que el pod este Ready (el binding del PVC es"
echo "    WaitForFirstConsumer, o sea que el PV recien se crea aca)..."
kubectl wait --for=condition=Ready pod/app-datos --timeout=90s

echo
echo "==> 4. PVC vinculado a un PV creado dinamicamente:"
kubectl get pvc datos-app-pvc
echo
PV_NAME=$(kubectl get pvc datos-app-pvc -o jsonpath='{.spec.volumeName}')
echo "    PV asociado: ${PV_NAME}"
kubectl get pv "${PV_NAME}"

echo
echo "==> 5. Escribiendo un dato en el volumen..."
MARCA="dato-critico-$(date +%s)"
kubectl exec app-datos -- sh -c "echo '${MARCA}' > /datos/marca.txt"
kubectl exec app-datos -- cat /datos/marca.txt

echo
echo "==> 6. Borrando el POD (el PVC y el PV quedan intactos)..."
kubectl delete pod app-datos
kubectl apply -f "${DIR}/pod.yaml"
kubectl wait --for=condition=Ready pod/app-datos --timeout=90s

echo
echo "==> Verificando que el dato sigue ahi tras recrear el pod..."
RESULTADO=$(kubectl exec app-datos -- cat /datos/marca.txt)
echo "    Contenido leido: ${RESULTADO}"

if [ "${RESULTADO}" != "${MARCA}" ]; then
  echo
  echo "FALLO: el dato no coincide, algo salio mal." >&2
  exit 1
fi
echo
echo "OK: el dato sobrevivio al borrado del pod. El PV vive independiente del pod que lo consume."

echo
echo "==> 7. Borrando el PVC para ver el ciclo de vida del PV (reclaimPolicy: Delete)..."
kubectl delete pod app-datos
kubectl delete pvc datos-app-pvc
echo "    Estado del PV justo despues de borrar el PVC (deberia verse 'Terminating' o ya no existir):"
kubectl get pv "${PV_NAME}" 2>/dev/null || echo "    El PV '${PV_NAME}' ya fue eliminado por el garbage collector (reclaimPolicy: Delete)."

echo
echo "==> Para limpiar todo:"
echo "    kind delete cluster --name ${CLUSTER_NAME}"
