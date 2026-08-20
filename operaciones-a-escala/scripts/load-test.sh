#!/usr/bin/env bash
## Genera carga sostenida contra echo-service desde dentro del cluster
## para disparar el HorizontalPodAutoscaler.
set -euo pipefail

NAMESPACE="${1:-default}"
DURATION_SECONDS="${2:-180}"

echo "Lanzando pod de carga contra echo-service durante ${DURATION_SECONDS}s (namespace: ${NAMESPACE})"

kubectl run load-generator \
  --namespace "${NAMESPACE}" \
  --image=busybox:1.36 \
  --restart=Never \
  --rm \
  -i \
  --command -- /bin/sh -c "
    end=\$(( \$(date +%s) + ${DURATION_SECONDS} ));
    while [ \$(date +%s) -lt \$end ]; do
      for i in \$(seq 1 20); do
        wget -q -O- http://echo-service.${NAMESPACE}.svc.cluster.local >/dev/null &
      done
      wait
    done
    echo 'Carga finalizada'
  "
