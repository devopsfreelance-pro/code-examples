#!/usr/bin/env bash
# Simula el "boton de autoservicio" de la internal platform: toma
# platform-spec.yaml, lo traduce a valores de Helm y despliega la
# WebApplication resultante en un cluster kind local. El developer que
# usa la plataforma real solo ve el primer paso (el spec); todo lo demas
# lo hace la plataforma por detras.
set -euo pipefail

CLUSTER_NAME="idp-demo"
RELEASE_NAME="mi-aplicacion"
SPEC_FILE="${1:-platform-spec.yaml}"
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
VALUES_FILE="${SCRIPT_DIR}/chart/values.generated.yaml"

for bin in kind kubectl helm python3; do
  if ! command -v "$bin" >/dev/null 2>&1; then
    echo "error: falta '$bin' en el PATH. Ver README.md > Requisitos." >&2
    exit 1
  fi
done

if ! kind get clusters 2>/dev/null | grep -qx "$CLUSTER_NAME"; then
  echo "==> Creando cluster kind '$CLUSTER_NAME'"
  kind create cluster --name "$CLUSTER_NAME"
else
  echo "==> Reusando cluster kind '$CLUSTER_NAME' existente"
fi

echo "==> Traduciendo ${SPEC_FILE} a valores de Helm"
python3 "${SCRIPT_DIR}/translate.py" "$SPEC_FILE" >"$VALUES_FILE"
cat "$VALUES_FILE"

echo "==> Desplegando WebApplication via Helm"
helm upgrade --install "$RELEASE_NAME" "${SCRIPT_DIR}/chart" \
  -f "$VALUES_FILE" \
  --kube-context "kind-${CLUSTER_NAME}"

echo "==> Esperando a que el Deployment este listo"
kubectl --context "kind-${CLUSTER_NAME}" rollout status "deployment/${RELEASE_NAME}" --timeout=120s

echo "==> Port-forward a localhost:8080 (Ctrl+C para cortar)"
kubectl --context "kind-${CLUSTER_NAME}" port-forward "service/${RELEASE_NAME}" 8080:80 &
PF_PID=$!
trap 'kill $PF_PID 2>/dev/null || true' EXIT

sleep 3
echo "==> Probando la aplicacion desplegada"
curl -sSf http://localhost:8080/ | head -n 5

echo "==> OK. La app quedo corriendo en el cluster kind '$CLUSTER_NAME'."
echo "    Para limpiar: kind delete cluster --name $CLUSTER_NAME"
wait $PF_PID
