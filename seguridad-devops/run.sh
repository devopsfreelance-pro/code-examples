#!/usr/bin/env bash
# Corre un security gate de "Seguridad como Codigo" (policy-as-code) contra manifiestos
# de Kubernetes usando OPA/Conftest, tal como se describe en la seccion
# "Seguridad como Codigo" del post. No requiere instalar nada: usa la imagen
# oficial de conftest via Docker.
set -euo pipefail

cd "$(dirname "$0")"

CONFTEST_IMAGE="openpolicyagent/conftest:v0.55.0"

echo "=== 1) Manifiesto INSEGURO (se espera que el gate lo BLOQUEE) ==="
set +e
docker run --rm \
  -v "$(pwd)/policy:/project/policy" \
  -v "$(pwd)/manifests:/project/manifests" \
  -w /project \
  "$CONFTEST_IMAGE" test --policy policy manifests/pod-insecure.yaml
INSECURE_EXIT=$?
set -e

echo
echo "=== 2) Manifiesto SEGURO (se espera que el gate lo APRUEBE) ==="
set +e
docker run --rm \
  -v "$(pwd)/policy:/project/policy" \
  -v "$(pwd)/manifests:/project/manifests" \
  -w /project \
  "$CONFTEST_IMAGE" test --policy policy manifests/pod-secure.yaml
SECURE_EXIT=$?
set -e

echo
if [[ "$INSECURE_EXIT" -ne 0 && "$SECURE_EXIT" -eq 0 ]]; then
  echo "OK: el security gate bloqueo el manifiesto inseguro y aprobo el seguro."
  exit 0
else
  echo "FALLO: el resultado del gate no fue el esperado (insecure_exit=$INSECURE_EXIT secure_exit=$SECURE_EXIT)."
  exit 1
fi
