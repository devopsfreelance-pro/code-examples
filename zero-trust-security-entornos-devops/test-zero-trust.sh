#!/usr/bin/env bash
# Prueba las tres reglas de microsegmentacion del ejemplo:
#   1. frontend -> backend   : DEBE funcionar (permitido explicitamente)
#   2. backend  -> database  : DEBE funcionar (permitido explicitamente)
#   3. frontend -> database  : DEBE fallar (sin regla de allow = deny)
#
# Sale con codigo != 0 si alguna verificacion no da el resultado esperado.
set -euo pipefail

NS="zero-trust-demo"
TIMEOUT=5
FAIL=0

check() {
  local desc="$1"
  local from_pod="$2"
  local target_url="$3"
  local expect="$4" # "allow" o "deny"

  echo "==> ${desc}"
  if kubectl -n "${NS}" exec "${from_pod}" -- \
      curl -s -o /dev/null -m "${TIMEOUT}" -w "%{http_code}" "${target_url}" \
      > /tmp/zt_result 2>/dev/null; then
    result="allow"
  else
    result="deny"
  fi

  if [[ "${result}" == "${expect}" ]]; then
    echo "    OK: resultado=${result} (esperado=${expect})"
  else
    echo "    FALLO: resultado=${result} (esperado=${expect})"
    FAIL=1
  fi
}

FRONTEND_POD=$(kubectl -n "${NS}" get pod -l app=frontend -o jsonpath='{.items[0].metadata.name}')
BACKEND_POD=$(kubectl -n "${NS}" get pod -l app=backend -o jsonpath='{.items[0].metadata.name}')

check "frontend -> backend (permitido)" "${FRONTEND_POD}" "http://backend.${NS}.svc.cluster.local" "allow"
check "backend -> database (permitido)" "${BACKEND_POD}" "http://database.${NS}.svc.cluster.local" "allow"
check "frontend -> database (debe estar bloqueado)" "${FRONTEND_POD}" "http://database.${NS}.svc.cluster.local" "deny"

echo ""
if [[ "${FAIL}" -eq 0 ]]; then
  echo "Todas las verificaciones de Zero Trust pasaron."
else
  echo "Alguna verificacion no coincidio con lo esperado. Ver detalle arriba."
fi
exit "${FAIL}"
