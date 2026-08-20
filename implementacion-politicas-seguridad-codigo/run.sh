#!/usr/bin/env bash
# Evalua planes de Terraform (simulados) contra las politicas Rego del post
# usando Conftest, tal como lo haria el job de GitHub Actions del post
# ("Integracion en el pipeline: ejemplo completo").
#
# Uso:
#   ./run.sh no-conforme   -> evalua examples/plan-no-conforme.json
#   ./run.sh conforme      -> evalua examples/plan-conforme.json
#   ./run.sh               -> corre ambos casos, en orden

set -euo pipefail

DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
CONFTEST_IMAGE="openpolicyagent/conftest:v0.56.0"

run_case() {
	local plan_file="$1"
	local label="$2"

	echo "=== Caso: ${label} (${plan_file}) ==="
	echo "--- deny (modo enforce) ---"
	set +e
	docker run --rm \
		-v "${DIR}:/project" \
		-w /project \
		"${CONFTEST_IMAGE}" \
		test "examples/${plan_file}" --policy policy/terraform --all-namespaces --output table
	local deny_status=$?
	set -e
	echo "exit code deny: ${deny_status}"

	echo "--- warn (modo audit, no bloquea) ---"
	set +e
	docker run --rm \
		-v "${DIR}:/project" \
		-w /project \
		"${CONFTEST_IMAGE}" \
		test "examples/${plan_file}" --policy policy/terraform --all-namespaces --no-fail --output table
	set -e
	echo
}

case "${1:-all}" in
	no-conforme)
		run_case "plan-no-conforme.json" "bucket publico y sin cifrar"
		;;
	conforme)
		run_case "plan-conforme.json" "bucket privado y cifrado"
		;;
	all)
		run_case "plan-no-conforme.json" "bucket publico y sin cifrar"
		run_case "plan-conforme.json" "bucket privado y cifrado"
		;;
	*)
		echo "Uso: $0 [no-conforme|conforme]" >&2
		exit 2
		;;
esac
