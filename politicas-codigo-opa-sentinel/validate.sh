#!/usr/bin/env bash
# Valida un plan de Terraform (en formato JSON) contra las politicas Rego
# de policies/, igual que el paso de CI/CD descrito en el post.
set -euo pipefail

cd "$(dirname "$0")"

INPUT_FILE="tfplan-sample.json"
POLICY_DIR="policies"
OUT_FILE="violations.json"

echo "Evaluando ${INPUT_FILE} contra las politicas en ${POLICY_DIR}/ ..."

docker run --rm \
    -v "$(pwd)/${POLICY_DIR}:/policies" \
    -v "$(pwd)/${INPUT_FILE}:/input.json" \
    openpolicyagent/opa:0.68.0 \
    eval --data /policies --input /input.json \
    --format pretty \
    "data.terraform.deny" > "${OUT_FILE}"

echo "--- Resultado (${OUT_FILE}) ---"
cat "${OUT_FILE}"

# opa eval con --format pretty siempre devuelve exit 0; el chequeo real de
# violaciones se hace inspeccionando el contenido, tal como en el post.
if grep -q '^\[\]$' "${OUT_FILE}"; then
    echo "Sin violaciones de politica."
    exit 0
else
    echo "Violaciones de politica detectadas. Ver ${OUT_FILE}."
    exit 1
fi
