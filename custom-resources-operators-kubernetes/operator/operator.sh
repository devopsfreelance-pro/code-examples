#!/usr/bin/env bash
# Mini custom operator para el CRD WebApp (webapp.example.com/v1), escrito
# en bash + kubectl + jq para no depender de Go ni del Operator SDK.
#
# Implementa el ciclo de reconciliación descrito en el post:
#   observar -> analizar (diff spec vs estado real) -> ejecutar -> status
#
# Cada RESYNC_SECONDS segundos:
#   1. Lista todos los recursos WebApp del namespace.
#   2. Por cada uno, crea/actualiza (kubectl apply) un Deployment y un
#      Service que reflejan spec.image / spec.replicas / spec.port.
#   3. Escribe status.phase y status.observedGeneration en el Custom
#      Resource usando el subrecurso status (kubectl patch --subresource).
#   4. Si el WebApp fue borrado, elimina el Deployment/Service asociados
#      (etiquetados con managed-by=webapp-operator).
#
# La reconciliación es idempotente: se puede ejecutar cualquier cantidad
# de veces con el mismo spec sin generar cambios adicionales.
#
# Requisitos: kubectl, jq
set -euo pipefail

NAMESPACE="${NAMESPACE:-default}"
GROUP="webapp.example.com"
VERSION="v1"
PLURAL="webapps"
RESYNC_SECONDS="${RESYNC_SECONDS:-5}"
LABEL_KEY="managed-by"
LABEL_VALUE="webapp-operator"
LABEL_SELECTOR="${LABEL_KEY}=${LABEL_VALUE}"

log() {
  printf '%s [operator] %s\n' "$(date '+%Y-%m-%d %H:%M:%S')" "$1"
}

reconcile_webapp() {
  local name="$1" image="$2" replicas="$3" port="$4" generation="$5"

  log "Reconciliando WebApp '${name}' (image=${image}, replicas=${replicas})"

  cat <<EOF | kubectl apply -n "${NAMESPACE}" -f - >/dev/null
apiVersion: apps/v1
kind: Deployment
metadata:
  name: ${name}
  labels:
    app: ${name}
    ${LABEL_KEY}: ${LABEL_VALUE}
spec:
  replicas: ${replicas}
  selector:
    matchLabels:
      app: ${name}
  template:
    metadata:
      labels:
        app: ${name}
        ${LABEL_KEY}: ${LABEL_VALUE}
    spec:
      containers:
        - name: webapp
          image: ${image}
          ports:
            - containerPort: ${port}
---
apiVersion: v1
kind: Service
metadata:
  name: ${name}
  labels:
    app: ${name}
    ${LABEL_KEY}: ${LABEL_VALUE}
spec:
  selector:
    app: ${name}
  ports:
    - port: ${port}
      targetPort: ${port}
EOF

  kubectl patch "${PLURAL}.${GROUP}" "${name}" -n "${NAMESPACE}" \
    --subresource=status --type=merge -p "$(jq -n \
      --arg phase "Ready" \
      --argjson gen "${generation}" \
      --arg ts "$(date -u '+%Y-%m-%dT%H:%M:%SZ')" \
      '{status:{phase:$phase, observedGeneration:$gen, lastReconcileTime:$ts}}')" \
    >/dev/null

  log "WebApp '${name}' reconciliada -> status.phase=Ready"
}

delete_orphans() {
  local live_names="$1"

  for kind in deployment service; do
    for res_name in $(kubectl get "${kind}" -n "${NAMESPACE}" -l "${LABEL_SELECTOR}" \
        -o jsonpath='{.items[*].metadata.name}' 2>/dev/null || true); do
      if ! grep -qx "${res_name}" <<<"${live_names}"; then
        log "WebApp '${res_name}' ya no existe, eliminando ${kind} huérfano"
        kubectl delete "${kind}" "${res_name}" -n "${NAMESPACE}" --ignore-not-found >/dev/null
      fi
    done
  done
}

log "Operator iniciado. Observando WebApp en namespace '${NAMESPACE}' cada ${RESYNC_SECONDS}s..."

while true; do
  webapps_json="$(kubectl get "${PLURAL}.${GROUP}" -n "${NAMESPACE}" -o json 2>/dev/null || echo '{"items":[]}')"

  live_names=""
  while IFS=$'\t' read -r name image replicas port generation; do
    [ -z "${name}" ] && continue
    live_names+="${name}"$'\n'
    reconcile_webapp "${name}" "${image}" "${replicas:-2}" "${port:-8080}" "${generation}"
  done < <(jq -r '.items[] | [.metadata.name, .spec.image, (.spec.replicas // 2), (.spec.port // 8080), .metadata.generation] | @tsv' <<<"${webapps_json}")

  delete_orphans "${live_names}"

  sleep "${RESYNC_SECONDS}"
done
