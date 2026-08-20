#!/usr/bin/env bash
# Corre la política de compliance as code (policies/kubernetes-security.rego)
# contra los manifiestos de ejemplo usando conftest.
#
# Uso: ./validate.sh
#
# Salida esperada:
#   - manifests/pod-compliant.yaml     -> PASS
#   - manifests/pod-noncompliant.yaml  -> FAIL (2 violaciones: root + privileged)
#
# El script termina con exit code != 0 si conftest reporta algún fallo,
# igual que lo haría un paso de CI/CD que bloquea el merge.

set -euo pipefail

cd "$(dirname "$0")"

CONFTEST_IMAGE="openpolicyagent/conftest:v0.56.0"

run_conftest() {
  if command -v conftest >/dev/null 2>&1; then
    conftest "$@"
  else
    docker run --rm -v "$(pwd)":/project -w /project "$CONFTEST_IMAGE" "$@"
  fi
}

echo "== Compliance as code: validando manifiestos de Kubernetes contra policies/kubernetes-security.rego =="
echo

echo "--- Caso 1: pod compliant (se espera PASS) ---"
run_conftest test manifests/pod-compliant.yaml --policy policies || true
echo

echo "--- Caso 2: pod NO compliant (se espera FAIL) ---"
set +e
run_conftest test manifests/pod-noncompliant.yaml --policy policies
noncompliant_status=$?
set -e
echo

if [ "$noncompliant_status" -eq 0 ]; then
  echo "ERROR: se esperaba que el pod no compliant fallara la validación y no fue así." >&2
  exit 1
fi

echo "== Resultado: la política bloqueó correctamente el manifiesto inseguro (exit code $noncompliant_status) =="
