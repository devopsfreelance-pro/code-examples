#!/usr/bin/env bash
# Levanta un cluster kind, instala Crossplane, el provider-kubernetes
# y aplica el ejemplo de XRD + Composition + Claim descrito en el post.
#
# Requisitos: docker, kind, kubectl, helm.
set -euo pipefail

CLUSTER_NAME="crossplane-demo"
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

echo "==> 1/6 Creando cluster kind '${CLUSTER_NAME}' (si no existe)"
if ! kind get clusters | grep -qx "${CLUSTER_NAME}"; then
  kind create cluster --name "${CLUSTER_NAME}"
else
  echo "    cluster ya existe, se reutiliza"
fi
kubectl config use-context "kind-${CLUSTER_NAME}"

echo "==> 2/6 Instalando Crossplane via Helm"
# Se pinea la version 1.20.11 (ultima release de la linea v1.x): la
# Composition de este ejemplo (01-composition.yaml) usa el modo clasico
# "Resources" (Patch & Transform). Crossplane v2.x elimino el campo
# spec.resources y solo acepta modo "Pipeline" (Composition Functions).
helm repo add crossplane-stable https://charts.crossplane.io/stable --force-update
helm repo update
helm upgrade --install crossplane crossplane-stable/crossplane \
  --namespace crossplane-system \
  --create-namespace \
  --version 1.20.11 \
  --wait \
  --timeout 5m

echo "==> 3/6 Esperando a que el pod de Crossplane este Ready"
kubectl wait --for=condition=Available deployment/crossplane \
  -n crossplane-system --timeout=180s

echo "==> 4/6 Instalando provider-kubernetes y su ProviderConfig"
# El ProviderConfig usa un CRD (kubernetes.crossplane.io/v1alpha1) que instala
# el propio provider al arrancar, por lo que este primer apply puede fallar
# con "no matches for kind ProviderConfig" si el CRD todavia no esta
# registrado (carrera). Se tolera el fallo y se reintenta despues de esperar
# a que el provider quede Healthy.
kubectl apply -f "${SCRIPT_DIR}/02-provider-kubernetes.yaml" || true

echo "    esperando a que el provider quede healthy (puede tardar 1-2 min)..."
kubectl wait --for=condition=Healthy provider.pkg.crossplane.io/provider-kubernetes \
  --timeout=180s

kubectl apply -f "${SCRIPT_DIR}/02-provider-kubernetes.yaml"

echo "==> 5/6 Aplicando XRD y Composition (la API de infraestructura custom)"
kubectl apply -f "${SCRIPT_DIR}/00-xrd.yaml"
kubectl apply -f "${SCRIPT_DIR}/01-composition.yaml"

echo "    esperando a que el XRD quede establecido..."
kubectl wait --for=condition=Established \
  compositeresourcedefinition/xappdatabases.example.org --timeout=60s

echo "==> 6/6 Aplicando el Claim (lo que pediria un desarrollador)"
kubectl apply -f "${SCRIPT_DIR}/03-claim.yaml"

echo ""
echo "==> Esperando a que el claim quede Ready (hasta 60s)..."
kubectl wait --for=condition=Ready appdatabase/demo-app-db -n default --timeout=60s || true

echo ""
echo "=== Resultado ==="
echo "--- Claim ---"
kubectl get appdatabase demo-app-db -n default -o wide
echo ""
echo "--- Composite resource (XR) generado ---"
kubectl get xappdatabases.example.org
echo ""
echo "--- Recursos gestionados (Objects del provider-kubernetes) ---"
kubectl get objects.kubernetes.crossplane.io
echo ""
echo "--- ConfigMap simulando el endpoint de la 'base de datos' ---"
kubectl get configmap demo-app-db-endpoint -n default -o yaml
echo ""
echo "Listo. Para borrar todo: ./cleanup.sh"
